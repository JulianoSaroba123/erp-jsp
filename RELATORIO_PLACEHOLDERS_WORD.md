# 📊 RELATÓRIO COMPLETO DE PLACEHOLDERS WORD

**Data:** 25/05/2026 (Atualizado)  
**Template:** `proposta_solar_modelo.docx`  
**Arquivo de contexto:** `app/energia_solar/proposta_word_service.py`

---

## ✅ RESUMO EXECUTIVO

- **Placeholders no template:** 19
- **Placeholders disponíveis no código:** 69+
- **Cobertura:** 27.5%
- **Status:** ✅ Sistema funcionando corretamente
- **Aliases críticos:** ✅ VALOR e EMPRESA corrigidos

---

## 📋 TABELA COMPLETA DE PLACEHOLDERS

### 🟢 PLACEHOLDERS ATIVOS NO TEMPLATE (19)

| Categoria | Placeholder | Descrição | Status | Valor Exemplo |
|-----------|-------------|-----------|--------|---------------|
| 👤 **Cliente** | `NOME_CLIENTE` | Nome/razão social do cliente | ✅ ATIVO | João Silva |
| 👤 Cliente | `CIDADE` | Cidade do cliente | ✅ ATIVO | Sorocaba |
| 👤 Cliente | `ESTADO` | Estado (UF) do cliente | ✅ ATIVO | SP |
| 👤 Cliente | `ENDERECO_CLIENTE` | Endereço completo do cliente | ✅ ATIVO | Rua das Flores, 123 |
| 📋 **Projeto** | `NUMERO_PROJETO` | ID numérico do projeto | ✅ ATIVO | 42 |
| 📋 Projeto | `DATA_PROPOSTA` | Data de criação da proposta | ✅ ATIVO | 25/05/2026 |
| 📋 Projeto | `VALIDADE_PROPOSTA` | Data de validade (15 dias) | ✅ ATIVO | 09/06/2026 |
| ⚡ **Técnico** | `POTENCIA_SISTEMA` | Potência total em kWp | ✅ ATIVO | 5,50 kWp |
| ⚡ Técnico | `QTD_MODULOS` | Quantidade de painéis | ✅ ATIVO | 10 |
| ⚡ Técnico | `POTENCIA_MODULO` | Potência de cada painel | ✅ ATIVO | 550W |
| ⚡ Técnico | `MODELO_MODULO` | Modelo do painel solar | ✅ ATIVO | Jinko Tiger Neo 550W |
| ⚡ Técnico | `FABRICANTE_MODULO` | Fabricante do painel | ✅ ATIVO | Jinko Solar |
| 📊 **Geração** | `GERACAO_MENSAL` | Geração média mensal | ✅ ATIVO | 725 kWh/mês |
| 📊 Geração | `CONSUMO_MENSAL` | Consumo médio mensal | ✅ ATIVO | 650 kWh/mês |
| 📊 Geração | `CONSUMO_ANUAL` | Consumo anual total | ✅ ATIVO | 7.800 kWh/ano |
| 📊 Geração | `AREA_NECESSARIA` | Área para instalação | ✅ ATIVO | 25,00 m² |
| 📊 Geração | `IRRADIACAO_SOLAR` | Irradiação solar local | ✅ ATIVO | 5,20 kWh/m².dia |
| 💰 **Financeiro** | `VALOR` | Valor total (alias) | ✅ ATIVO | R$ 25.500,00 |
| 🏢 **Empresa** | `EMPRESA` | Nome da empresa (alias) | ✅ ATIVO | JSP Elétrica & Solar |

---

## 🔵 PLACEHOLDERS DISPONÍVEIS (Não usados no template - 50+)

### 👤 **Dados do Cliente Completos** (Prioridade: ⭐⭐⭐)

