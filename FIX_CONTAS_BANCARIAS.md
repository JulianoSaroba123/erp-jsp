# 🏦 SOLUÇÃO: Contas Bancárias Não Aparecem no Lançamento

## ❌ Problema
Ao criar um novo lançamento financeiro, o campo "CONTA BANCÁRIA" mostra "Nenhuma" mesmo tendo configurado contas em "Configurações".

## ✅ Solução

### Passo 1: Executar o Script no Render

Acesse o **Shell** do Render e execute:

```bash
python criar_contas_render.py
```

Este script irá:
- ✅ Verificar contas existentes
- ✅ Criar 5 contas bancárias padrão
- ✅ Não duplicar contas já existentes

### Passo 2: Verificar Contas Criadas

Após executar o script, você terá as seguintes contas:

1. **Banco do Brasil - Conta Corrente** (Principal)
   - Saldo inicial: R$ 10.000,00
   - Limite: R$ 5.000,00

2. **Itaú - Cartão Corporativo**
   - Saldo inicial: R$ 0,00
   - Limite: R$ 10.000,00

3. **Caixa Geral**
   - Saldo inicial: R$ 500,00
   - Para pequenas despesas

4. **Banco do Brasil - Salários**
   - Conta exclusiva para folha de pagamento

5. **Santander Empresarial**
   - Conta secundária com saldo de R$ 5.000,00

### Passo 3: Testar

1. Acesse: `/financeiro/lancamentos/novo`
2. O campo **CONTA BANCÁRIA** agora deve listar todas as contas
3. Selecione a conta desejada ao criar o lançamento

---

## 📋 Local (SQLite)

Se estiver testando localmente, execute:

```bash
python criar_contas_bancarias.py
```

---

## 🔧 Personalizar Contas

Para adicionar suas próprias contas bancárias:

1. **Via Interface (em breve)**
   - Acesse: `/configuracoes/contas-bancarias`
   - Clique em "Nova Conta"

2. **Via Script Python**
   - Edite `criar_contas_render.py`
   - Adicione nova conta no array `contas_padrao`
   - Execute o script novamente

### Exemplo de Nova Conta:

```python
{
    'nome': 'Nubank Empresarial',
    'tipo': 'conta_corrente',
    'banco': 'Nubank',
    'agencia': None,
    'numero_conta': '1234567-8',
    'saldo_inicial': Decimal('3000.00'),
    'saldo_atual': Decimal('3000.00'),
    'limite_credito': Decimal('2000.00'),
    'ativa': True,
    'ativo': True,
    'principal': False,
    'observacoes': 'Conta digital corporativa'
}
```

---

## ✅ Verificação

Para confirmar que as contas foram criadas:

```python
from app.app import app
from app.financeiro.financeiro_model import ContaBancaria

with app.app_context():
    contas = ContaBancaria.query.filter_by(ativo=True, ativa=True).all()
    for c in contas:
        print(f"{c.nome} - Saldo: {c.saldo_formatado}")
```

---

## 🎯 Resultado Esperado

Após seguir os passos acima, ao criar um novo lançamento financeiro:

- ✅ Campo "CONTA BANCÁRIA" mostra dropdown com as contas
- ✅ Cada conta exibe: Nome - Banco - Saldo
- ✅ Você pode selecionar a conta apropriada
- ✅ O lançamento fica vinculado à conta

---

## 📝 Observações

- As contas são criadas com os campos `ativo=True` e `ativa=True`
- Apenas contas ativas aparecem no formulário
- A conta marcada como `principal=True` pode ser pré-selecionada
- O saldo é atualizado automaticamente ao pagar/receber lançamentos

---

**Status:** ✅ Resolvido  
**Data:** 05/02/2026  
**Versão:** ERP JSP v3.0
