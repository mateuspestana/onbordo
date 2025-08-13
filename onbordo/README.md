## OnBordo API de Veleiros

API em FastAPI que lê a planilha `base_barcos_dummy.xlsx` e expõe endpoints para consultar barcos com filtros dinâmicos.

### Requisitos
- Python 3.9+
- Windows PowerShell (você está no Windows)

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

### Estrutura
- `app/main.py`: aplicação FastAPI
- `base_barcos_dummy.xlsx`: fonte de dados

### Endpoints
- `GET /` informações básicas
- `GET /schema` metadados das colunas e contagem de linhas
- `GET /boats` lista de barcos com filtros, ordenação, projeção de colunas e paginação
- `GET /boats/{id}` detalhe de um barco por `id`

### Filtros e parâmetros
Todos os parâmetros são passados como query string. A API aceita tanto o nome exato da coluna da planilha quanto um "apelido" normalizado (sem acentos, espaços viram underscore). Você pode ver o mapa completo em `GET /schema` (campo `aliases`).

Para a planilha enviada, os apelidos típicos ficam assim:

- `ID do Barco` → `id_do_barco`
- `Preço por Dia (R$)` → `preco_por_dia_rs`
- `Nome do Barco` → `nome_do_barco`
- `Marina/Porto` → `marina_porto`
- `Pés` → `pes`
- `Tripulante` → `tripulante`
- `Preço do Arrais (R$)` → `preco_do_arrais_rs`
- `Outros Serviços` → `outros_servicos` (detectada como coluna de serviços)

- Filtros genéricos por coluna (detecta tipo automaticamente se for numérico):
  - Igualdade: `?marina_porto=Angra dos Reis`
  - Contém (case-insensitive): `?nome_do_barco__contains=Oceanis`
  - Em lista: `?marina_porto__in=Angra dos Reis,Paraty`
  - Menor/Maior: `?preco_por_dia_rs__lt=1500` `?preco_por_dia_rs__gte=1000`
  - Intervalo: `?preco_por_dia_rs__between=1000,2000`
  - Nulos: `?tripulante__isnull=true`

- Serviços (coluna `Outros Serviços`, com itens separados por vírgula na planilha):
  - Qualquer um: `?services_any=skipper,combustivel`
  - Todos: `?services_all=skipper,limpeza`
  - Excluir se tiver: `?services_not=combustivel`

- Ordenação e paginação:
  - Ordenar (por apelido ou nome original): `?sort_by=-preco_por_dia_rs,+pes`
  - Paginar: `?limit=10&offset=20`

- Projeção de colunas (quais colunas retornar):
  - `?columns=id,nome_do_barco,preco_por_dia_rs,marina_porto`

- Atualizar leitura do Excel em memória:
  - `?refresh=true` (recarrega a planilha no request atual)

### Exemplos
- Listar todos:
  - `GET http://127.0.0.1:8000/boats`
- Filtrar por marina/porto e preço mínimo:
  - `GET http://127.0.0.1:8000/boats?marina_porto=Angra dos Reis&preco_por_dia_rs__gte=1000`
- Serviços contendo qualquer entre `skipper` ou `combustivel` e ordenar por preço desc:
  - `GET http://127.0.0.1:8000/boats?services_any=skipper,combustivel&sort_by=-preco_por_dia_rs`
- Colunas específicas com paginação:
  - `GET http://127.0.0.1:8000/boats?columns=id,nome_do_barco,preco_por_dia_rs&limit=5&offset=5`

### Notas
- A API detecta automaticamente a coluna de serviços por nomes comuns: `outros_servicos`, `servicos`, `serviços`, `services`, `servico`, `serviço`.
- O campo `id` é gerado a partir do índice ao carregar a planilha.
- Use `format=debug` em `/boats` para inspecionar o campo auxiliar `services_list` que a API usa internamente.

