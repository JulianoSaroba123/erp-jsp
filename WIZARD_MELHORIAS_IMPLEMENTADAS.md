# ✅ Melhorias Implementadas no Wizard de Projetos Solares

## 📅 Data: 03/01/2026

## 🎯 Objetivo
Corrigir e melhorar o formulário `projeto_wizard.html` para eliminar bugs, adicionar validações dinâmicas e implementar cálculos automáticos.

---

## 🔧 Correções Implementadas

### 1. ✅ Campos com `name` Duplicado
**Problema**: Existiam dois campos com `name="tarifa_kwh"` (um em kWh direto, outro em valor da conta)

**Solução**:
- Renomeado `tarifa_kwh_valor` para `tarifa_kwh_conta`
- Adicionado JavaScript que consolida o valor correto no submit baseado no método ativo
- Campo hidden `tarifa_kwh_final` é criado dinamicamente no momento do envio

**Arquivos modificados**:
- `projeto_wizard.html` linha ~290: Campo renomeado para `tarifa_kwh_conta`
- `projeto_wizard.html` linha ~2150: Lógica de consolidação no submit

---

### 2. ✅ Alternância de Painéis por Método de Cálculo
**Problema**: Os três painéis (kWh direto, histórico 12m, valor da conta) apareciam simultaneamente

**Solução**:
- Implementado evento `change` nos radios `metodo_calculo`
- JavaScript mostra/oculta painéis automaticamente:
  - `kwh_direto` → exibe `painel_kwh_direto`
  - `historico_12m` → exibe `painel_historico`
  - `valor_conta` → exibe `painel_valor_conta`

**Código adicionado**: Função `setupCalculos()` linha ~1425

---

### 3. ✅ Cálculo Automático por Valor da Conta
**Problema**: Campo "Valor da Conta (R$)" não calculava o consumo automaticamente

**Solução**:
- Adicionado evento `input` nos campos `valor_conta_luz` e `tarifa_kwh_conta`
- Fórmula: **Consumo = Valor da Conta ÷ Tarifa**
- Resultado exibido em tempo real em `#consumo_calculado_valor`
- Valor é automaticamente transferido para `consumo_kwh_mes` (campo principal)

**Exemplo**:
- Valor da conta: R$ 382,50
- Tarifa: R$ 0,85/kWh
- **Consumo calculado: 450 kWh/mês**

---

### 4. ✅ Cálculo de Média do Histórico 12 Meses
**Problema**: Campos dos 12 meses não calculavam a média automaticamente

**Solução**:
- Adicionado evento `input` em todos os `.mes-input`
- Função `calcularMediaHistorico()` soma os valores preenchidos e divide pela quantidade
- Resultado exibido em `#media_historico`
- Valor é automaticamente transferido para `consumo_kwh_mes`

**Exemplo**:
- Janeiro: 450, Fevereiro: 480, Março: 420 (demais vazios)
- **Média: (450+480+420) ÷ 3 = 450 kWh**

---

### 5. ✅ Validação Dinâmica de Campos Obrigatórios
**Problema**: Campos `required` fixos causavam erro ao enviar painel oculto

**Solução**:
- JavaScript remove/adiciona `required` dinamicamente conforme o método selecionado:
  - **kWh Direto**: `consumo_kwh_mes` é obrigatório
  - **Histórico 12m**: Nenhum campo individual obrigatório (aceita média parcial)
  - **Valor da Conta**: `valor_conta_luz` é obrigatório

**Comportamento**:
- Ao trocar de método, os `required` são atualizados automaticamente
- Apenas os campos visíveis são validados no submit

---

## 📊 Fluxo de Funcionamento

### Método: kWh Direto (padrão)
1. Usuário preenche `consumo_kwh_mes` diretamente
2. Campo é obrigatório (`required`)
3. Usado para cálculo de potência

