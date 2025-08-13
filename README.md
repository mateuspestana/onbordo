## OnBordo API de Veleiros

API em FastAPI que lê a planilha `base_barcos_dummy.xlsx` e expõe endpoints para consultar barcos com filtros dinâmicos.

### Requisitos
- Python 3.9+
- Windows PowerShell

### Instalação e execução (PowerShell)
```powershell
cd C:\Users\matheus.pestana\Documents\onbordo

# 1) Criar e ativar ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Instalar dependências
python -m pip install -U pip
pip install -r requirements.txt

# 3) Subir a API (http://127.0.0.1:8000)
uvicorn app.main:app --reload
```

Ao subir, a documentação interativa estará em `http://127.0.0.1:8000/docs`.

### Endpoints
- `GET /` informações básicas
- `GET /schema` metadados e mapa de apelidos (`aliases`)
- `GET /boats` lista com filtros, ordenação, projeção e paginação
- `GET /boats/{id}` detalhe por `id`

### Apelidos (normalizados) para suas colunas
- `ID do Barco` → `id_do_barco`
- `Preço por Dia (R$)` → `preco_por_dia_rs`
- `Nome do Barco` → `nome_do_barco`
- `Marina/Porto` → `marina_porto`
- `Pés` → `pes`
- `Tripulante` → `tripulante`
- `Preço do Arrais (R$)` → `preco_do_arrais_rs`
- `Outros Serviços` → `outros_servicos` (coluna de serviços)

Veja todos em `GET /schema`.

### Exemplos
- `GET /boats?marina_porto=Angra dos Reis&preco_por_dia_rs__gte=1000`
- `GET /boats?services_any=skipper,combustivel&sort_by=-preco_por_dia_rs`
- `GET /boats?columns=id,nome_do_barco,preco_por_dia_rs&limit=5&offset=5`

