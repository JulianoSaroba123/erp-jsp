# 📋 LISTA COMPLETA DE VARIÁVEIS PARA PROPOSTA SOLAR

## ⚠️ SITUAÇÃO ATUAL DO DOCUMENTO
**Arquivo analisado:** `E:\Modelos de Documentos_Solar\Documento-JSPELE-0002 - Propsta Modelo 02-Usual.docx`

**Variáveis encontradas:** APENAS 2 de 40+
- {{CONSUMO_MENSAL}}
- {{CONSUMO_ANUAL}}

**Status:** ❌ INCOMPLETO - Faltam 38+ variáveis essenciais!

---

## ✅ TODAS AS 40+ VARIÁVEIS DISPONÍVEIS NO SISTEMA

### 👤 **1. DADOS DO CLIENTE (5 variáveis)**

```
{{NOME_CLIENTE}}           - Nome ou razão social do cliente
{{CPF_CNPJ_CLIENTE}}       - CPF ou CNPJ do cliente
{{CIDADE}}                 - Cidade do cliente/projeto
{{ESTADO}}                 - Estado (UF)
{{ENDERECO_CLIENTE}}       - Endereço completo do cliente
```

**Exemplo de uso no Word:**
```
PROPOSTA COMERCIAL PARA: {{NOME_CLIENTE}}
CPF/CNPJ: {{CPF_CNPJ_CLIENTE}}
Localização: {{CIDADE}}/{{ESTADO}}
```

---

### 📋 **2. DADOS DO PROJETO (3 variáveis)**

```
{{NUMERO_PROJETO}}         - ID/Número do projeto
{{DATA_PROPOSTA}}          - Data de emissão (gerada automaticamente)
{{VALIDADE_PROPOSTA}}      - Data de validade (+30 dias da emissão)
```

**Exemplo de uso no Word:**
```
Proposta Nº: {{NUMERO_PROJETO}}
Data: {{DATA_PROPOSTA}}
Válida até: {{VALIDADE_PROPOSTA}}
```

---

### ⚡ **3. DADOS TÉCNICOS DO SISTEMA (8 variáveis)**

```
{{POTENCIA_SISTEMA}}       - Potência total instalada (ex: "15,21 kWp")
{{QTD_MODULOS}}            - Quantidade de módulos solares
{{POTENCIA_MODULO}}        - Potência por módulo (ex: "605W")
{{MODELO_MODULO}}          - Modelo do módulo (ex: "DM605-144H")
{{FABRICANTE_MODULO}}      - Fabricante do módulo (ex: "DAH Solar")
{{MODELO_INVERSOR}}        - Modelo do inversor
{{FABRICANTE_INVERSOR}}    - Fabricante do inversor
{{POTENCIA_INVERSOR}}      - Potência do inversor (ex: "15000W")
```

**Exemplo de uso no Word:**
```
ESPECIFICAÇÕES TÉCNICAS:
- Potência Total: {{POTENCIA_SISTEMA}}
- Módulos: {{QTD_MODULOS}} x {{MODELO_MODULO}} ({{FABRICANTE_MODULO}})
- Inversor: {{MODELO_INVERSOR}} de {{POTENCIA_INVERSOR}} ({{FABRICANTE_INVERSOR}})
```

---

### 📊 **4. GERAÇÃO E CONSUMO (7 variáveis)**

```
{{GERACAO_MENSAL}}         - Geração estimada por mês (ex: "1.800 kWh/mês")
{{GERACAO_ANUAL}}          - Geração estimada por ano (ex: "21.600 kWh/ano")
{{CONSUMO_MENSAL}}         - Consumo mensal atual (ex: "1.520 kWh/mês")  ✅ JÁ EXISTE
{{CONSUMO_ANUAL}}          - Consumo anual (ex: "18.240 kWh/ano")        ✅ JÁ EXISTE
{{AREA_NECESSARIA}}        - Área necessária para instalação (ex: "65,00 m²")
{{IRRADIACAO_SOLAR}}       - Irradiação solar média (ex: "4,60 kWh/m².dia")
```

**Exemplo de uso no Word:**
```
BALANÇO ENERGÉTICO:
- Consumo Atual: {{CONSUMO_MENSAL}} ({{CONSUMO_ANUAL}})
- Geração Estimada: {{GERACAO_MENSAL}} ({{GERACAO_ANUAL}})
- Área Necessária: {{AREA_NECESSARIA}}
- Irradiação Local: {{IRRADIACAO_SOLAR}}
```

---

### 💰 **5. VALORES FINANCEIROS (9 variáveis)**