| Placeholder | Descrição | Valor Exemplo | Recomendação |
|-------------|-----------|---------------|--------------|
| `CPF_CNPJ_CLIENTE` | CPF ou CNPJ do cliente | 123.456.789-00 | ⭐⭐⭐ Importante |
| `TELEFONE_CLIENTE` | Telefone de contato | (15) 99999-8888 | ⭐⭐⭐ Importante |
| `EMAIL_CLIENTE` | E-mail do cliente | cliente@email.com | ⭐⭐⭐ Importante |
| `CEP_CLIENTE` | CEP do endereço | 18000-000 | ⭐⭐ Opcional |

---

### 💰 **Dados Financeiros Detalhados** (Prioridade: ⭐⭐⭐)

| Placeholder | Descrição | Valor Exemplo | Recomendação |
|-------------|-----------|---------------|--------------|
| `VALOR_INVESTIMENTO` | Valor total do investimento | R$ 25.500,00 | ⭐⭐⭐ CRITICAL |
| `ECONOMIA_MENSAL` | Economia na conta de luz/mês | R$ 550,00 | ⭐⭐⭐ CRITICAL |
| `ECONOMIA_ANUAL` | Economia total por ano | R$ 6.600,00 | ⭐⭐⭐ CRITICAL |
| `ECONOMIA_25_ANOS` | Economia em 25 anos | R$ 165.000,00 | ⭐⭐⭐ CRITICAL |
| `PAYBACK` | Tempo de retorno do investimento | 3,9 anos | ⭐⭐⭐ CRITICAL |
| `ROI_25_ANOS` | Retorno sobre investimento | 547% | ⭐⭐⭐ CRITICAL |
| `CONTA_LUZ_ATUAL` | Valor atual da conta de luz | R$ 650,00 | ⭐⭐⭐ Muito importante |
| `CONTA_LUZ_FUTURA` | Valor futuro (com solar) | R$ 100,00 | ⭐⭐⭐ Muito importante |
| `REDUCAO_PERCENTUAL` | Percentual de redução | 85% | ⭐⭐⭐ Muito importante |
| `PERCENTUAL_COMPENSACAO` | % de compensação da energia | 100% | ⭐⭐ Importante |
| `PRECO_KWH` | Tarifa de energia (R$/kWh) | R$ 0,8500 | ⭐⭐ Importante |
| `TARIFA_ENERGIA` | Tarifa de energia (alias) | R$ 0,8500 | ⭐⭐ Importante |
| `FATURA_SEM_SISTEMA` | Fatura antes do sistema | R$ 650,00 | ⭐⭐ Opcional |
| `FATURA_COM_SISTEMA` | Fatura após o sistema | R$ 100,00 | ⭐⭐ Opcional |
| `FATURA_MINIMA_TECNICA` | Fatura mínima obrigatória | R$ 100,00 | ⭐ Opcional |
| `ADICIONAIS_FATURA` | Custos adicionais (CIP, etc) | R$ 45,00 | ⭐ Opcional |
| `ACRESCIMO_ANUAL_PERCENTUAL` | Reajuste anual da energia | 10,00% | ⭐⭐ Importante |
| `REAJUSTE_ANUAL` | Reajuste anual (alias) | 10,00% | ⭐⭐ Importante |

---

### 💵 **Custos Detalhados** (Prioridade: ⭐⭐)

| Placeholder | Descrição | Valor Exemplo | Recomendação |
|-------------|-----------|---------------|--------------|
| `CUSTO_EQUIPAMENTOS` | Custo dos equipamentos | R$ 18.000,00 | ⭐⭐ Importante |
| `CUSTO_INSTALACAO` | Custo da instalação | R$ 6.000,00 | ⭐⭐ Importante |
| `CUSTO_PROJETO` | Custo do projeto | R$ 1.500,00 | ⭐⭐ Importante |

---

### ⚡ **Dados Técnicos do Inversor** (Prioridade: ⭐⭐⭐)

