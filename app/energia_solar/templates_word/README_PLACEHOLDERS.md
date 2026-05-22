# 📝 README - Sistema de Propostas Word

## 🎯 Visão Geral

Este sistema permite gerar propostas comerciais personalizadas a partir de modelos Word (.docx). O sistema:
1. Carrega um template Word com placeholders
2. Substitui os placeholders com dados reais do projeto solar
3. Gera um documento DOCX preenchido
4. (Opcional) Converte para PDF usando LibreOffice

## 📂 Estrutura de Arquivos

```
app/energia_solar/
├── templates_word/               # Pasta para modelos Word
│   └── proposta_solar_modelo.docx   # Template principal (criar manualmente)
├── documentos_gerados/           # Pasta onde são salvos os documentos gerados
│   ├── proposta_projeto_123_20250522_142530.docx
│   └── proposta_projeto_123_20250522_142530.pdf
├── proposta_word_service.py      # Serviço de manipulação Word
└── energia_solar_routes.py       # Rota projeto_proposta_word_pdf()
```

## 🏷️ Placeholders Disponíveis

Use estes placeholders no seu template Word. Eles serão automaticamente substituídos pelos dados do projeto.

### 👤 Dados do Cliente
| Placeholder | Descrição | Exemplo |
|------------|-----------|---------|
| `{{NOME_CLIENTE}}` | Nome ou razão social do cliente | João Silva Ltda |
| `{{CPF_CNPJ_CLIENTE}}` | CPF ou CNPJ do cliente | 12.345.678/0001-90 |
| `{{CIDADE}}` | Cidade do cliente ou projeto | Sorocaba |
| `{{ESTADO}}` | Estado (UF) | SP |
| `{{ENDERECO_CLIENTE}}` | Endereço completo | Rua das Flores, 123 |

### 📋 Dados do Projeto
| Placeholder | Descrição | Exemplo |
|------------|-----------|---------|
| `{{NUMERO_PROJETO}}` | ID/Número do projeto | 456 |
| `{{DATA_PROPOSTA}}` | Data de emissão da proposta | 22/05/2025 |
| `{{VALIDADE_PROPOSTA}}` | Data de validade (30 dias) | 21/06/2025 |

### ⚡ Dados Técnicos
| Placeholder | Descrição | Exemplo |
|------------|-----------|---------|
| `{{POTENCIA_SISTEMA}}` | Potência total do sistema | 10,50 kWp |
| `{{QTD_MODULOS}}` | Quantidade de módulos/placas | 26 |
| `{{POTENCIA_MODULO}}` | Potência de cada módulo | 550W |
| `{{MODELO_MODULO}}` | Modelo do módulo solar | JKM550M-7RL4-V |
| `{{FABRICANTE_MODULO}}` | Fabricante do módulo | JinkoSolar |
| `{{MODELO_INVERSOR}}` | Modelo do inversor | SG10RT |
| `{{FABRICANTE_INVERSOR}}` | Fabricante do inversor | Sungrow |
| `{{POTENCIA_INVERSOR}}` | Potência do inversor | 10000W |

### 📊 Geração e Consumo
| Placeholder | Descrição | Exemplo |
|------------|-----------|---------|
| `{{GERACAO_MENSAL}}` | Geração média mensal | 1.350 kWh/mês |
| `{{GERACAO_ANUAL}}` | Geração anual total | 16.200 kWh/ano |
| `{{CONSUMO_MENSAL}}` | Consumo médio mensal | 1.200 kWh/mês |
| `{{CONSUMO_ANUAL}}` | Consumo anual | 14.400 kWh/ano |
| `{{AREA_NECESSARIA}}` | Área de telhado necessária | 65,00 m² |
| `{{IRRADIACAO_SOLAR}}` | Irradiação solar média | 5,20 kWh/m².dia |

### 💰 Valores Financeiros
| Placeholder | Descrição | Exemplo |
|------------|-----------|---------|
| `{{VALOR_INVESTIMENTO}}` | Valor total do investimento | R$ 28.497,50 |
| `{{ECONOMIA_MENSAL}}` | Economia mensal estimada | R$ 1.248,00 |
| `{{ECONOMIA_ANUAL}}` | Economia anual estimada | R$ 14.976,00 |
| `{{ECONOMIA_25_ANOS}}` | Economia em 25 anos (com inflação) | R$ 528.000,00 |
| `{{PAYBACK}}` | Tempo de retorno do investimento | 1,9 anos |
| `{{ROI_25_ANOS}}` | ROI em 25 anos (%) | 1.753% |