### Método: Histórico 12 Meses
1. Usuário preenche consumo de cada mês
2. JavaScript calcula média automaticamente
3. Média é transferida para `consumo_kwh_mes`
4. Não exige todos os 12 meses preenchidos

### Método: Valor da Conta
1. Usuário preenche `valor_conta_luz` (R$)
2. Sistema calcula: **Consumo = Valor ÷ Tarifa**
3. Resultado é transferido para `consumo_kwh_mes`
4. Campo valor da conta é obrigatório

---

## 🔄 Consolidação no Submit

Quando o botão **Finalizar** é clicado:

```javascript
// 1. Detectar método ativo
const metodoSelecionado = document.querySelector('input[name="metodo_calculo"]:checked').value;

// 2. Consolidar tarifa do campo ativo
let tarifaFinal = 0.85; // padrão
if (metodoSelecionado === 'kwh_direto') {
    tarifaFinal = document.getElementById('tarifa_kwh').value;
} else if (metodoSelecionado === 'valor_conta') {
    tarifaFinal = document.getElementById('tarifa_kwh_conta').value;
}

// 3. Criar campo hidden com valor consolidado
<input type="hidden" name="tarifa_kwh_final" value="0.85">
```

---

## 🧪 Testes Recomendados

### Teste 1: Alternância de Painéis
1. Abrir wizard em `/energia-solar/projetos/novo`
2. Ir para Aba 2 (Consumo)
3. Clicar em cada método de cálculo
4. ✅ Verificar que apenas 1 painel aparece por vez

### Teste 2: Cálculo por Valor da Conta
1. Selecionar método "Valor da Conta"
2. Preencher: Valor = R$ 382,50, Tarifa = R$ 0,85
3. ✅ Verificar que aparece "Consumo Calculado: 450 kWh/mês"

### Teste 3: Média Histórico
1. Selecionar método "Histórico 12 Meses"
2. Preencher 3 meses: 450, 480, 420
3. ✅ Verificar que aparece "Média Mensal: 450 kWh"

### Teste 4: Validação Dinâmica
1. Selecionar "kWh Direto" → tentar Finalizar sem consumo
2. ✅ Deve exigir preenchimento de "Consumo Mensal (kWh)"
3. Trocar para "Valor da Conta" → tentar Finalizar sem valor
4. ✅ Deve exigir preenchimento de "Valor da Conta (R$)"

### Teste 5: Submit Consolidado
1. Preencher wizard completo
2. Usar método "Valor da Conta" com tarifa R$ 0,92
3. Clicar Finalizar
4. ✅ No backend, verificar que `tarifa_kwh_final = 0.92`

---

## 📁 Arquivos Modificados

| Arquivo | Linhas Alteradas | Descrição |
|---------|------------------|-----------|
| `projeto_wizard.html` | ~290 | Renomeado campo `tarifa_kwh_conta` |
| `projeto_wizard.html` | ~1425-1520 | Adicionada lógica de painéis e cálculos |
| `projeto_wizard.html` | ~2150-2180 | Consolidação de campos no submit |
| `projeto_wizard.html` | ~237 | Adicionado `required` em `consumo_kwh_mes` |

---

## 🚀 Próximos Passos (Opcional)

- [ ] Adicionar validação de tarifa mínima/máxima (ex: R$ 0,50 a R$ 2,00)
- [ ] Implementar auto-preenchimento de tarifa média por estado
- [ ] Adicionar gráfico de consumo histórico (Chart.js)
- [ ] Salvar histórico de tarifas do cliente
- [ ] Adicionar campo de "Taxa de Disponibilidade" (mínimo da concessionária)

---

## 👨‍💻 Desenvolvedor
GitHub Copilot + Juliano Saroba

## 📝 Notas Técnicas
- Utiliza jQuery (já incluído no base.html)
- Compatible com Bootstrap 5
- Não requer bibliotecas adicionais
- Auto-save já implementado (mantido intacto)