| Placeholder | Descrição | Valor Exemplo | Recomendação |
|-------------|-----------|---------------|--------------|
| `MODELO_INVERSOR` | Modelo do inversor | Growatt MIN 5000TL-XH | ⭐⭐⭐ Muito importante |
| `FABRICANTE_INVERSOR` | Fabricante do inversor | Growatt | ⭐⭐⭐ Muito importante |
| `POTENCIA_INVERSOR` | Potência nominal do inversor | 5,00 kW | ⭐⭐⭐ Muito importante |
| `GARANTIA_INVERSOR` | Garantia do inversor | 10 anos | ⭐⭐ Importante |

---

### 📊 **Dados Técnicos Adicionais** (Prioridade: ⭐⭐)

| Placeholder | Descrição | Valor Exemplo | Recomendação |
|-------------|-----------|---------------|--------------|
| `GERACAO_ANUAL` | Geração anual estimada | 8.700 kWh/ano | ⭐⭐ Importante |
| `TIPO_INSTALACAO` | Tipo de instalação elétrica | Bifásica | ⭐⭐ Importante |
| `GARANTIA_MODULOS` | Garantia dos painéis | 25 anos (potência) | ⭐⭐ Importante |
| `VIDA_UTIL_SISTEMA` | Vida útil do sistema | 25 anos | ⭐⭐ Importante |
| `CONSUMO_MINIMO_KWH` | Consumo mínimo da concessionária | 50 kWh | ⭐ Opcional |

---

### 🏢 **Dados da Empresa** (Prioridade: ⭐⭐⭐)

| Placeholder | Descrição | Valor Exemplo | Recomendação |
|-------------|-----------|---------------|--------------|
| `NOME_EMPRESA` | Nome fantasia da empresa | JSP Elétrica & Solar | ⭐⭐⭐ Muito importante |
| `CNPJ_EMPRESA` | CNPJ da empresa | 12.345.678/0001-90 | ⭐⭐ Importante |
| `TELEFONE_EMPRESA` | Telefone comercial | (15) 99670-2036 | ⭐⭐⭐ Muito importante |
| `EMAIL_EMPRESA` | E-mail comercial | atendimento@eletricasaroba.com.br | ⭐⭐⭐ Muito importante |
| `SITE_EMPRESA` | Website da empresa | www.eletricasaroba.com.br | ⭐⭐ Importante |

---

### 📝 **Condições Comerciais** (Prioridade: ⭐⭐⭐)

| Placeholder | Descrição | Valor Exemplo | Recomendação |
|-------------|-----------|---------------|--------------|
| `FORMA_PAGAMENTO` | Condições de pagamento | À vista ou parcelado | ⭐⭐⭐ Muito importante |
| `PRAZO_ENTREGA` | Prazo de entrega | 45 dias úteis | ⭐⭐⭐ Muito importante |
| `PRAZO_INSTALACAO` | Prazo de instalação | 7 a 15 dias úteis | ⭐⭐⭐ Muito importante |
| `PRAZO_TOTAL` | Prazo total do projeto | 60 dias úteis | ⭐⭐ Importante |

---

### 🛠️ **Informações do Kit** (Prioridade: ⭐)

| Placeholder | Descrição | Valor Exemplo | Recomendação |
|-------------|-----------|---------------|--------------|
| `KIT_DESCRICAO` | Descrição do kit solar | Kit Residencial 5kWp | ⭐ Opcional |
| `OUTRAS_DESCRICOES` | Outras descrições/observações | Inclui estruturas e cabos | ⭐ Opcional |

---

## 🔧 ALIASES CONFIGURADOS

| Alias Curto | Placeholder Original | Status |
|-------------|---------------------|--------|
| `VALOR` | `VALOR_INVESTIMENTO` | ✅ Funcionando |
| `EMPRESA` | `NOME_EMPRESA` | ✅ Funcionando |
| `cliente_nome` | `NOME_CLIENTE` | ✅ Funcionando |
| `cliente_cpf_cnpj` | `CPF_CNPJ_CLIENTE` | ✅ Funcionando |
| `id_projeto` | `NUMERO_PROJETO` | ✅ Funcionando |
| `data_proposta` | `DATA_PROPOSTA` | ✅ Funcionando |

