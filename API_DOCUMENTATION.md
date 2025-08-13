# OnBordo API - Documentação Completa

API FastAPI para aluguel de veleiros que lê dados de `base_barcos_dummy.xlsx` e oferece endpoints com filtros dinâmicos.

## Base URL
```
http://127.0.0.1:8000
```

## Documentação Interativa
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 📋 Endpoints Disponíveis

### 1. `GET /` - Informações Básicas

**Descrição**: Retorna informações gerais sobre a API.

**Parâmetros**: Nenhum

**Resposta**:
```json
{
  "name": "OnBordo - API de Veleiros",
  "version": "1.0.0",
  "docs": "/docs",
  "openapi": "/openapi.json",
  "endpoints": {
    "boats": "/boats",
    "schema": "/schema"
  }
}
```

---

### 2. `GET /schema` - Metadados da Planilha

**Descrição**: Retorna informações sobre colunas, apelidos e estrutura dos dados.

**Parâmetros**:
- `refresh` (opcional): `true` para recarregar planilha

**Resposta**:
```json
{
  "columns": [
    {"name": "id", "dtype": "mixed"},
    {"name": "ID do Barco", "dtype": "mixed"},
    {"name": "Preço por Dia (R$)", "dtype": "mixed"},
    {"name": "Nome do Barco", "dtype": "mixed"},
    {"name": "Marina/Porto", "dtype": "mixed"},
    {"name": "Pés", "dtype": "mixed"},
    {"name": "Tripulantes", "dtype": "mixed"},
    {"name": "Preço do Arrais (R$)", "dtype": "mixed"},
    {"name": "Outros Serviços", "dtype": "mixed"}
  ],
  "aliases": [
    {"alias": "id", "column": "id"},
    {"alias": "id_do_barco", "column": "ID do Barco"},
    {"alias": "preco_por_dia_rs", "column": "Preço por Dia (R$)"},
    {"alias": "nome_do_barco", "column": "Nome do Barco"},
    {"alias": "marina_porto", "column": "Marina/Porto"},
    {"alias": "pes", "column": "Pés"},
    {"alias": "tripulantes", "column": "Tripulantes"},
    {"alias": "preco_do_arrais_rs", "column": "Preço do Arrais (R$)"},
    {"alias": "outros_servicos", "column": "Outros Serviços"}
  ],
  "services_column": "Outros Serviços",
  "count": 32
}
```

---

### 3. `GET /boats` - Lista de Barcos

**Descrição**: Retorna lista de barcos com filtros, ordenação e paginação.

#### 🔍 Parâmetros de Filtragem

##### Filtros por Coluna (usando nome original ou apelido):

**Operadores Disponíveis**:
- **Sem operador** (auto): Igualdade para números, contém para texto
- `__eq`: Igualdade exata
- `__contains`: Contém texto (case-insensitive)
- `__in`: Está em lista (separada por vírgula)
- `__lt`: Menor que
- `__lte`: Menor ou igual
- `__gt`: Maior que
- `__gte`: Maior ou igual
- `__between`: Entre dois valores (min,max)
- `__isnull`: É nulo (`true`/`false`)

**Exemplos de Filtros**:
```
# Por preço
?preco_por_dia_rs__gte=2000          # Preço >= R$ 2000
?preco_por_dia_rs__between=1000,3000 # Preço entre R$ 1000-3000
?preco_por_dia_rs__lt=1500           # Preço < R$ 1500

# Por marina/porto
?marina_porto=Paraty                 # Marina exata
?marina_porto__contains=Rio          # Marina contendo "Rio"
?marina_porto__in=Paraty,Angra dos Reis # Marinas específicas

# Por nome do barco
?nome_do_barco__contains=Oceanis     # Nome contendo "Oceanis"

# Por pés
?pes__gte=40                         # Barcos >= 40 pés
?pes__between=30,50                  # Barcos entre 30-50 pés

# Por tripulantes
?tripulantes__lte=10                 # Até 10 tripulantes

# Por preço do arrais
?preco_do_arrais_rs__gt=0           # Com arrais pago
?preco_do_arrais_rs__isnull=true    # Sem arrais
```

##### Filtros Específicos de Serviços:
- `services_any`: Barco tem QUALQUER um dos serviços listados
- `services_all`: Barco tem TODOS os serviços listados
- `services_not`: Barco NÃO tem nenhum dos serviços listados

```
?services_any=Pesca,Mergulho         # Tem pesca OU mergulho
?services_all=Pesca,Travessia        # Tem pesca E travessia
?services_not=Combustível            # NÃO tem combustível
```

#### 📊 Parâmetros de Ordenação:
- `sort_by`: Colunas para ordenar (separadas por vírgula)
  - Prefixo `-` para decrescente
  - Prefixo `+` ou sem prefixo para crescente

```
?sort_by=-preco_por_dia_rs           # Por preço decrescente
?sort_by=marina_porto,+pes           # Por marina, depois pés crescente
?sort_by=-pes,preco_por_dia_rs       # Por pés desc, depois preço cresc
```

#### 📄 Parâmetros de Paginação:
- `limit`: Número máximo de resultados
- `offset`: Número de resultados para pular

```
?limit=10                            # Primeiros 10 resultados
?limit=5&offset=10                   # Resultados 11-15
```

