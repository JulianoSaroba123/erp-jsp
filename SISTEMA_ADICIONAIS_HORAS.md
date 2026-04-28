# 💼 Sistema de Controle de Adicionais de Horas - Colaboradores
## ERP JSP v3.0

---

## 🎯 Objetivo

Permitir controle separado de **custos com colaboradores** e **receita do cliente** quando há negociações comerciais especiais de adicionais de horas extras, feriados, finais de semana etc.

---

## 📋 Regras de Adicionais (Padrão)

### Para Colaboradores (CUSTO - Sempre aplicado)

✅ **Após 17:00 em dias normais**: 50% de adicional  
✅ **Sábados**: 50% de adicional  
✅ **Domingos**: 100% de adicional  
✅ **Feriados**: 100% de adicional  

**Exemplo:**  
- Colaborador recebe R$ 50/h normalmente
- Trabalhou no domingo: R$ 50 × 2 = R$ 100/h (100% adicional)

### Para Clientes (RECEITA - Customizável)

Por padrão, cobra do cliente o mesmo percentual pago ao colaborador. Mas você pode negociar valores diferentes!

**Exemplo de Negociação:**
- **Situação**: Feriado 21/04/2026
- **Colaborador recebe**: R$ 50/h + 100% = R$ 100/h (custo)
- **Cliente paga**: R$ 50/h + 50% = R$ 75/h (receita negociada)
- **Resultado**: Margem menor, mas fecha o negócio ✅

---

## 🛠️ Como Funciona

### 1. Cálculo Automático

O sistema detecta automaticamente:
- ✓ Dia da semana (segunda a domingo)
- ✓ Feriados nacionais
- ✓ Horário de trabalho (se passou das 17:00)

E aplica o adicional correto para o **colaborador** (custo).

### 2. Cobrança Padrão

Se você **não preencher** nenhum campo extra:
- Cliente paga o mesmo adicional que o colaborador recebe
- Margem mantém-se estável

### 3. Cobrança Negociada

Se você preencher o campo **"% Adicional para Cliente"**:
- Colaborador continua recebendo conforme regras trabalhistas
- Cliente paga o percentual que você definiu
- Sistema calcula automaticamente a diferença de margem

---

## 💻 Campos Adicionados

### Na tabela `ordem_servico_colaborador`:

1. **`percentual_adicional_cobranca`** (Numeric 5,2)
   - Percentual customizado cobrado do cliente
   - `NULL` = usar percentual padrão (igual ao do colaborador)
   - Valor definido = usar esse percentual para o cliente
   - Exemplo: `50.00` para 50%

2. **`valor_hora_custo`** (Numeric 10,2)
   - Valor/hora pago ao colaborador (com adicional aplicado)
   - Calculado automaticamente
   - Usado para controle de custos

3. **`valor_hora_receita`** (Numeric 10,2)
   - Valor/hora cobrado do cliente (com adicional aplicado)
   - Calculado automaticamente
   - Usado para faturamento

---

## 📝 Exemplo Prático

### Cenário 1: Sem Negociação (Padrão)

**Dados:**
- Colaborador: João
- Valor/hora base: R$ 50,00
- Data: 21/04/2026 (Feriado - Tiradentes)
- Horas trabalhadas: 8h

**Cálculo:**
- Sistema detecta: Feriado = 100% adicional
- **Custo (colaborador)**: R$ 50 × 2 = R$ 100/h → 8h = R$ 800,00
- **Receita (cliente)**: R$ 50 × 2 = R$ 100/h → 8h = R$ 800,00
- **Margem**: R$ 0,00 (quebra-zero, só no adicional)

### Cenário 2: Com Negociação Comercial

**Dados:**
- Colaborador: João
- Valor/hora base: R$ 50,00
- Data: 21/04/2026 (Feriado - Tiradentes)
- Horas trabalhadas: 8h
- **Negociado com cliente**: 50% ao invés de 100%

**Cálculo:**
- Sistema detecta: Feriado = 100% adicional
- **Custo (colaborador)**: R$ 50 × 2 = R$ 100/h → 8h = R$ 800,00 ✅
- **Receita (cliente)**: R$ 50 × 1.5 = R$ 75/h → 8h = R$ 600,00 📉
- **Margem**: -R$ 200,00 (prejuízo de R$ 200, mas cliente fechou!)

### Cenário 3: Sábado Normal

**Dados:**
- Colaborador: Maria
- Valor/hora base: R$ 60,00
- Data: 26/04/2026 (Sábado)
- Horas trabalhadas: 4h

