from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import re
import unicodedata

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware


APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parent
EXCEL_PATH = PROJECT_ROOT / "base_barcos_dummy.xlsx"


app = FastAPI(title="OnBordo - API de Veleiros", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_CACHE: Dict[str, Any] = {"df": None, "services_column": None, "alias_map": None}


def _normalize_name(name: Any) -> str:
    s = str(name).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"R\s*\$", "RS", s, flags=re.IGNORECASE)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_").lower()


def _normalize_services_cell(cell: Any) -> List[str]:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    if isinstance(cell, list):
        return [str(x).strip() for x in cell if str(x).strip()]
    # split on comma or semicolon
    parts = [p.strip() for p in str(cell).replace(";", ",").split(",")]
    return [p for p in parts if p]


def _load_dataframe(refresh: bool = False) -> Tuple[pd.DataFrame, Optional[str], Dict[str, str]]:
    global _CACHE
    if _CACHE["df"] is not None and not refresh:
        return _CACHE["df"].copy(), _CACHE["services_column"], dict(_CACHE["alias_map"])  # type: ignore

    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Arquivo Excel não encontrado em: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH)

    # Cria ID estável baseado no índice do arquivo
    df = df.reset_index(drop=True)
    df.insert(0, "id", df.index.astype(int))

    # Construir mapa de apelidos normalizados -> nome original
    alias_map: Dict[str, str] = {}
    for c in df.columns:
        alias = _normalize_name(c)
        alias_map.setdefault(alias, c)

    # Preferências explícitas de apelidos para a planilha informada
    preferred_aliases: Dict[str, str] = {
        "id_do_barco": "ID do Barco",
        "preco_por_dia_rs": "Preço por Dia (R$)",
        "nome_do_barco": "Nome do Barco",
        "marina_porto": "Marina/Porto",
        "pes": "Pés",
        "tripulante": "Tripulante",
        "preco_do_arrais_rs": "Preço do Arrais (R$)",
        "outros_servicos": "Outros Serviços",
    }

    # Injeta/ajusta mapeamentos conforme preferências, validando existência
    for alias, desired_original in preferred_aliases.items():
        if desired_original in df.columns:
            alias_map[alias] = desired_original
        else:
            # Caso o cabeçalho varie levemente, tenta casar por normalização
            matched = next((c for c in df.columns if _normalize_name(c) == alias), None)
            if matched is not None:
                alias_map[alias] = matched

    # Detecta coluna de serviços por nome provável (normalizado)
    service_alias_targets = {"servicos", "servico", "servicos_outros", "outros_servicos", "services"}
    services_col: Optional[str] = None
    for alias, original in alias_map.items():
        if alias in service_alias_targets:
            services_col = original
            break

    if services_col is not None:
        df["services_list"] = df[services_col].apply(_normalize_services_cell)
    else:
        df["services_list"] = [[] for _ in range(len(df))]

    _CACHE = {"df": df, "services_column": services_col, "alias_map": alias_map}
    return df.copy(), services_col, alias_map


def _to_records(df: pd.DataFrame, include_services_list: bool = False) -> List[Dict[str, Any]]:
    records = df.to_dict(orient="records")
    if not include_services_list:
        for rec in records:
            rec.pop("services_list", None)
    return records


def _try_parse_number(value: str) -> Any:
    try:
        if "." in value or "," in value:
            # normalize comma to dot for float
            return float(value.replace(",", "."))
        return int(value)
    except Exception:
        return value


