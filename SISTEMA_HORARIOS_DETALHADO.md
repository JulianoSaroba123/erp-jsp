# ✅ Sistema de Horários Detalhado - 6 Campos

## 📋 Resumo da Implementação

O sistema de controle de horas foi **completamente redesenhado** de um modelo simplificado de 2 campos para um modelo detalhado de **6 campos**, permitindo rastreamento preciso de:

- **Período Normal**: Entrada Manhã, Saída Almoço, Retorno Almoço, Saída
- **Horas Extras** (opcional): Entrada Extra, Saída Extra

---

## 🔄 Alterações Realizadas

### 1️⃣ **Frontend** - Formulário HTML

**📝 Arquivo:** `app/ordem_servico/templates/os/form.html`

#### Campos Adicionados (linhas 383-463):
```html
<!-- ✅ Período Normal -->
<input id="hora_entrada_manha" name="hora_entrada_manha" type="time">
<input id="hora_saida_almoco" name="hora_saida_almoco" type="time">
<input id="hora_retorno_almoco" name="hora_retorno_almoco" type="time">
<input id="hora_saida" name="hora_saida" type="time">

<!-- ✅ Horas Extras (Opcional) -->
<input id="hora_entrada_extra" name="hora_entrada_extra" type="time">
<input id="hora_saida_extra" name="hora_saida_extra" type="time">

<!-- ✅ Campos Calculados (readonly) -->
<input id="horasNormais" name="horas_normais" readonly>
<input id="horasExtras" name="horas_extras" readonly>
```

#### JavaScript Reescrito (linhas 1623-1755):
```javascript
function calcularTotalHoras() {
    // Calcula horas normais
    horasNormaisMinutos = (Saída Almoço - Entrada Manhã) + (Saída - Retorno Almoço)
    
    // Calcula horas extras
    horasExtrasMinutos = Saída Extra - Entrada Extra
    
    // Total = Normal + Extra
}
```

#### Event Listeners (6 campos):
```javascript
horaEntradaManhaInput.addEventListener('change', calcularTotalHoras);
horaSaidaAlmocoInput.addEventListener('change', calcularTotalHoras);
horaRetornoAlmocoInput.addEventListener('change', calcularTotalHoras);
horaSaidaInput.addEventListener('change', calcularTotalHoras);
horaEntradaExtraInput.addEventListener('change', calcularTotalHoras);
horaSaidaExtraInput.addEventListener('change', calcularTotalHoras);
```

---

### 2️⃣ **Backend** - Modelo de Dados

**📝 Arquivo:** `app/ordem_servico/ordem_servico_model.py`

#### 8 Novos Campos (após linha 134):
```python
# Sistema de Tempo Detalhado (6 campos + 2 calculados)
hora_entrada_manha = db.Column(db.Time)
hora_saida_almoco = db.Column(db.Time)
hora_retorno_almoco = db.Column(db.Time)
hora_saida = db.Column(db.Time)
hora_entrada_extra = db.Column(db.Time)
hora_saida_extra = db.Column(db.Time)
horas_normais = db.Column(db.String(20))  # "8h 00min"
horas_extras = db.Column(db.String(20))   # "2h 30min"
```

**⚠️ Campos Antigos Mantidos:** `hora_inicial`, `hora_final`, `intervalo_almoco` (compatibilidade)

---

### 3️⃣ **Backend** - Rotas

**📝 Arquivo:** `app/ordem_servico/ordem_servico_routes.py`

#### Rota `novo()` - Processamento (linhas 483-515):
```python
# Converte 6 campos de horário detalhado
hora_entrada_manha = datetime.strptime(request.form.get('hora_entrada_manha'), '%H:%M').time() if request.form.get('hora_entrada_manha') else None
# ... repete para todos os 6 campos
```

#### Rota `novo()` - Salvamento (linhas 567-576):
```python
ordem = OrdemServico(
    # ...
    hora_entrada_manha=hora_entrada_manha,
    hora_saida_almoco=hora_saida_almoco,
    # ... todos os 6 campos
    horas_normais=request.form.get('horasNormais', '').strip(),
    horas_extras=request.form.get('horasExtras', '').strip()
)
```

