# 📋 Variáveis para Templates Word - Sistema Solar Fotovoltaico

## 🎯 Como usar no Word
Digite as variáveis entre colchetes `[variavel]` no documento Word.
**Exemplo:** `[nome_cliente]` será substituído por "Michel Nunes de Oliveira"

**⚠️ IMPORTANTE:** Use exatamente como mostrado (com colchetes, sem espaços, respeitando maiúsculas/minúsculas)

---

## 📊 DADOS DO PROJETO

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `[id_projeto]` | Número do projeto | 23 |
| `[projeto_titulo]` | Título/Código do projeto | 506255440 |
| `[nome_cliente]` | Nome completo do cliente | Michel Nunes de Oliveira |
| `[data_criacao]` | Data de criação | 06/01/2026 |
| `[status]` | Status do projeto | Ativo |

---

## 📍 ENDEREÇO E LOCALIZAÇÃO

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `[endereco]` | Endereço completo | Rua Hermes Casarini |
| `[numero]` | Número | 123 |
| `[complemento]` | Complemento | Casa |
| `[bairro]` | Bairro | Centro |
| `[cidade]` | Cidade | Tatuí |
| `[estado]` | Estado (UF) | SP |
| `[cep]` | CEP | 18270-000 |
| `[latitude]` | Latitude geográfica | -23,3487 |
| `[longitude]` | Longitude geográfica | -47,8461 |
{{geracao_estimada_ano}}     - Geração anual em kWh (ex: 5.112)
{{area_necessaria}}          - Área necessária em m² (ex: 21.5)
```

### Consumo e Tarifa
```
{{consumo_kwh_mes}}          - Consumo mensal em kWh (ex: 270)
{{consumo_kwh_ano}}          - Consumo anual em kWh
{{tarifa_kwh}}               - Tarifa por kWh (ex: 1.04)
{{tarifa_kwh_formatado}}     - Tarifa formatada (ex: R$ 1,04)
```

### Dados Solares
```
{{irradiacao_solar}}         - Irradiação solar média (ex: 4.82)
{{irradiacao_formatada}}     - Irradiação formatada (ex: 4,82 kWh/m².dia)
{{orientacao_telhado}}       - Orientação do telhado
{{tipo_telhado}}             - Tipo de telhado
{{estrutura_fixacao}}        - Tipo de estrutura
```

---

## 💰 VALORES FINANCEIROS

### Custos Detalhados
```
{{custo_equipamentos}}       - Custo dos equipamentos
{{custo_instalacao}}         - Custo de instalação
{{custo_projeto}}            - Custo do projeto
{{custo_total}}              - Custo total do sistema
{{valor_venda}}              - Valor de venda final
{{margem_lucro}}             - Margem de lucro (%)
```

### Custos Formatados (com R$)
```
{{custo_equipamentos_fmt}}   - Ex: R$ 7.107,79
{{custo_instalacao_fmt}}     - Ex: R$ 2.030,80
{{custo_projeto_fmt}}        - Ex: R$ 1.015,40
{{custo_total_fmt}}          - Ex: R$ 10.153,99
{{valor_venda_fmt}}          - Ex: R$ 10.153,99
```

### Retorno do Investimento
```
{{economia_mensal}}          - Economia mensal estimada
{{economia_anual}}           - Economia anual estimada
{{economia_25anos}}          - Economia total em 25 anos
{{payback_anos}}             - Payback em anos (ex: 4.2)
{{payback_meses}}            - Payback em meses (ex: 50)
{{payback_formatado}}        - Payback formatado (ex: 4 anos e 2 meses)
{{roi_percentual}}           - ROI em % (ex: 265.1)
```

### Valores Formatados de Economia
```
{{economia_mensal_fmt}}      - Ex: R$ 180,40
{{economia_anual_fmt}}       - Ex: R$ 2.164,80
{{economia_25anos_fmt}}      - Ex: R$ 258.989,60
```

---

## 🔧 EQUIPAMENTOS

### Painéis Solares
```
{{qtd_placas}}               - Quantidade de placas (ex: 6)
{{placa_modelo}}             - Modelo da placa (ex: DMEGC DM605M10)
{{placa_fabricante}}         - Fabricante (ex: DMEGC)
{{placa_potencia}}           - Potência unitária em Wp (ex: 605)
{{placa_tecnologia}}         - Tecnologia (ex: Monocristalino)
{{placa_garantia}}           - Garantia em anos (ex: 25)
{{placa_eficiencia}}         - Eficiência (ex: 21.5%)
```

### Inversores
```
{{qtd_inversores}}           - Quantidade de inversores (ex: 1)
{{inversor_modelo}}          - Modelo do inversor
{{inversor_fabricante}}      - Fabricante
{{inversor_potencia}}        - Potência nominal em kW (ex: 3.0)
{{inversor_tipo}}            - Tipo (ex: String)
{{inversor_garantia}}        - Garantia em anos
{{inversor_eficiencia}}      - Eficiência (ex: 97.5%)
```

### Kit Fotovoltaico (se aplicável)
```
{{kit_nome}}                 - Nome do kit
{{kit_descricao}}            - Descrição completa
{{kit_potencia}}             - Potência do kit
```

---

## 📈 CÁLCULOS E PROJEÇÕES

### Fatura de Energia
```
{{fatura_atual_mensal}}      - Fatura mensal atual
{{fatura_atual_anual}}       - Fatura anual atual
{{fatura_com_sistema}}       - Fatura com sistema (mínima)
{{economia_primeira_fatura}} - Economia na primeira fatura
```

### Projeção Financeira
```
{{total_economizado_5anos}}  - Total economizado em 5 anos
{{total_economizado_10anos}} - Total economizado em 10 anos
{{total_economizado_15anos}} - Total economizado em 15 anos
{{total_economizado_20anos}} - Total economizado em 20 anos
{{total_economizado_25anos}} - Total economizado em 25 anos
```

---

## 🏢 DADOS DA EMPRESA

### Identificação
```
{{empresa_nome}}             - Nome da empresa
{{empresa_razao}}            - Razão social
{{empresa_cnpj}}             - CNPJ
{{empresa_ie}}               - Inscrição Estadual
```

### Contato
```
{{empresa_telefone}}         - Telefone
{{empresa_celular}}          - Celular
{{empresa_email}}            - Email
{{empresa_site}}             - Website
```

### Endereço
```
{{empresa_endereco}}         - Endereço completo
{{empresa_logradouro}}       - Logradouro
{{empresa_numero}}           - Número
{{empresa_bairro}}           - Bairro
{{empresa_cidade}}           - Cidade
{{empresa_uf}}               - UF
{{empresa_cep}}              - CEP
```

---

## 📅 CONDIÇÕES COMERCIAIS

### Formas de Pagamento
```
{{forma_pagamento}}          - Forma de pagamento escolhida
{{condicao_pagamento}}       - Condição de pagamento
{{desconto_avista}}          - Desconto à vista (%)
{{valor_entrada}}            - Valor da entrada
{{qtd_parcelas}}             - Quantidade de parcelas
{{valor_parcela}}            - Valor da parcela
```

### Prazos
```
{{prazo_instalacao}}         - Prazo para instalação (dias)
{{prazo_homologacao}}        - Prazo para homologação (dias)
{{prazo_total}}              - Prazo total estimado (dias)
{{validade_proposta}}        - Validade da proposta (dias)
{{data_validade}}            - Data de validade da proposta
```

---

## 📋 INFORMAÇÕES TÉCNICAS

### Homologação
```
{{concessionaria}}           - Nome da concessionária
{{tipo_conexao}}             - Tipo de conexão (Monofásico/Bifásico/Trifásico)
{{tensao_rede}}              - Tensão da rede
{{grupo_tarifario}}          - Grupo tarifário (A ou B)
{{modalidade}}               - Modalidade de compensação
```

### Garantias
```
{{garantia_instalacao}}      - Garantia de instalação (anos)
{{garantia_paineis}}         - Garantia dos painéis (anos)
{{garantia_inversores}}      - Garantia dos inversores (anos)
{{garantia_estrutura}}       - Garantia da estrutura (anos)
```

---

## 🎨 FORMATAÇÃO ESPECIAL

### Valores Monetários
Adicione `_fmt` ou `_formatado` para valores em Real:
```
{{valor_venda_fmt}}          - R$ 10.153,99
```

### Datas
```
{{data_criacao}}             - 06/01/2026
{{data_criacao_extenso}}     - 06 de Janeiro de 2026
{{mes_ano}}                  - Janeiro/2026
```

### Números
```
{{potencia_kwp}}             - 3.63 (número puro)
{{potencia_kwp_formatado}}   - 3,63 kWp (formatado)
```

---

## 📊 TABELAS E LISTAS

### Loop de Equipamentos (para listas)
```
{% for item in lista_equipamentos %}
  - {{item.nome}} - Qtd: {{item.quantidade}} - Valor: {{item.valor_fmt}}
{% endfor %}
```

### Tabela Mensal de Geração
```
{% for mes in meses %}
  {{mes.nome}} | {{mes.geracao}} kWh | {{mes.economia_fmt}}
{% endfor %}
```

### Projeção 25 Anos
```
{% for ano in projecao_25anos %}
  Ano {{ano.numero}} | Economia: {{ano.economia_fmt}} | Acumulado: {{ano.acumulado_fmt}}
{% endfor %}
```

---

## 🔄 CONDICIONAIS

### Exemplo de uso condicional
```
{% if qtd_placas > 10 %}
  Sistema de grande porte
{% else %}
  Sistema residencial
{% endif %}
```

```
{% if cliente_tipo == 'PJ' %}
  CNPJ: {{cliente_cpf_cnpj}}
{% else %}
  CPF: {{cliente_cpf_cnpj}}
{% endif %}
```

---

## 💡 EXEMPLOS DE USO NO WORD

### Cabeçalho da Proposta
```
PROPOSTA COMERCIAL Nº {{projeto_id}}

Cliente: {{nome_cliente}}
Data: {{data_criacao}}
Validade: {{validade_proposta}} dias
```

### Resumo do Sistema
```
Sistema Fotovoltaico de {{potencia_kwp_formatado}}
Geração Estimada: {{geracao_estimada_mes}} kWh/mês
Quantidade de Placas: {{qtd_placas}} x {{placa_modelo}} ({{placa_potencia}}Wp)
Inversor: {{inversor_modelo}} ({{inversor_potencia}} kW)
```

### Valores
```
Investimento Total: {{valor_venda_fmt}}
Economia Mensal: {{economia_mensal_fmt}}
Retorno do Investimento: {{payback_formatado}}
Economia em 25 anos: {{economia_25anos_fmt}}
```

---

## 🚀 PRÓXIMOS PASSOS

1. Crie seu template Word (.docx)
2. Use as variáveis acima entre `{{` e `}}`
3. Salve o template em `app/energia_solar/templates/docs/template_proposta.docx`
4. O sistema vai substituir automaticamente os valores

**Dúvidas?** Todas as variáveis estão disponíveis no contexto do Python!
