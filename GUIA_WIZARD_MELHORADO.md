# 🎯 Guia Rápido: Wizard de Projetos Solares - Melhorias

## ✅ O QUE FOI CORRIGIDO

### 1️⃣ Campos Duplicados Resolvidos
**Antes**: Dois campos `tarifa_kwh` causavam conflito  
**Agora**: Cada método tem seu próprio campo, consolidado automaticamente no envio

### 2️⃣ Painéis Dinâmicos
**Antes**: Todos os 3 painéis apareciam ao mesmo tempo  
**Agora**: Apenas 1 painel visível por vez, conforme método escolhido

### 3️⃣ Cálculos Automáticos
**Antes**: Usuário tinha que calcular consumo manualmente  
**Agora**: Sistema calcula automaticamente em tempo real

---

## 🚀 COMO USAR

### Método 1: kWh Direto (Mais Comum)
```
1. Selecione "kWh Direto"
2. Digite o consumo mensal: 450 kWh
3. Pronto! ✅
```

### Método 2: Histórico 12 Meses
```
1. Selecione "Histórico 12 Meses"
2. Preencha os meses que tiver (não precisa dos 12):
   - Janeiro: 450
   - Fevereiro: 480
   - Março: 420
3. Média calculada automaticamente: 450 kWh ✅
```

### Método 3: Valor da Conta
```
1. Selecione "Valor da Conta (R$)"
2. Digite o valor da conta: R$ 382,50
3. Tarifa já vem preenchida: R$ 0,85/kWh
4. Consumo calculado automaticamente: 450 kWh ✅
```

---

## 🧪 TESTE AGORA

### ✅ Teste Rápido (2 minutos)

1. **Abra o wizard**: http://localhost:5001/energia-solar/projetos/novo

2. **Vá para Aba 2** (Consumo)

3. **Teste cada método**:
   - Clique em "kWh Direto" → veja painel aparecer
   - Clique em "Histórico 12 Meses" → veja painel trocar
   - Clique em "Valor da Conta" → veja painel trocar novamente

4. **Teste o cálculo automático**:
   - Selecione "Valor da Conta"
   - Digite: **382.50** no campo "Valor da Conta"
   - Veja aparecer: **"Consumo Calculado: 450 kWh/mês"**

5. **✅ FUNCIONOU!**

---

## 🎨 O QUE VOCÊ VAI VER

### Painel kWh Direto
```
┌─────────────────────────────────────────┐
│ Consumo Mensal (kWh) *                  │
│ [ 450                  ]                │
│                                         │
│ Tarifa (R$/kWh)                         │
│ [ 0.85                 ]                │
└─────────────────────────────────────────┘
```

### Painel Histórico 12 Meses
```
┌─────────────────────────────────────────┐
│ Janeiro    Fevereiro    Março           │
│ [ 450 ]    [ 480 ]      [ 420 ]         │
│                                         │
│ Abril      Maio         Junho           │
│ [     ]    [     ]      [     ]         │
│                                         │
│ Média Mensal: 450 kWh                   │
└─────────────────────────────────────────┘
```

### Painel Valor da Conta
```
┌─────────────────────────────────────────┐
│ Valor da Conta (R$) *                   │
│ [ 382.50               ]                │
│                                         │
│ Tarifa (R$/kWh)                         │
│ [ 0.85                 ]                │
│                                         │
│ Consumo Calculado: 450 kWh/mês ✅       │
└─────────────────────────────────────────┘
```

---

## ⚡ RECURSOS ATIVOS

### ✅ Validação Inteligente
- Apenas campos visíveis são obrigatórios
- Troca automática ao mudar de método
- Mensagens claras de erro

### ✅ Cálculos em Tempo Real
- Digite → veja resultado instantâneo
- Média histórico atualiza conforme digita
- Consumo por valor da conta atualiza instantaneamente

### ✅ Auto-Save
- Rascunho salvo a cada 30 segundos
- Recupera dados se fechar página
- Indicador visual quando salva

---

## 🐛 PROBLEMAS RESOLVIDOS

| ❌ Antes | ✅ Agora |
|----------|----------|
| Campos duplicados causavam erro | Campos únicos, consolidados no envio |
| Usuário via 3 painéis ao mesmo tempo | Apenas 1 painel por vez |
| Tinha que calcular consumo manualmente | Cálculo automático em tempo real |
| Validação quebrava ao trocar método | Validação dinâmica por método ativo |
| Histórico 12m não calculava média | Média automática enquanto digita |

---

## 📚 PRÓXIMOS PASSOS

Depois de testar, você pode:

1. **Criar um projeto completo** usando qualquer método
2. **Editar um projeto existente** (tabs liberados)
3. **Ver a proposta** gerada com todos os cálculos

---

## 💡 DICAS

### Dica 1: Qual método usar?
- **kWh Direto**: Quando o cliente sabe o consumo exato
- **Histórico 12m**: Para análise de variação sazonal
- **Valor da Conta**: Quando cliente só tem a conta em mãos

### Dica 2: Tarifa Média por Estado
A tarifa R$ 0,85/kWh é uma média nacional.  
Em breve: auto-preenchimento por estado! 🎯

### Dica 3: Console do Navegador
Aperte **F12** → aba **Console** para ver logs em tempo real:
```
📊 Método de cálculo alterado: valor_conta
💡 Consumo calculado: R$ 382.5 ÷ R$ 0.85/kWh = 450 kWh
✅ Formulário validado! Enviando...
```

---

## 🆘 AJUDA

### Não está calculando?
1. Abra F12 → Console
2. Procure por erros em vermelho
3. Recarregue a página com Ctrl+F5

### Painel não troca?
1. Feche o navegador completamente
2. Abra novamente
3. Limpe cache: Ctrl+Shift+Delete

### Servidor não inicia?
```powershell
taskkill /F /IM python.exe
python run.py
```

---

**📅 Atualizado em**: 03/01/2026  
**🚀 Versão**: 3.0 - Wizard Melhorado  
**👨‍💻 Dev**: GitHub Copilot + Juliano Saroba
