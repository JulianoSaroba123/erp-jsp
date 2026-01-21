# 💳 PARCELAMENTO EM PROPOSTAS - GUIA COMPLETO

## 📋 Visão Geral

Sistema de parcelamento automático para propostas comerciais. Quando você seleciona **"Parcelado"** como forma de pagamento, o sistema permite configurar:

- ✅ Número de parcelas (1 a 120)
- ✅ Entrada (percentual do valor total)
- ✅ Intervalo entre parcelas (em dias)
- ✅ Data de vencimento da primeira parcela
- ✅ Preview visual das parcelas antes de salvar

---

## 🎯 Como Usar

### 1️⃣ Criar Nova Proposta com Parcelamento

1. **Menu**: Propostas > Nova Proposta

2. **Preencha os dados básicos**:
   - Cliente
   - Título
   - Descrição
   - Produtos/Serviços

3. **Seção "Formas de Pagamento"**:
   - Selecione: **Parcelado**
   - Os campos de parcelamento aparecem automaticamente!

4. **Configure o Parcelamento**:
   
   **Entrada (%)**:
   - Ex: `20` = 20% de entrada
   - O restante será dividido nas parcelas
   
   **Número de Parcelas**:
   - Ex: `12` = 12 vezes
   - Máximo: 120 parcelas
   
   **Intervalo (dias)**:
   - Ex: `30` = parcelas mensais
   - Ex: `15` = parcelas quinzenais
   - Ex: `60` = parcelas bimestrais
   
   **1ª Parcela**:
   - Escolha a data de vencimento da primeira parcela
   - As demais serão calculadas automaticamente

5. **Preview das Parcelas**:
   - Clique em **"👁️ Visualizar Parcelas"**
   - Veja a tabela com todas as parcelas
   - Confira datas e valores

6. **Salvar**:
   - Clique em **"Salvar Proposta"**
   - As parcelas serão geradas automaticamente no banco de dados!

---

## 📊 Exemplo Prático

### Cenário Real

**Proposta**: Sistema de Energia Solar  
**Valor Total**: R$ 25.000,00  
**Forma de Pagamento**: Parcelado

**Configuração**:
- **Entrada**: 20% (R$ 5.000,00)
- **Parcelas**: 3x
- **Intervalo**: 30 dias
- **1ª Parcela**: 21/02/2026

**Resultado Gerado**:

| Parcela | Vencimento | Valor |
|---------|------------|-------|
| **Entrada** | 21/02/2026 | **R$ 5.000,00** |
| Parcela 1/3 | 23/03/2026 | R$ 6.666,67 |
| Parcela 2/3 | 22/04/2026 | R$ 6.666,67 |
| Parcela 3/3 | 22/05/2026 | R$ 6.666,66 |
| **TOTAL** | - | **R$ 25.000,00** |

> **Nota**: A última parcela é ajustada para fechar exatamente no valor total.

---

## 🔧 Campos Técnicos

### Tabela: `propostas`

Novos campos adicionados:

```sql
numero_parcelas         INTEGER DEFAULT 1
intervalo_parcelas      INTEGER DEFAULT 30
data_primeira_parcela   DATE
```

### Tabela: `parcelas_proposta`

Nova tabela criada:

```sql
id                      INTEGER PRIMARY KEY
proposta_id             INTEGER (FK -> propostas.id)
numero_parcela          INTEGER (0 = entrada, 1-120 = parcelas)
valor_parcela           NUMERIC(10, 2)
data_vencimento         DATE
status                  VARCHAR(20) [pendente, pago, cancelado]
data_pagamento          DATE
descricao               VARCHAR(200)
ativo                   BOOLEAN
data_criacao            TIMESTAMP
```

---

## 💻 Código Backend

### Método `gerar_parcelas()`

Localizado em: `app/proposta/proposta_model.py`

```python
def gerar_parcelas(self):
    """
    Gera parcelas automaticamente baseado em:
    - numero_parcelas
    - entrada (%)
    - data_primeira_parcela
    - intervalo_parcelas
    - valor_total
    """
```

**Lógica**:

1. Calcula valor da entrada (percentual do total)
2. Calcula valor restante
3. Divide valor restante pelo número de parcelas
4. Cria parcela de entrada (se houver)
5. Cria parcelas restantes com intervalos
6. Ajusta última parcela para fechar centavos

---

## 🎨 Interface do Usuário

### JavaScript - Interatividade

Localizado em: `app/proposta/templates/proposta/form.html`

**Funcionalidades**:

1. **Toggle Campos**:
   - Mostra/oculta campos quando muda forma de pagamento
   
2. **Preview Dinâmico**:
   - Calcula parcelas em tempo real
   - Exibe tabela formatada
   - Mostra resumo do parcelamento

3. **Formatação**:
   - Datas no formato brasileiro (dd/mm/aaaa)
   - Valores monetários (R$ x.xxx,xx)

---

## 📝 Fluxo de Dados

### Criação de Proposta

```
1. Usuário preenche formulário
   ↓
2. Seleciona "Parcelado"
   ↓
3. Configura parcelamento (parcelas, entrada, etc)
   ↓
4. Visualiza preview
   ↓
5. Salva proposta
   ↓
6. Backend:
   - Salva dados da proposta
   - Calcula totais
   - Chama proposta.gerar_parcelas()
   - Cria registros em parcelas_proposta
   ↓
7. Parcelas salvas no banco!
```

### Edição de Proposta

