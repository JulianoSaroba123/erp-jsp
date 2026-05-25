# 📦 Exportação e Importação - Módulo Energia Solar

Este diretório contém os arquivos de exportação dos dados do módulo de Energia Solar do ERP JSP v3.0.

## 🔧 Scripts Disponíveis

### 1. Exportar Dados
**Arquivo:** `exportar_energia_solar.py` (na raiz do projeto)

**Uso:**
```bash
python exportar_energia_solar.py
```

**O que faz:**
- Exporta TODOS os dados do módulo Energia Solar
- Cria arquivo JSON com timestamp no formato: `energia_solar_export_YYYYMMDD_HHMMSS.json`
- Salva automaticamente nesta pasta `exports/`

**Dados exportados:**
- ✅ Cálculos de Energia Solar
- ✅ Projetos Solares
- ✅ Kits Solares
- ✅ Placas Solares
- ✅ Inversores Solares
- ✅ Custos Padrão
- ✅ Itens de Orçamento

---

### 2. Importar Dados
**Arquivo:** `importar_energia_solar.py` (na raiz do projeto)

**Uso básico:**
```bash
# Importa o arquivo mais recente automaticamente
python importar_energia_solar.py

# Importa arquivo específico
python importar_energia_solar.py exports/energia_solar_export_20260525_183126.json

# Importa com limpeza prévia (CUIDADO!)
python importar_energia_solar.py --limpar
```

**O que faz:**
- Lê arquivo JSON de exportação
- Importa todos os dados para o banco de dados
- Evita duplicação de IDs (modo incremental)
- Opção de limpar dados antes da importação

**Opções:**
- `--limpar` ou `-l`: Limpa TODOS os dados existentes antes de importar (pede confirmação)
- Sem arquivo: usa o export mais recente da pasta `exports/`

---

## 📊 Formato do Arquivo JSON

```json
{
  "calculos_energia_solar": [...],
  "projetos_solares": [...],
  "kits_solares": [...],
  "placas_solares": [...],
  "inversores_solares": [...],
  "custos_padrao": [...],
  "orcamento_itens": [...],
  "metadata": {
    "data_exportacao": "2026-05-25T18:31:26",
    "versao": "1.0"
  }
}
```

---

## 🎯 Casos de Uso

### Backup Regular
```bash
# Exportar dados semanalmente
python exportar_energia_solar.py
```

### Migração entre Ambientes
```bash
# No servidor de origem (produção)
python exportar_energia_solar.py

# Copiar arquivo para servidor destino (dev/homologação)
# No servidor destino
python importar_energia_solar.py exports/energia_solar_export_20260525_183126.json
```

### Restaurar Dados
```bash
# Limpar e restaurar do backup
python importar_energia_solar.py --limpar exports/energia_solar_export_20260525_183126.json
```

### Sincronizar Catálogos
```bash
# Exportar apenas catálogos (kits, placas, inversores, custos)
# Importar em outro ambiente mantendo projetos locais
python importar_energia_solar.py exports/energia_solar_export_20260525_183126.json
```

---

## ⚠️ Avisos Importantes

### ⚠️ Antes de Importar com --limpar
- **BACKUP OBRIGATÓRIO**: Sempre faça backup antes de limpar dados!
- Esta ação **APAGA PERMANENTEMENTE** todos os dados de energia solar
- Não há como desfazer após a confirmação

### ⚠️ Ordem de Importação
O script respeita automaticamente a ordem correta devido a relacionamentos:
1. Placas (independente)
2. Inversores (independente)
3. Kits (depende de placas e inversores)
4. Projetos (independente)
5. Cálculos (independente)
6. Custos Padrão (independente)
7. Itens de Orçamento (depende de projetos)

### ⚠️ IDs Duplicados
- O script **não sobrescreve** dados existentes
- Se encontrar ID duplicado, pula o registro
- Use `--limpar` se quiser substituir tudo

---

## 🔍 Verificação Pós-Importação

Após importar, verifique os dados:

```python
# No console Python ou script
from app.app import criar_app
from app.energia_solar.catalogo_model import KitSolar, PlacaSolar, InversorSolar

app = criar_app()
with app.app_context():
    print(f"Kits: {KitSolar.query.count()}")
    print(f"Placas: {PlacaSolar.query.count()}")
    print(f"Inversores: {InversorSolar.query.count()}")
```

---

## 📝 Logs e Erros

Ambos os scripts fornecem output detalhado:
- ✅ Sucesso
- ⚠️ Avisos (registros duplicados, campos faltantes)
- ❌ Erros (falha ao importar registro específico)

Os erros **não interrompem** a importação - o script continua com os próximos registros.

---

## 🆘 Solução de Problemas

### Erro: "Tabela não encontrada"
```bash
# Criar/atualizar tabelas primeiro
python scripts/criar_tabelas.py
```

### Erro: "Arquivo não encontrado"
```bash
# Verificar se o arquivo existe
ls exports/
# Ou usar caminho absoluto
python importar_energia_solar.py C:\ERP_JSP\exports\arquivo.json
```

### Erro: "Foreign key constraint"
- Significa que há dependências faltantes (ex: kit referencia placa inexistente)
- Solução: Importar com `--limpar` para garantir consistência completa

---

## 📚 Mais Informações

- **Documentação do Módulo:** Ver `MODULO_ENERGIA_SOLAR.md` na raiz
- **Estrutura do Banco:** Ver `app/energia_solar/` para modelos
- **Suporte:** Abrir issue no repositório do projeto

---

**Última atualização:** 25/05/2026  
**Versão:** 1.0  
**ERP JSP v3.0** 🚀