```
{{VALOR_INVESTIMENTO}}     - Valor total do investimento (ex: "R$ 28.497,50")
{{ECONOMIA_MENSAL}}        - Economia mensal estimada (ex: "R$ 1.245,80")
{{ECONOMIA_ANUAL}}         - Economia anual (ex: "R$ 14.949,60")
{{ECONOMIA_25_ANOS}}       - Economia acumulada em 25 anos (ex: "R$ 648.750,00")
{{PAYBACK}}                - Tempo de retorno do investimento (ex: "1,9 anos")
{{ROI_25_ANOS}}            - Retorno sobre investimento em 25 anos (ex: "2.177%")
```

**Exemplo de uso no Word:**
```
ANÁLISE FINANCEIRA:
Investimento Total: {{VALOR_INVESTIMENTO}}

ECONOMIA:
- Mensal: {{ECONOMIA_MENSAL}}
- Anual: {{ECONOMIA_ANUAL}}
- Em 25 anos: {{ECONOMIA_25_ANOS}}

RETORNO:
- Payback: {{PAYBACK}}
- ROI (25 anos): {{ROI_25_ANOS}}
```

---

### 💵 **6. COMPOSIÇÃO DE CUSTOS (3 variáveis)**

```
{{CUSTO_EQUIPAMENTOS}}     - Custo dos equipamentos (ex: "R$ 18.523,38")
{{CUSTO_INSTALACAO}}       - Custo da instalação (ex: "R$ 7.124,37")
{{CUSTO_PROJETO}}          - Custo do projeto (ex: "R$ 2.849,75")
```

**Exemplo de uso no Word:**
```
COMPOSIÇÃO DO INVESTIMENTO:
- Equipamentos: {{CUSTO_EQUIPAMENTOS}}
- Instalação: {{CUSTO_INSTALACAO}}
- Projeto: {{CUSTO_PROJETO}}
─────────────────────────
TOTAL: {{VALOR_INVESTIMENTO}}
```

---

### 🏢 **7. DADOS DA EMPRESA (5 variáveis)**

```
{{NOME_EMPRESA}}           - Nome da empresa (ex: "JSP Elétrica & Solar")
{{CNPJ_EMPRESA}}           - CNPJ da empresa
{{TELEFONE_EMPRESA}}       - Telefone (ex: "(15) 99670-2036")
{{EMAIL_EMPRESA}}          - E-mail (ex: "atendimento@eletricasaroba.com.br")
{{SITE_EMPRESA}}           - Site da empresa
```

**Exemplo de uso no Word:**
```
{{NOME_EMPRESA}}
CNPJ: {{CNPJ_EMPRESA}}
Tel: {{TELEFONE_EMPRESA}}
E-mail: {{EMAIL_EMPRESA}}
Site: {{SITE_EMPRESA}}
```

---

## 📝 **COMO ADICIONAR NO SEU DOCUMENTO WORD**

### **Método 1: Copiar e Colar**
1. Abra seu documento Word
2. Posicione o cursor onde quer a variável
3. Copie o código com as chaves duplas: `{{NOME_DA_VARIAVEL}}`
4. Cole no documento
5. Salve o arquivo

### **Método 2: Digitar Manualmente**
1. Digite duas chaves de abertura: `{{`
2. Digite o nome EXATO da variável (TUDO EM MAIÚSCULAS)
3. Digite duas chaves de fechamento: `}}`
4. Exemplo: `{{NOME_CLIENTE}}`

---

## ⚠️ **IMPORTANTE - REGRAS PARA AS VARIÁVEIS**

✅ **CERTO:**
- `{{NOME_CLIENTE}}` → Nome em maiúsculas, chaves duplas
- `{{VALOR_INVESTIMENTO}}` → Underline para separar palavras
- `{{QTD_MODULOS}}` → Abreviações permitidas

❌ **ERRADO:**
- `{NOME_CLIENTE}` → Chaves simples não funcionam
- `{{nome_cliente}}` → Minúsculas não funcionam
- `{{NOME CLIENTE}}` → Espaços não funcionam
- `{{ NOME_CLIENTE }}` → Espaços antes/depois não funcionam

---

## 🎯 **ESTRUTURA SUGERIDA PARA PROPOSTA COMPLETA**

### **PÁGINA 1 - CAPA**
```
PROPOSTA COMERCIAL DE ENERGIA SOLAR

{{NOME_EMPRESA}}
{{TELEFONE_EMPRESA}} | {{EMAIL_EMPRESA}}

PROPOSTA PARA:
{{NOME_CLIENTE}}
{{CIDADE}}/{{ESTADO}}

Proposta Nº: {{NUMERO_PROJETO}}
Data: {{DATA_PROPOSTA}}
Válida até: {{VALIDADE_PROPOSTA}}
```