#### 🎯 Parâmetros de Projeção:
- `columns`: Colunas específicas para retornar (separadas por vírgula)

```
?columns=id,nome_do_barco,preco_por_dia_rs
?columns=marina_porto,pes,tripulantes
```

#### 🔧 Parâmetros Especiais:
- `refresh`: `true` para recarregar planilha
- `format`: `debug` para incluir campo `services_list` interno

**Resposta**:
```json
{
  "total": 32,
  "count": 2,
  "items": [
    {
      "id": 0,
      "ID do Barco": 1,
      "Preço por Dia (R$)": 2497,
      "Nome do Barco": "Vento Carioca",
      "Marina/Porto": "Ilha Grande",
      "Pés": 25,
      "Tripulantes": 6,
      "Preço do Arrais (R$)": 400,
      "Outros Serviços": "Pesca"
    },
    {
      "id": 1,
      "ID do Barco": 2,
      "Preço por Dia (R$)": 1465,
      "Nome do Barco": "Maré Alta",
      "Marina/Porto": "Urca - Rio de Janeiro",
      "Pés": 50,
      "Tripulantes": 16,
      "Preço do Arrais (R$)": 200,
      "Outros Serviços": "Mergulho guiado, Travessia"
    }
  ]
}
```

---

### 4. `GET /boats/{id}` - Detalhes de um Barco

**Descrição**: Retorna detalhes de um barco específico pelo ID.

**Parâmetros**:
- `id` (path): ID do barco (número inteiro)
- `refresh` (opcional): `true` para recarregar planilha

**Resposta de Sucesso**:
```json
{
  "id": 0,
  "ID do Barco": 1,
  "Preço por Dia (R$)": 2497,
  "Nome do Barco": "Vento Carioca",
  "Marina/Porto": "Ilha Grande",
  "Pés": 25,
  "Tripulantes": 6,
  "Preço do Arrais (R$)": 400,
  "Outros Serviços": "Pesca"
}
```

**Resposta de Erro (404)**:
```json
{
  "detail": "Barco não encontrado"
}
```

---

## 🎯 Exemplos Práticos de Uso

### 1. Buscar barcos caros em Paraty
```
GET /boats?marina_porto=Paraty&preco_por_dia_rs__gte=2500&sort_by=-preco_por_dia_rs
```

### 2. Barcos grandes com serviços de pesca
```
GET /boats?pes__gte=35&services_any=Pesca&limit=5
```

### 3. Barcos econômicos no Rio de Janeiro
```
GET /boats?marina_porto__contains=Rio&preco_por_dia_rs__lt=2000&sort_by=preco_por_dia_rs
```

### 4. Barcos para grupos grandes com múltiplos serviços
```
GET /boats?tripulantes__gte=12&services_all=Travessia,Mergulho&columns=id,nome_do_barco,tripulantes,outros_servicos
```

### 5. Barcos sem arrais em qualquer marina
```
GET /boats?preco_do_arrais_rs__isnull=true&sort_by=marina_porto,preco_por_dia_rs
```

### 6. Busca paginada ordenada por tamanho
```
GET /boats?sort_by=-pes&limit=10&offset=0
```

---

## ⚠️ Códigos de Erro

### 400 - Bad Request
```json
{
  "detail": "Coluna desconhecida para filtro: coluna_inexistente"
}
```

```json
{
  "detail": "Operador desconhecido: operador_invalido (coluna nome_coluna)"
}
```

```json
{
  "detail": "Filtro between inválido para preco_por_dia_rs. Use min,max"
}
```

```json
{
  "detail": "Parâmetros de paginação inválidos"
}
```

### 404 - Not Found
```json
{
  "detail": "Barco não encontrado"
}
```

### 500 - Internal Server Error
```json
{
  "detail": "Arquivo Excel não encontrado em: caminho/para/arquivo.xlsx"
}
```

---

## 🗂️ Mapeamento de Colunas

| Nome Original | Apelido Normalizado | Tipo | Descrição |
|---------------|-------------------|------|-----------|
| `ID do Barco` | `id_do_barco` | Número | Identificador original do barco |
| `Preço por Dia (R$)` | `preco_por_dia_rs` | Número | Valor diário do aluguel |
| `Nome do Barco` | `nome_do_barco` | Texto | Nome/modelo do barco |
| `Marina/Porto` | `marina_porto` | Texto | Local de partida |
| `Pés` | `pes` | Número | Tamanho do barco em pés |
| `Tripulantes` | `tripulantes` | Número | Capacidade máxima |
| `Preço do Arrais (R$)` | `preco_do_arrais_rs` | Número | Custo adicional do capitão |
| `Outros Serviços` | `outros_servicos` | Texto | Serviços extras (separados por vírgula) |

---

## 🔄 Fluxo de Uso Recomendado

1. **Explorar estrutura**: `GET /schema`
2. **Listar todos**: `GET /boats`
3. **Filtrar por necessidades**: `GET /boats?filtros...`
4. **Obter detalhes**: `GET /boats/{id}`

---

## 📝 Notas Importantes

- Todos os filtros são **case-insensitive** para texto
- Múltiplos filtros são aplicados com **AND** lógico
- Serviços são detectados automaticamente na coluna "Outros Serviços"
- IDs são gerados sequencialmente a partir do índice da planilha (0, 1, 2...)
- Use `refresh=true` se a planilha foi modificada externamente