---

## � RECOMENDAÇÕES PRIORITÁRIAS

### 🎯 Top 10 Placeholders para Adicionar ao Template

1. **`VALOR_INVESTIMENTO`** ⭐⭐⭐ - Valor total é essencial em propostas
2. **`ECONOMIA_MENSAL`** ⭐⭐⭐ - Principal argumento de venda
3. **`ECONOMIA_ANUAL`** ⭐⭐⭐ - Reforça o benefício financeiro
4. **`PAYBACK`** ⭐⭐⭐ - Tempo de retorno é decisivo para o cliente
5. **`MODELO_INVERSOR`** ⭐⭐⭐ - Complementa dados técnicos
6. **`FABRICANTE_INVERSOR`** ⭐⭐⭐ - Transparência técnica
7. **`TELEFONE_CLIENTE`** ⭐⭐⭐ - Contato essencial
8. **`CPF_CNPJ_CLIENTE`** ⭐⭐⭐ - Identificação legal
9. **`FORMA_PAGAMENTO`** ⭐⭐⭐ - Condições comerciais
10. **`PRAZO_ENTREGA`** ⭐⭐⭐ - Expectativa de timeline

---

## 📊 ESTATÍSTICAS

| Métrica | Valor |
|---------|-------|
| **Total de placeholders no código** | 69+ |
| **Placeholders no template** | 19 |
| **Cobertura atual** | 27,5% |
| **Aliases funcionando** | 6 |
| **Placeholders críticos faltando** | ~15 |

---

## ✅ STATUS DO SISTEMA

- ✅ **Sistema de substituição**: Funcionando perfeitamente
- ✅ **Aliases críticos**: VALOR e EMPRESA corrigidos
- ✅ **Fallback XML**: Implementado para text boxes
- ✅ **Geração de PDF**: Suportada (via LibreOffice)
- ✅ **Documentação**: Completa e atualizada

---

## 🔍 COMO USAR ESTE RELATÓRIO

1. **Abra o template Word** em `app/energia_solar/templates_word/proposta_solar_modelo.docx`
2. **Adicione novos placeholders** da tabela acima conforme necessidade
3. **Use o formato UPPERCASE** sem chaves: `NOME_PLACEHOLDER`
4. **Teste a geração** pela rota `/energia-solar/proposta-word/<id>`
5. **Verifique o resultado** - todos os placeholders devem ser substituídos

---

## 📁 ARQUIVOS RELACIONADOS

- **Template Word**: `app/energia_solar/templates_word/proposta_solar_modelo.docx`
- **Contexto/Dados**: `app/energia_solar/proposta_word_service.py` (função `montar_contexto_proposta()`)
- **Substituição**: `app/energia_solar/word_utils.py` (função `substituir_variaveis_word()`)
- **Aliases**: `app/energia_solar/word_utils.py` (função `_expandir_aliases_variaveis()`)
- **Rota**: `app/energia_solar/energia_solar_routes.py` (rota `/proposta-word/<int:id>`)

---

## 💡 DICAS DE USO

### Como adicionar um novo placeholder ao template:

1. Abra o arquivo `.docx` no Word
2. Digite o placeholder em MAIÚSCULAS (ex: `ECONOMIA_MENSAL`)
3. Salve o arquivo
4. O sistema automaticamente substituirá na geração

### Como adicionar um novo dado ao contexto:

1. Edite `app/energia_solar/proposta_word_service.py`
2. Adicione a variável no dicionário `contexto` da função `montar_contexto_proposta()`
3. Use UPPERCASE para o nome da chave
4. Formate o valor apropriadamente (use `formatar_moeda()` para valores monetários)