**Cálculo:**
- Sistema detecta: Sábado = 50% adicional
- **Custo (colaborador)**: R$ 60 × 1.5 = R$ 90/h → 4h = R$ 360,00
- **Receita (cliente)**: R$ 60 × 1.5 = R$ 90/h → 4h = R$ 360,00
- **Margem**: R$ 0,00 (quebra-zero)

---

## 🔧 Métodos Disponíveis no Model

### Verificação de Tipo de Dia

```python
colaborador.eh_feriado()        # True se é feriado nacional
colaborador.eh_domingo()        # True se é domingo
colaborador.eh_sabado()         # True se é sábado
colaborador.tem_horas_apos_17h()  # True se trabalhou após 17:00
```

### Cálculo de Adicionais

```python
# Retorna o percentual de adicional baseado nas regras
percentual = colaborador.calcular_percentual_adicional_padrao()
# Retorna: Decimal('0.00'), Decimal('50.00') ou Decimal('100.00')

# Calcula valores de custo e receita
custo, receita, perc_colab, perc_cliente = colaborador.calcular_valores_com_adicional(valor_hora_base=50)

# Atualiza os campos automaticamente
colaborador.atualizar_valores_com_adicional(valor_hora_base=50)
```

### Propriedades de Consulta

```python
colaborador.descricao_adicional  # Ex: "Feriado (100%)"
colaborador.total_custo          # Total pago ao colaborador
colaborador.total_receita        # Total cobrado do cliente
colaborador.margem_contribuicao  # Diferença (receita - custo)
```

---

## 📊 Feriados Nacionais Cadastrados

O sistema reconhece automaticamente:
- 01/01 - Ano Novo
- 21/04 - Tiradentes
- 01/05 - Dia do Trabalho
- 07/09 - Independência do Brasil
- 12/10 - Nossa Senhora Aparecida
- 02/11 - Finados
- 15/11 - Proclamação da República
- 25/12 - Natal

**Nota:** Feriados móveis (Carnaval, Páscoa, Corpus Christi) devem ser adicionados manualmente quando necessário.

---

## 🎨 Interface (A Implementar)

### No formulário de lançamento de horas:

1. **Campo automático** (somente leitura):
   - "Tipo de Dia": Mostra "Feriado (100%)", "Sábado (50%)", etc.

2. **Campo editável** (opcional):
   - "% Adicional para Cliente": Campo numérico
   - Placeholder: "Deixe vazio para usar o padrão"
   - Dica: "Preencha apenas se negociou percentual diferente"

3. **Campos calculados** (somente leitura):
   - "Valor/h Custo": Mostra quanto você paga ao colaborador
   - "Valor/h Receita": Mostra quanto cobra do cliente
   - "Margem/h": Mostra a diferença (pode ser negativa!)

---

## ⚠️ Pontos de Atenção

1. **Margem Negativa**: É possível ter margem negativa em negociações comerciais. O sistema vai mostrar claramente quando isso acontecer.

2. **Direitos Trabalhistas**: O percentual pago ao colaborador sempre respeita as regras trabalhistas (50% ou 100%), não importa o que for negociado com o cliente.

3. **Feriados Municipais**: O sistema só reconhece feriados nacionais. Para feriados municipais, você pode:
   - Marcar manualmente o percentual de adicional
   - Ou extender o método `eh_feriado()` para incluir feriados locais

4. **Hora Extra vs Hora Adicional**: 
   - "Hora Extra" = hora trabalhada além da jornada
   - "Adicional" = percentual aplicado sobre o valor/hora

---

## 🚀 Próximos Passos

1. ✅ **Banco de dados:** Campos adicionados
2. ✅ **Model:** Métodos de cálculo implementados
3. ⏳ **Interface:** Atualizar formulário de lançamento de horas
4. ⏳ **PDF:** Mostrar valores de custo e receita na OS
5. ⏳ **Relatório:** Criar relatório de margem por OS/colaborador

---

## 📞 Dúvidas Frequentes

**P: Se eu não preencher nada, como fica?**  
R: Sistema calcula automaticamente e cobra do cliente o mesmo percentual pago ao colaborador.

**P: Posso cobrar MAIS do cliente do que pago ao colaborador?**  
R: Sim! Exemplo: Colaborador recebe 50%, você cobra 100% do cliente.

**P: Como funciona em dia normal após 17:00?**  
R: Sistema detecta que a saída ou hora extra foi após 17:00 e aplica 50% automaticamente.

**P: E se for sábado E feriado?**  
R: Precedência: Feriado > Domingo > Sábado. Então seria 100% (feriado).

**P: Como adicionar feriados municipais?**  
R: Edite o método `eh_feriado()` no model `OrdemServicoColaborador` para incluir novas datas.

---

**Desenvolvido por JSP Soluções - Abril 2026**  
**Versão: 3.0**