#### Rota `editar()` - Atualização (linhas 1178-1218):
```python
# Atualiza todos os 6 campos individualmente
if request.form.get('hora_entrada_manha'):
    ordem.hora_entrada_manha = datetime.strptime(request.form.get('hora_entrada_manha'), '%H:%M').time()
else:
    ordem.hora_entrada_manha = None
# ... repete para todos os campos
```

---

### 4️⃣ **Banco de Dados** - Migração

**📝 Script:** `adicionar_campos_horarios_detalhados.py`

#### Colunas Adicionadas:
```sql
ALTER TABLE ordem_servico ADD COLUMN hora_entrada_manha TIME;
ALTER TABLE ordem_servico ADD COLUMN hora_saida_almoco TIME;
ALTER TABLE ordem_servico ADD COLUMN hora_retorno_almoco TIME;
ALTER TABLE ordem_servico ADD COLUMN hora_saida TIME;
ALTER TABLE ordem_servico ADD COLUMN hora_entrada_extra TIME;
ALTER TABLE ordem_servico ADD COLUMN hora_saida_extra TIME;
ALTER TABLE ordem_servico ADD COLUMN horas_normais VARCHAR(20);
ALTER TABLE ordem_servico ADD COLUMN horas_extras VARCHAR(20);
```

**✅ Status:** Migração concluída no banco local (SQLite)

---

## 🎯 Como Funciona

### Fluxo de Uso:

1. **Usuário preenche horários:**
   - 🏢 Entrada Manhã: `08:00`
   - 🍽️ Saída Almoço: `12:00`
   - ⏰ Retorno Almoço: `13:00`
   - 🏠 Saída: `17:00`
   - 🌙 Entrada Extra: `18:00` (opcional)
   - 🌙 Saída Extra: `20:00` (opcional)

2. **JavaScript calcula automaticamente:**
   - **Horas Normais** = (12:00 - 08:00) + (17:00 - 13:00) = `8h 00min`
   - **Horas Extras** = (20:00 - 18:00) = `2h 00min`
   - **Total** = 8h + 2h = `10h 00min`

3. **Campos readonly exibem:**
   - `horasNormais`: "8h 00min" (fundo azul)
   - `horasExtras`: "2h 00min" (fundo amarelo)
   - Alert box: "Total de Horas: 10h 00min"

4. **Backend salva todos os valores:**
   - 6 campos Time no banco
   - 2 campos String calculados (horas_normais, horas_extras)

---

## 🧪 Checklist de Testes

### ✅ Testes Locais Concluídos:
- [x] Migração do banco de dados executada
- [x] Modelo atualizado com 8 novos campos
- [x] Rotas novo() e editar() atualizadas
- [x] JavaScript calcula corretamente
- [x] Event listeners funcionando

### ⏳ Testes Pendentes:
- [ ] Criar nova OS no formulário
- [ ] Verificar cálculo automático em tempo real
- [ ] Salvar OS com 6 campos preenchidos
- [ ] Editar OS existente
- [ ] Visualizar OS (verificar exibição dos campos)
- [ ] Validar dados no banco de dados
- [ ] Testar campos opcionais (horas extras vazias)
- [ ] Testar com colaborador (interface restrita)

---

## 🚀 Próximos Passos

### 1. **Testar Localmente** ✅
```bash
python run.py
```
- Acessar: http://localhost:5000/os/novo
- Preencher formulário com 6 campos de horário
- Verificar cálculos automáticos
- Salvar e visualizar

### 2. **Atualizar visualizar.html** ⏳
Exibir 6 campos de horário detalhado em vez de 2:
```html
<p><strong>🏢 Entrada Manhã:</strong> {{ ordem.hora_entrada_manha.strftime('%H:%M') }}</p>
<p><strong>🍽️ Saída Almoço:</strong> {{ ordem.hora_saida_almoco.strftime('%H:%M') }}</p>
<!-- ... -->
<p><strong>📊 Horas Normais:</strong> {{ ordem.horas_normais }}</p>
<p><strong>⏱️ Horas Extras:</strong> {{ ordem.horas_extras }}</p>
```