### **PÁGINA 2 - APRESENTAÇÃO DO PROJETO**
```
SISTEMA FOTOVOLTAICO PROPOSTO

LOCALIZAÇÃO:
Cliente: {{NOME_CLIENTE}}
Endereço: {{ENDERECO_CLIENTE}}
Cidade: {{CIDADE}}/{{ESTADO}}

ESPECIFICAÇÕES TÉCNICAS:
Potência do Sistema: {{POTENCIA_SISTEMA}}
Módulos Solares: {{QTD_MODULOS}} x {{MODELO_MODULO}} ({{FABRICANTE_MODULO}})
Potência por Módulo: {{POTENCIA_MODULO}}
Inversor: {{MODELO_INVERSOR}} de {{POTENCIA_INVERSOR}} ({{FABRICANTE_INVERSOR}})
Área Necessária: {{AREA_NECESSARIA}}
```

### **PÁGINA 3 - ANÁLISE ENERGÉTICA**
```
BALANÇO ENERGÉTICO

CONSUMO ATUAL:
- Mensal: {{CONSUMO_MENSAL}}
- Anual: {{CONSUMO_ANUAL}}

GERAÇÃO ESTIMADA:
- Mensal: {{GERACAO_MENSAL}}
- Anual: {{GERACAO_ANUAL}}

DADOS DO LOCAL:
- Irradiação Solar Média: {{IRRADIACAO_SOLAR}}
```

### **PÁGINA 4 - INVESTIMENTO E RETORNO**
```
ANÁLISE FINANCEIRA

INVESTIMENTO TOTAL: {{VALOR_INVESTIMENTO}}

COMPOSIÇÃO DO INVESTIMENTO:
├─ Equipamentos: {{CUSTO_EQUIPAMENTOS}}
├─ Instalação: {{CUSTO_INSTALACAO}}
└─ Projeto: {{CUSTO_PROJETO}}

ECONOMIA ESTIMADA:
├─ Mensal: {{ECONOMIA_MENSAL}}
├─ Anual: {{ECONOMIA_ANUAL}}
└─ Em 25 anos: {{ECONOMIA_25_ANOS}}

RETORNO DO INVESTIMENTO:
├─ Payback: {{PAYBACK}}
└─ ROI (25 anos): {{ROI_25_ANOS}}
```

### **PÁGINA 5 - RODAPÉ/ASSINATURA**
```
{{NOME_EMPRESA}}
CNPJ: {{CNPJ_EMPRESA}}
Telefone: {{TELEFONE_EMPRESA}}
E-mail: {{EMAIL_EMPRESA}}
Site: {{SITE_EMPRESA}}

___________________________
Assinatura do Cliente

{{NOME_CLIENTE}}
CPF/CNPJ: {{CPF_CNPJ_CLIENTE}}
```

---

## 📊 **RESUMO**

| Categoria | Quantidade | Variáveis no Documento Atual |
|-----------|------------|------------------------------|
| **Cliente** | 5 variáveis | ❌ 0 de 5 |
| **Projeto** | 3 variáveis | ❌ 0 de 3 |
| **Técnicos** | 8 variáveis | ❌ 0 de 8 |
| **Geração** | 7 variáveis | ✅ 2 de 7 (CONSUMO_MENSAL, CONSUMO_ANUAL) |
| **Financeiro** | 9 variáveis | ❌ 0 de 9 |
| **Custos** | 3 variáveis | ❌ 0 de 3 |
| **Empresa** | 5 variáveis | ❌ 0 de 5 |
| **TOTAL** | **40 variáveis** | **❌ 2 de 40 (5%)** |

---

## 🎯 **PRÓXIMOS PASSOS**

1. ✅ Abra o documento Word original
2. ✅ Adicione as variáveis conforme os exemplos acima
3. ✅ Salve o documento como `proposta_solar_modelo.docx`
4. ✅ Coloque em: `app/energia_solar/templates_word/proposta_solar_modelo.docx`
5. ✅ Teste gerando uma proposta no sistema

---

## 🆘 **AJUDA RÁPIDA**

**Copie este bloco de teste e cole no seu Word:**
```
TESTE DE VARIÁVEIS:
Cliente: {{NOME_CLIENTE}}
Sistema: {{POTENCIA_SISTEMA}} com {{QTD_MODULOS}} módulos
Investimento: {{VALOR_INVESTIMENTO}}
Payback: {{PAYBACK}}
```

Se aparecer assim no PDF gerado:
```
Cliente: João da Silva Ltda
Sistema: 15,21 kWp com 26 módulos
Investimento: R$ 28.497,50
Payback: 1,9 anos
```

✅ **Está funcionando!** Continue adicionando as outras variáveis.

---

**Gerado pelo Sistema ERP JSP v3.0**
**Data: 22/05/2026**