def _parse_in_list(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _apply_generic_filters(df: pd.DataFrame, qp: Dict[str, str], services_col: Optional[str], alias_map: Dict[str, str]) -> pd.DataFrame:
    reserved = {
        "limit",
        "offset",
        "sort_by",
        "sort_order",
        "columns",
        "services_any",
        "services_all",
        "services_not",
        "refresh",
        "format",
    }

    filtered = df

    # Generic column filters with optional operators (e.g., preco__gte=1000)
    for raw_key, raw_value in qp.items():
        if raw_key in reserved:
            continue

        if "__" in raw_key:
            column, op = raw_key.split("__", 1)
        else:
            column, op = raw_key, "auto"

        if column not in filtered.columns:
            # tenta resolver por apelido
            alias = _normalize_name(column)
            if alias in alias_map:
                column = alias_map[alias]
            else:
                raise HTTPException(status_code=400, detail=f"Coluna desconhecida para filtro: {column}")

        series = filtered[column]
        val = raw_value

        # tenta converter números
        if op in {"lt", "lte", "gt", "gte", "between"}:
            # range-like ops esperam numéricos
            pass
        else:
            # para in/contains/eq, manter string se a coluna for objeto
            pass

        if op == "auto":
            if pd.api.types.is_numeric_dtype(series):
                comp = _try_parse_number(val)
                filtered = filtered[series == comp]
            else:
                filtered = filtered[series.astype(str).str.contains(str(val), case=False, na=False)]
        elif op == "eq":
            comp = _try_parse_number(val) if pd.api.types.is_numeric_dtype(series) else val
            if pd.api.types.is_string_dtype(series):
                filtered = filtered[series.astype(str).str.lower() == str(comp).lower()]
            else:
                filtered = filtered[series == comp]
        elif op == "contains":
            filtered = filtered[series.astype(str).str.contains(str(val), case=False, na=False)]
        elif op == "in":
            values = _parse_in_list(val)
            if pd.api.types.is_string_dtype(series):
                lowered = [v.lower() for v in values]
                filtered = filtered[series.astype(str).str.lower().isin(lowered)]
            else:
                parsed = [
                    _try_parse_number(v) if pd.api.types.is_numeric_dtype(series) else v for v in values
                ]
                filtered = filtered[series.isin(parsed)]
        elif op in {"lt", "lte", "gt", "gte"}:
            comp = _try_parse_number(val)
            if op == "lt":
                filtered = filtered[series < comp]
            elif op == "lte":
                filtered = filtered[series <= comp]
            elif op == "gt":
                filtered = filtered[series > comp]
            elif op == "gte":
                filtered = filtered[series >= comp]
        elif op == "between":
            parts = _parse_in_list(val)
            if len(parts) != 2:
                raise HTTPException(status_code=400, detail=f"Filtro between inválido para {column}. Use min,max")
            lo, hi = _try_parse_number(parts[0]), _try_parse_number(parts[1])
            filtered = filtered[(series >= lo) & (series <= hi)]
        elif op == "isnull":
            truthy = str(val).lower() in {"1", "true", "t", "yes", "y"}
            filtered = filtered[series.isna()] if truthy else filtered[series.notna()]
        else:
            raise HTTPException(status_code=400, detail=f"Operador desconhecido: {op} (coluna {column})")

    # Serviços específicos
    any_q = qp.get("services_any")
    all_q = qp.get("services_all")
    not_q = qp.get("services_not")

    if any_q or all_q or not_q:
        # trabalha sempre com coluna preprocessada services_list
        if "services_list" not in filtered.columns:
            filtered["services_list"] = [[] for _ in range(len(filtered))]

        def norm_list(v: Optional[str]) -> List[str]:
            if not v:
                return []
            return [s.strip().lower() for s in _parse_in_list(v)]

        any_list = set(norm_list(any_q))
        all_list = set(norm_list(all_q))
        not_list = set(norm_list(not_q))

        def matches(row_services: Iterable[str]) -> bool:
            sset = {s.strip().lower() for s in row_services if s}
            if any_list and sset.isdisjoint(any_list):
                return False
            if all_list and not all_list.issubset(sset):
                return False
            if not_list and not sset.isdisjoint(not_list):
                return False
            return True

        filtered = filtered[filtered["services_list"].apply(matches)]

    return filtered


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": app.title,
        "version": app.version,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {"boats": "/boats", "schema": "/schema"},
    }


@app.get("/schema")
def schema(refresh: bool = False) -> Dict[str, Any]:
    df, services_col, alias_map = _load_dataframe(refresh=refresh)
    cols = [
        {"name": str(c), "dtype": str(df[c].dtype)}
        for c in df.columns
        if c != "services_list"
    ]
    aliases = [{"alias": a, "column": o} for a, o in alias_map.items() if o != "services_list"]
    return {"columns": cols, "aliases": aliases, "services_column": services_col, "count": int(len(df))}


@app.get("/boats")
def list_boats(request: Request) -> Dict[str, Any]:
    qp = dict(request.query_params)

    refresh = str(qp.get("refresh", "false")).lower() in {"1", "true", "t", "yes", "y"}
    df, services_col, alias_map = _load_dataframe(refresh=refresh)

    filtered = _apply_generic_filters(df, qp, services_col, alias_map)

    # Ordenação
    sort_by = qp.get("sort_by")
    if sort_by:
        sort_cols: List[str] = []
        ascending: List[bool] = []
        for token in sort_by.split(","):
            token = token.strip()
            if not token:
                continue
            if token.startswith("-"):
                col = token[1:]
                asc = False
            elif token.startswith("+"):
                col = token[1:]
                asc = True
            else:
                col = token
                asc = True
            if col not in filtered.columns:
                alias = _normalize_name(col)
                if alias in alias_map:
                    col = alias_map[alias]
                else:
                    raise HTTPException(status_code=400, detail=f"Coluna inexistente para ordenação: {col}")
            sort_cols.append(col)
            ascending.append(asc)
        if sort_cols:
            filtered = filtered.sort_values(by=sort_cols, ascending=ascending, kind="mergesort")

    # Projeção de colunas
    columns = qp.get("columns")
    if columns:
        requested = [c.strip() for c in columns.split(",") if c.strip()]
        # Garante que id esteja presente
        if "id" not in requested:
            requested = ["id"] + requested
        resolved: List[str] = []
        missing: List[str] = []
        for c in requested:
            if c in filtered.columns:
                resolved.append(c)
            elif c == "services_list":
                continue
            else:
                alias = _normalize_name(c)
                if alias in alias_map:
                    resolved.append(alias_map[alias])
                else:
                    missing.append(c)
        if missing:
            raise HTTPException(status_code=400, detail=f"Colunas inexistentes na projeção: {', '.join(missing)}")
        filtered = filtered[resolved]

    # Paginação
    try:
        limit = int(qp.get("limit", "0"))
        offset = int(qp.get("offset", "0"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Parâmetros de paginação inválidos")

    total = int(len(filtered))
    if offset > 0:
        filtered = filtered.iloc[offset:]
    if limit and limit > 0:
        filtered = filtered.iloc[:limit]

    # Formato de saída
    include_services_list = str(qp.get("format", "")).lower() == "debug"
    data = _to_records(filtered, include_services_list=include_services_list)
    return {"total": total, "count": len(data), "items": data}


@app.get("/boats/{boat_id}")
def get_boat(boat_id: int, refresh: bool = False) -> Dict[str, Any]:
    df, _, _ = _load_dataframe(refresh=refresh)
    row = df[df["id"] == boat_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Barco não encontrado")
    return _to_records(row)[0]


