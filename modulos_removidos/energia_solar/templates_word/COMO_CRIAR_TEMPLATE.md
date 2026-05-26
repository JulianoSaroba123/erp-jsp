# INSTRUÇÕES: Como Criar o Template Word

## ⚠️ IMPORTANTE
Você precisa criar manualmente o arquivo Word em:
```
app/energia_solar/templates_word/proposta_solar_modelo.docx
```

## 📝 Conteúdo Sugerido para o Template

Abra o Microsoft Word e cole o texto abaixo (ou crie seu próprio layout):

---

═══════════════════════════════════════════════════════════════
                    PROPOSTA COMERCIAL
         SISTEMA DE ENERGIA SOLAR FOTOVOLTAICA
═══════════════════════════════════════════════════════════════

DADOS DO CLIENTE
────────────────────────────────────────────────────────────────
Cliente: {{NOME_CLIENTE}}
CPF/CNPJ: {{CPF_CNPJ_CLIENTE}}
Endereço: {{ENDERECO_CLIENTE}}
Cidade: {{CIDADE}} - {{ESTADO}}

DADOS DA PROPOSTA
────────────────────────────────────────────────────────────────
Proposta Nº: {{NUMERO_PROJETO}}
Data de Emissão: {{DATA_PROPOSTA}}
Validade: {{VALIDADE_PROPOSTA}}

═══════════════════════════════════════════════════════════════
                  ESPECIFICAÇÕES TÉCNICAS
═══════════════════════════════════════════════════════════════

🔋 SISTEMA PROPOSTO
────────────────────────────────────────────────────────────────
Potência do Sistema: {{POTENCIA_SISTEMA}}
Área Necessária: {{AREA_NECESSARIA}}
Irradiação Solar Média: {{IRRADIACAO_SOLAR}}

☀️ MÓDULOS FOTOVOLTAICOS
────────────────────────────────────────────────────────────────
Quantidade: {{QTD_MODULOS}} unidades
Fabricante: {{FABRICANTE_MODULO}}
Modelo: {{MODELO_MODULO}}
Potência Unitária: {{POTENCIA_MODULO}}

⚡ INVERSOR
────────────────────────────────────────────────────────────────
Fabricante: {{FABRICANTE_INVERSOR}}
Modelo: {{MODELO_INVERSOR}}
Potência: {{POTENCIA_INVERSOR}}

═══════════════════════════════════════════════════════════════
                   ESTIMATIVA DE GERAÇÃO
═══════════════════════════════════════════════════════════════

📊 PRODUÇÃO DE ENERGIA
────────────────────────────────────────────────────────────────
Geração Mensal Estimada: {{GERACAO_MENSAL}}
Geração Anual Estimada: {{GERACAO_ANUAL}}
Consumo Mensal Atual: {{CONSUMO_MENSAL}}
Consumo Anual Atual: {{CONSUMO_ANUAL}}

═══════════════════════════════════════════════════════════════
                    INVESTIMENTO FINANCEIRO
═══════════════════════════════════════════════════════════════

💰 COMPOSIÇÃO DO INVESTIMENTO
────────────────────────────────────────────────────────────────
Equipamentos: {{CUSTO_EQUIPAMENTOS}}
Instalação: {{CUSTO_INSTALACAO}}
Projeto e Documentação: {{CUSTO_PROJETO}}
────────────────────────────────────────────────────────────────
VALOR TOTAL: {{VALOR_INVESTIMENTO}}

═══════════════════════════════════════════════════════════════
                    RETORNO DO INVESTIMENTO
═══════════════════════════════════════════════════════════════

📈 ECONOMIA ESTIMADA
────────────────────────────────────────────────────────────────
Economia Mensal: {{ECONOMIA_MENSAL}}
Economia Anual: {{ECONOMIA_ANUAL}}
Economia em 25 Anos: {{ECONOMIA_25_ANOS}}

💎 INDICADORES FINANCEIROS
────────────────────────────────────────────────────────────────
Payback (Retorno): {{PAYBACK}}
ROI em 25 Anos: {{ROI_25_ANOS}}

═══════════════════════════════════════════════════════════════
                    INFORMAÇÕES DA EMPRESA
═══════════════════════════════════════════════════════════════

{{NOME_EMPRESA}}
CNPJ: {{CNPJ_EMPRESA}}
Telefone: {{TELEFONE_EMPRESA}}
E-mail: {{EMAIL_EMPRESA}}
Site: {{SITE_EMPRESA}}

═══════════════════════════════════════════════════════════════

---

## 📋 PASSOS PARA CRIAR O TEMPLATE:

1. Abra o Microsoft Word
2. Cole o texto acima (ou crie seu próprio design)
3. Formate como desejar:
   - Adicione cores
   - Insira logo da empresa
   - Use tabelas para organizar dados
   - Adicione imagens
   - Use estilos de título, negrito, etc.
4. Salve o arquivo como: `proposta_solar_modelo.docx`
5. Coloque o arquivo na pasta: `app/energia_solar/templates_word/`

## ✅ IMPORTANTE:
- Mantenha os placeholders EXATAMENTE como estão: `{{NOME_CLIENTE}}`, `{{VALOR_INVESTIMENTO}}`, etc.
- Os placeholders devem ter chaves duplas `{{ }}` e letras MAIÚSCULAS
- Não quebre os placeholders em múltiplas linhas
- Você pode adicionar textos, imagens e formatação livremente

## 🎨 DICAS DE FORMATAÇÃO:
- Use **Título 1** para seções principais
- Use **Título 2** para sub-seções
- Adicione cores da empresa (JSP: Azul #003366 e Amarelo #ffcc00)
- Insira o logo da empresa no cabeçalho
- Use tabelas para organizar valores
- Adicione bordas e sombreamento para destacar informações importantes

---

Após criar o template, clique em "Proposta Comercial (Word/PDF)" no dashboard do projeto!