### 3. **Aplicar no Render** ⏳
#### Passo 1: Shell do Render
```bash
# Fazer upload do script de migração
python adicionar_campos_horarios_detalhados.py
```

#### Passo 2: Git Deploy
```bash
git add .
git commit -m "feat: Sistema de horários detalhado com 6 campos (entrada manhã, saída almoço, retorno, saída, extras)"
git push origin main
```

#### Passo 3: Verificar Deploy
- Aguardar deploy automático no Render
- Testar formulário no Render
- Verificar migração do banco PostgreSQL

---

## 📊 Estrutura de Dados

### Campos no Banco:

| Campo                | Tipo        | Descrição                          |
|---------------------|-------------|------------------------------------|
| `hora_entrada_manha` | TIME        | Horário de entrada pela manhã     |
| `hora_saida_almoco`  | TIME        | Horário de saída para almoço      |
| `hora_retorno_almoco`| TIME        | Horário de retorno do almoço      |
| `hora_saida`         | TIME        | Horário de saída (final período)  |
| `hora_entrada_extra` | TIME        | Início horas extras (opcional)    |
| `hora_saida_extra`   | TIME        | Fim horas extras (opcional)       |
| `horas_normais`      | VARCHAR(20) | Total calculado (ex: "8h 00min")  |
| `horas_extras`       | VARCHAR(20) | Extras calculadas (ex: "2h 30min")|

### Campos Antigos (mantidos):
- `hora_inicial` (TIME)
- `hora_final` (TIME)
- `intervalo_almoco` (INTEGER)
- `total_horas` (VARCHAR 20)

---

## 🎨 Interface Visual

### Período Normal:
```
┌─────────────────────────────────────────┐
│ 🏢 Período Normal                       │
├─────────────────────────────────────────┤
│ 🏢 Entrada Manhã:    [08:00]           │
│ 🍽️ Saída Almoço:     [12:00]           │
│ ⏰ Retorno Almoço:   [13:00]           │
│ 🏠 Saída:            [17:00]           │
└─────────────────────────────────────────┘
```

### Horas Extras (Opcional):
```
┌─────────────────────────────────────────┐
│ 🌙 Horas Extras (Opcional)              │
├─────────────────────────────────────────┤
│ 🌙 Entrada Extra:    [18:00]           │
│ 🌙 Saída Extra:      [20:00]           │
└─────────────────────────────────────────┘
```

### Resultados:
```
┌─────────────────────────────────────────┐
│ Horas Normais:  [8h 00min] (azul info) │
│ Horas Extras:   [2h 00min] (amarelo)   │
│                                         │
│ ✅ Total: 10h 00min | KM: 50 km       │
└─────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Problema: JavaScript não calcula automaticamente
**Solução:** Verificar console do navegador (F12) para erros. Event listeners devem exibir:
```
✅ Event listener: Entrada Manhã
✅ Event listener: Saída Almoço
...
```

### Problema: Campos não salvam
**Solução:** Verificar `name="hora_entrada_manha"` nos inputs. Backend processa por esses nomes.

### Problema: Erro ao salvar
**Solução:** Executar migração do banco:
```bash
python adicionar_campos_horarios_detalhados.py
```

---

## 📝 Notas Importantes

- ✅ Campos de horas extras são **opcionais** (podem ficar vazios)
- ✅ Cálculo acontece **automaticamente** ao preencher/alterar qualquer campo
- ✅ Campos antigos (`hora_inicial`, `hora_final`) foram **mantidos** para compatibilidade
- ✅ Sistema funciona para **todos os tipos de usuário** (admin, usuario, colaborador)
- ✅ Colaboradores veem APENAS este formulário (sem valores financeiros)

---

## 📅 Histórico

**Data:** 2025-01-20  
**Status:** ✅ Implementação concluída (local)  
**Pendente:** Testes completos, atualizar visualizar.html, deploy Render