### 💵 Custos Detalhados
| Placeholder | Descrição | Exemplo |
|------------|-----------|---------|
| `{{CUSTO_EQUIPAMENTOS}}` | Custo dos equipamentos | R$ 18.523,38 |
| `{{CUSTO_INSTALACAO}}` | Custo da instalação | R$ 7.124,38 |
| `{{CUSTO_PROJETO}}` | Custo do projeto | R$ 2.849,75 |

### 🏢 Dados da Empresa
| Placeholder | Descrição | Exemplo |
|------------|-----------|---------|
| `{{NOME_EMPRESA}}` | Nome da empresa | JSP Elétrica & Solar |
| `{{CNPJ_EMPRESA}}` | CNPJ da empresa | 12.345.678/0001-90 |
| `{{TELEFONE_EMPRESA}}` | Telefone da empresa | (15) 99670-2036 |
| `{{EMAIL_EMPRESA}}` | E-mail da empresa | atendimento@eletricasaroba.com.br |
| `{{SITE_EMPRESA}}` | Site da empresa | www.exemplo.com.br |

## 🔧 Como Criar o Template Word

1. **Crie um documento Word** em `app/energia_solar/templates_word/proposta_solar_modelo.docx`

2. **Digite os placeholders** exatamente como mostrado acima, com chaves duplas:
   ```
   Cliente: {{NOME_CLIENTE}}
   Cidade: {{CIDADE}} - {{ESTADO}}
   Valor do Investimento: {{VALOR_INVESTIMENTO}}
   ```

3. **Use formatação Word normal**: negrito, cores, tabelas, imagens, etc.

4. **Exemplo de tabela**:
   ```
   | Item             | Valor                      |
   |------------------|----------------------------|
   | Equipamentos     | {{CUSTO_EQUIPAMENTOS}}     |
   | Instalação       | {{CUSTO_INSTALACAO}}       |
   | Projeto          | {{CUSTO_PROJETO}}          |
   | **Total**        | **{{VALOR_INVESTIMENTO}}** |
   ```

## 🚀 Como Usar

1. **No Dashboard do Projeto**, clique em "Ferramentas"
2. Selecione **"Proposta Comercial (Word/PDF)"**
3. O sistema irá:
   - Carregar o template
   - Preencher todos os placeholders
   - Salvar DOCX em `documentos_gerados/`
   - Tentar converter para PDF (se LibreOffice estiver instalado)
   - Baixar o arquivo automaticamente

## ⚙️ Conversão para PDF (Opcional)

### 📥 Instalar LibreOffice

**Windows:**
```powershell
# Baixar do site oficial
# https://www.libreoffice.org/download/download/
# Adicionar ao PATH: C:\Program Files\LibreOffice\program
```

**Linux (Render/Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install -y libreoffice
```

### 🔍 Verificar Instalação
```bash
libreoffice --version
```

Se LibreOffice não estiver disponível, o sistema retorna um arquivo **DOCX** ao invés de PDF.

## 🎨 Dicas de Formatação

### ✅ Boas Práticas
- Use **estilos Word** (Título 1, Título 2, etc.) para estrutura consistente
- Insira **imagens** do logo diretamente no template
- Use **tabelas** para organizar dados técnicos
- Aplique **cores corporativas** com ferramentas de formatação Word
- Adicione **quebras de página** onde necessário

### ❌ Evite
- Não quebre placeholders em múltiplas linhas
- Não use formatação condicional complexa (use Word, não fórmulas)
- Não edite o nome dos placeholders

## 🐛 Troubleshooting

### ❗ "Template Word não encontrado"
**Causa:** Arquivo `proposta_solar_modelo.docx` não existe  
**Solução:** Crie o template em `app/energia_solar/templates_word/`

### ❗ "LibreOffice não disponível"
**Causa:** LibreOffice não está instalado ou não está no PATH  
**Solução:** Instale LibreOffice ou use o arquivo DOCX gerado

### ❗ "Placeholders não foram substituídos"
**Causa:** Nome do placeholder digitado incorretamente no template  
**Solução:** Verifique se os placeholders estão exatamente como na tabela acima (com chaves duplas e letras maiúsculas)

## 📚 Referências

- **Python-docx**: https://python-docx.readthedocs.io/
- **LibreOffice**: https://www.libreoffice.org/
- **Flask send_file**: https://flask.palletsprojects.com/en/2.3.x/api/#flask.send_file
