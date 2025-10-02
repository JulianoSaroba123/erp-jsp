# 🎯 Campo Markup com Cálculo Automático - Guia de Uso

## 📋 Funcionalidades Implementadas

### 📊 **Campo Markup**
- **Localização**: Formulário de cadastro/edição de produtos
- **Tipo**: Campo numérico com símbolo % 
- **Funcionalidade**: Cálculo automático do preço de venda

### 🧮 **Cálculos Automáticos**

#### **1. Cálculo do Preço (Custo + Markup → Preço)**
```
Preço = Custo × (1 + Markup ÷ 100)
Exemplo: R$ 100,00 × (1 + 25 ÷ 100) = R$ 125,00
```

#### **2. Cálculo do Markup (Custo + Preço → Markup)**  
```
Markup = ((Preço ÷ Custo) - 1) × 100
Exemplo: ((R$ 125,00 ÷ R$ 100,00) - 1) × 100 = 25%
```

### ⚡ **Funcionalidades da Interface**

#### **🎨 Interações Automáticas**
- ✅ **Custo + Markup** → Calcula Preço automaticamente
- ✅ **Custo + Preço** → Calcula Markup automaticamente  
- ✅ **Feedback visual** com destaque verde nos campos calculados
- ✅ **Validações** para valores negativos
- ✅ **Formatação** automática com 2 casas decimais

#### **🛡️ Validações Implementadas**
- ✅ Custo não pode ser negativo
- ✅ Markup não pode ser negativo
- ✅ Preço não pode ser negativo
- ✅ Alerta quando preço < custo
- ✅ Confirmação para preços com margem negativa

### 📊 **Exibição na Listagem**
- ✅ Nova coluna "Markup (%)" na tabela de produtos
- ✅ Formatação: "25.0%" 
- ✅ Produtos existentes atualizados com markup calculado

### 🔧 **Métodos do Modelo**

```python
# Cálculos disponíveis no modelo Produto
produto.calcular_preco_venda()          # Retorna preço baseado em custo + markup
produto.atualizar_preco_por_markup()    # Atualiza o campo preco automaticamente
produto.calcular_markup_por_preco()     # Retorna markup baseado em custo + preço
```

## 📊 **Produtos de Teste Atualizados**

| Produto | Custo | Preço | Markup |
|---------|-------|--------|---------|
| Notebook Gamer RGB | R$ 2.000,00 | R$ 2.500,00 | 25.0% |
| Mouse Wireless Pro | R$ 100,00 | R$ 150,00 | 50.0% |
| Teclado Mecânico LED | R$ 220,00 | R$ 300,00 | 36.4% |
| Monitor Ultrawide 34" | R$ 900,00 | R$ 1.200,00 | 33.3% |
| Headset Gamer 7.1 | R$ 180,00 | R$ 250,00 | 38.9% |

## 🚀 **Como Usar**

### **Cenário 1: Definir Markup e Calcular Preço**
1. Digite o **Custo** do produto
2. Digite o **Markup** desejado (ex: 25 para 25%)
3. O **Preço** será calculado automaticamente

### **Cenário 2: Definir Preço e Calcular Markup**
1. Digite o **Custo** do produto  
2. Digite o **Preço** de venda desejado
3. O **Markup** será calculado automaticamente

### **Cenário 3: Ajuste de Valores**
- Qualquer alteração em **Custo** ou **Markup** recalcula o **Preço**
- Qualquer alteração em **Preço** (quando não focado em Markup) recalcula o **Markup**

## ✅ **Status de Implementação**
- ✅ Modelo atualizado com campo markup
- ✅ Banco de dados atualizado (coluna adicionada)
- ✅ Interface com campo markup e validações
- ✅ JavaScript para cálculos automáticos
- ✅ Listagem com coluna markup
- ✅ Produtos existentes atualizados
- ✅ Testes de funcionalidade validados

---
**Implementado com Flask + SQLAlchemy + JavaScript** 🎉