### Como criar um alias:

1. Edite `app/energia_solar/word_utils.py`
2. Na função `_expandir_aliases_variaveis()`, adicione:
   ```python
   if 'PLACEHOLDER_ORIGINAL' in expandidas:
       expandidas['ALIAS_CURTO'] = expandidas['PLACEHOLDER_ORIGINAL']
   ```

---

**Última atualização:** 25/05/2026  
**Mantido por:** Sistema ERP JSP v3.0

#### 🏢 Empresa (5)
- `NOME_EMPRESA` ⭐⭐⭐
- `CNPJ_EMPRESA` ⭐⭐
- `TELEFONE_EMPRESA` ⭐⭐
- `EMAIL_EMPRESA` ⭐⭐
- `SITE_EMPRESA` ⭐

#### 📋 Comercial (4)
- `FORMA_PAGAMENTO` ⭐⭐
- `PRAZO_ENTREGA` ⭐⭐
- `PRAZO_INSTALACAO` ⭐
- `PRAZO_TOTAL` ⭐

---

## 🔧 AÇÕES NECESSÁRIAS

### 1. Adicionar Aliases Faltantes no Código

Os placeholders `VALOR` e `EMPRESA` no template precisam de aliases:

**Arquivo:** `app/energia_solar/word_utils.py`
**Função:** `_expandir_aliases_variaveis()`

Adicionar:
```python
if 'VALOR_INVESTIMENTO' in expandidas:
    expandidas['VALOR'] = expandidas['VALOR_INVESTIMENTO']
if 'NOME_EMPRESA' in expandidas:
    expandidas['EMPRESA'] = expandidas['NOME_EMPRESA']
```

### 2. Enriquecer o Template Word (Opcional)

Para melhorar as propostas, considere adicionar ao template:

**Prioridade ALTA (⭐⭐⭐):**
- `VALOR_INVESTIMENTO`
- `ECONOMIA_MENSAL`
- `ECONOMIA_ANUAL`
- `PAYBACK`
- `NOME_EMPRESA`
- `CPF_CNPJ_CLIENTE`
- `TELEFONE_CLIENTE`
- `EMAIL_CLIENTE`

**Prioridade MÉDIA (⭐⭐):**
- `FABRICANTE_INVERSOR`
- `MODELO_INVERSOR`
- `POTENCIA_INVERSOR`
- `CUSTO_EQUIPAMENTOS`
- `CUSTO_INSTALACAO`
- `CONTA_LUZ_ATUAL`
- `CONTA_LUZ_FUTURA`

---

## ✅ COMO IMPLEMENTAR

### Para Adicionar Placeholder no Template Word:

1. Abra `proposta_solar_modelo.docx` no Microsoft Word
2. Digite a palavra em MAIÚSCULAS onde deseja o dado dinâmico
   - Exemplo: `VALOR_INVESTIMENTO`
3. Salve o documento
4. O sistema substituirá automaticamente na geração

### Para Verificar se um Placeholder Está Disponível:

Execute:
```bash
python validar_placeholders_word.py
```

---

## 📈 RECOMENDAÇÕES

1. **Corrigir Aliases Imediatamente** ✅
   - Adicionar aliases para `VALOR` e `EMPRESA` no código

2. **Enriquecer Template Gradualmente** 📝
   - Começar pelos placeholders de prioridade ALTA
   - Testar após cada adição

3. **Documentar Mudanças** 📚
   - Atualizar `README_PLACEHOLDERS.md` se necessário

4. **Validar Regularmente** 🔍
   - Usar script `validar_placeholders_word.py` após mudanças

---

## 🎯 META

**Objetivo:** Alcançar **80%+ de cobertura** (42+ placeholders usados)

**Estado Atual:** 35.8% (19 placeholders)
**Faltam:** 23 placeholders para atingir meta

---

*Relatório gerado automaticamente por `validar_placeholders_word.py`*
