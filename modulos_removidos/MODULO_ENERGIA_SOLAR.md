# 🌞 Módulo de Cálculo de Energia Solar

## ✨ Funcionalidades

O módulo de Energia Solar permite calcular sistemas fotovoltaicos completos, incluindo:

- **Dimensionamento automático** do sistema (kWp)
- **Cálculo de número de painéis** necessários
- **Estimativa de geração** mensal e anual
- **Análise de economia** e retorno financeiro
- **Payback e ROI** em 25 anos
- **Especificação de inversores** (String, Micro, Híbrido)
- **Cálculo de área necessária**
- **Irradiação solar por estado** (automático)

## 📊 Como Usar

### 1. Acessar o Módulo
- Menu lateral: **Energia Solar** → Dashboard
- Ou acesse diretamente: `/energia-solar`

### 2. Fazer um Cálculo
1. Clique em **"Nova Calculadora"**
2. Preencha os dados:
   - **Cliente**: Selecione ou digite o nome
   - **Consumo mensal** (kWh): Veja na conta de energia
   - **Tarifa** (R$/kWh): Valor sem impostos (~R$ 0,85)
   - **Estado**: Seleciona automaticamente a irradiação solar
   - **Tipo de instalação**: Telhado, Solo, Carport, etc.
   - **Orientação**: Norte (ideal), Leste, Oeste, etc.
3. Clique em **"Calcular Sistema"**

### 3. Visualizar Resultados
O sistema calcula automaticamente:
- ✅ **Potência do sistema** em kWp
- ✅ **Número de painéis** (painéis de 550W)
- ✅ **Número de inversores** necessários
- ✅ **Área necessária** em m²
- ✅ **Geração mensal** estimada
- ✅ **Economia mensal e anual**
- ✅ **Investimento total** (R$ 4,50/Wp)
- ✅ **Payback** (anos para retorno)
- ✅ **ROI em 25 anos** (%)

### 4. Gerenciar Cálculos
- **Dashboard**: Visualiza últimos cálculos e estatísticas
- **Listar**: Lista todos os cálculos com paginação
- **Visualizar**: Detalhes completos do sistema
- **Imprimir**: Gera relatório para apresentar ao cliente
- **Excluir**: Remove cálculos antigos

## 🔧 Parâmetros Técnicos

### Painéis
- **Potência**: 550W (padrão moderno)
- **Área por painel**: 2m²
- **Eficiência**: 80% (considera perdas)

### Inversores
- **Tipo padrão**: String Inversor
- **Dimensionamento**: 1 inversor para cada 10kWp
- **Potência**: Proporcional ao sistema

### Custos
- **Custo por Wp**: R$ 4,50 (média nacional)
- **Inclui**: Painéis, inversores, estrutura, instalação

### Irradiação Solar (kWh/m²/dia)
Estados com **maior** irradiação:
- RN: 5.9 | PE: 5.8 | CE: 5.7 | PB: 5.6 | BA: 5.5

Estados com **menor** irradiação:
- AM: 4.3 | RS: 4.4 | SC: 4.5 | AC: 4.5 | PR: 4.7

## 📈 Exemplos de Cálculo

### Exemplo 1: Residência Pequena
- **Consumo**: 250 kWh/mês
- **Tarifa**: R$ 0,85/kWh
- **Estado**: SP (4.6 kWh/m²/dia)

**Resultado**:
- Sistema: ~2.5 kWp
- Painéis: 5 unidades
- Área: 10 m²
- Economia: R$ 212/mês
- Investimento: ~R$ 11.250
- Payback: ~4.4 anos

### Exemplo 2: Residência Média
- **Consumo**: 500 kWh/mês
- **Tarifa**: R$ 0,85/kWh
- **Estado**: MG (5.0 kWh/m²/dia)

**Resultado**:
- Sistema: ~4.5 kWp
- Painéis: 9 unidades
- Área: 18 m²
- Economia: R$ 425/mês
- Investimento: ~R$ 20.250
- Payback: ~4.0 anos

### Exemplo 3: Empresa
- **Consumo**: 2000 kWh/mês
- **Tarifa**: R$ 0,85/kWh
- **Estado**: CE (5.7 kWh/m²/dia)

**Resultado**:
- Sistema: ~16 kWp
- Painéis: 30 unidades
- Área: 60 m²
- Economia: R$ 1.700/mês
- Investimento: ~R$ 72.000
- Payback: ~3.5 anos

## 💡 Dicas

1. **Consumo real**: Use a média de 12 meses para maior precisão
2. **Tarifa**: Considere apenas energia (sem impostos/taxas)
3. **Orientação**: Norte é ideal no hemisfério sul
4. **Inclinação**: Idealmente igual à latitude local
5. **Sombreamento**: Reduza 10-20% se houver árvores/prédios
6. **Espaço**: Verifique se há área suficiente no telhado

## 🗄️ Banco de Dados

### Tabela: `calculo_energia_solar`
Armazena todos os cálculos realizados com:
- Dados do cliente e localização
- Parâmetros de consumo e tarifa
- Sistema dimensionado (painéis, inversores)
- Estimativas de geração e economia
- Análise financeira (custo, payback, ROI)
- Detalhes da instalação

## 🚀 Instalação

Execute o script para criar a tabela:
```bash
python criar_tabela_energia_solar.py
```

O módulo já está integrado ao sistema e aparece na sidebar!

## 📞 Integração com Propostas

Futuramente, os cálculos poderão ser:
- Convertidos em propostas comerciais
- Vinculados a clientes existentes
- Exportados para PDF
- Enviados por email

---

**Desenvolvido para ERP JSP v3.0** 🚀