```
1. Usuário edita proposta
   ↓
2. Muda configuração de parcelamento
   ↓
3. Salva
   ↓
4. Backend:
   - Remove parcelas antigas
   - Recalcula totais
   - Gera novas parcelas
   ↓
5. Parcelas atualizadas!
```

---

## 🔍 Validações

### Frontend (JavaScript)

- ✅ Número de parcelas: 1 a 120
- ✅ Intervalo: 1 a 365 dias
- ✅ Data primeira parcela: obrigatória se parcelado

### Backend (Python)

- ✅ Percentual entrada: 0 a 100%
- ✅ Valor total deve estar preenchido
- ✅ Soma das parcelas = valor total (ajuste automático)

---

## 🚀 Melhorias Futuras (Roadmap)

### Curto Prazo
- [ ] Adicionar juros por parcela
- [ ] Permitir valores personalizados por parcela
- [ ] Exportar tabela de parcelas para PDF/Excel

### Médio Prazo
- [ ] Integração com lançamentos financeiros
- [ ] Gerar boletos automaticamente
- [ ] Envio de lembrete de vencimento

### Longo Prazo
- [ ] Controle de recebimentos
- [ ] Baixa automática de parcelas
- [ ] Relatório de inadimplência

---

## 🐛 Troubleshooting

### Problema: Campos de parcelamento não aparecem

**Solução**: Certifique-se de selecionar "Parcelado" na forma de pagamento.

### Problema: Preview não mostra parcelas

**Solução**: 
1. Verifique se preencheu o valor total
2. Informe a data da primeira parcela
3. Confira o número de parcelas (deve ser > 0)

### Problema: Erro ao salvar parcelas

**Solução**:
1. Verifique se executou o script de migração:
   ```bash
   python scripts/adicionar_campos_parcelamento_proposta.py
   ```
2. Confirme que as colunas existem no banco

### Problema: Soma das parcelas diferente do total

**Solução**: Isso é normal! A última parcela é ajustada automaticamente para fechar os centavos.

---

## 📚 Arquivos Modificados

### Backend
- ✅ `app/proposta/proposta_model.py` - Modelo e lógica
- ✅ `app/proposta/proposta_routes.py` - Rotas de salvamento

### Frontend
- ✅ `app/proposta/templates/proposta/form.html` - Formulário HTML + JavaScript

### Scripts
- ✅ `scripts/adicionar_campos_parcelamento_proposta.py` - Migração de banco

### Documentação
- ✅ `PARCELAMENTO_PROPOSTAS.md` - Este arquivo

---

## 🎓 Exemplos de Uso

### Exemplo 1: Parcelamento Simples (sem entrada)

```
Valor Total: R$ 10.000,00
Entrada: 0%
Parcelas: 10x
Intervalo: 30 dias
1ª Parcela: 01/02/2026

Resultado:
- 10 parcelas de R$ 1.000,00
- Vencimentos: 01/02, 03/03, 02/04, ...
```

### Exemplo 2: Parcelamento com Entrada

```
Valor Total: R$ 15.000,00
Entrada: 30%
Parcelas: 6x
Intervalo: 30 dias
1ª Parcela: 15/02/2026

Resultado:
- Entrada: R$ 4.500,00 (15/02/2026)
- 6 parcelas de R$ 1.750,00
- Vencimentos: 17/03, 16/04, 16/05, ...
```

### Exemplo 3: Parcelamento Quinzenal

```
Valor Total: R$ 5.000,00
Entrada: 10%
Parcelas: 8x
Intervalo: 15 dias
1ª Parcela: 05/02/2026

Resultado:
- Entrada: R$ 500,00 (05/02/2026)
- 8 parcelas de R$ 562,50
- Vencimentos: 20/02, 07/03, 22/03, ...
```

---

## 📊 Diagrama de Relacionamentos

```
┌──────────────┐
│  Proposta    │
│──────────────│
│ id           │
│ valor_total  │
│ forma_pag... │◄──────┐
│ numero_parc..│       │
│ intervalo_...│       │
│ data_primeir.│       │
└──────────────┘       │
                       │
                       │ 1:N
                       │
                ┌──────┴──────────────┐
                │ ParcelaProposta     │
                │─────────────────────│
                │ id                  │
                │ proposta_id (FK)    │
                │ numero_parcela      │
                │ valor_parcela       │
                │ data_vencimento     │
                │ status              │
                │ data_pagamento      │
                │ descricao           │
                └─────────────────────┘
```

---

## 🎯 Checklist de Implementação

- [x] Criar modelo `ParcelaProposta`
- [x] Adicionar campos na tabela `propostas`
- [x] Criar tabela `parcelas_proposta`
- [x] Implementar método `gerar_parcelas()`
- [x] Atualizar formulário HTML
- [x] Adicionar JavaScript para preview
- [x] Atualizar rota de criação
- [x] Atualizar rota de edição
- [x] Criar script de migração
- [x] Testar criação de proposta
- [x] Testar edição de proposta
- [x] Documentar funcionalidade
- [ ] Adicionar ao manual do usuário
- [ ] Treinar equipe

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte este documento
2. Verifique o MANUAL_USUARIO.md
3. Entre em contato com a equipe de TI

---

**ERP JSP v3.1.0**  
*Sistema de Parcelamento Automático de Propostas*  
*© 2026 JSP Soluções*

---

📄 **PARCELAMENTO_PROPOSTAS.md** | Versão 1.0 | Janeiro 2026
