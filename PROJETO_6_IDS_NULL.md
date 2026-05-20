# 🚨 KIT NÃO APARECE - PROJETO #6 COM IDs NULL

## 🎯 DIAGNÓSTICO

✅ **Migração executada:** 98 colunas no banco  
✅ **Colunas existem:** kit_id, placa_id, inversor_id  
❌ **Valores NULL:** Projeto #6 não tem IDs preenchidos  
❌ **Backend:** Retorna `projeto.kit = None`  
❌ **JavaScript:** Detecta "Projeto SEM kit" e não adiciona nada

---

## ✅ SOLUÇÃO: POPULAR PROJETO #6

Execute no **Render Shell:**

```bash
python popular_projeto_6_render.py
```

**O que esse script faz:**

1️⃣ **Lista dados atuais** do projeto #6  
2️⃣ **Busca placa** compatível no catálogo  
3️⃣ **Busca inversor** compatível no catálogo  
4️⃣ **Busca kit** que usa placa+inversor (opcional)  
5️⃣ **Atualiza projeto** com placa_id, inversor_id, kit_id  
6️⃣ **Verifica resultado** final

---

## 📋 OUTPUT ESPERADO

```
🔍 DADOS ATUAIS DO PROJETO #6
============================================================
📊 Cliente: Mauricio Tadeu Ferreira
📦 Número de painéis: 26
🔌 Número de inversores: 1

🆔 IDs atuais:
   kit_id: NULL ❌
   placa_id: NULL ❌
   inversor_id: NULL ❌

🔍 BUSCANDO PLACA NO CATÁLOGO
============================================================
✅ Placa encontrada:
   ID: 1
   Modelo: MODULO FOTOVOLTAICO 585W BIFACIAL N-TYPE
   Fabricante: DMEGC TIER 1
   Potência: 585W
   Preço: R$ 350.00

🔍 BUSCANDO INVERSOR NO CATÁLOGO
============================================================
✅ Inversor encontrado:
   ID: 3
   Modelo: 1 x ASN-10SL
   Fabricante: DEYE
   Potência: 10.0kW
   Preço: R$ 2500.00

🔍 BUSCANDO KIT COMPATÍVEL
============================================================
✅ Kit encontrado:
   ID: 5
   Fabricante: DEYE
   Descrição: Kit 5.6kWp
   Potência: 5.6 kWp
   Preço: R$ 2800.00

✍️ ATUALIZANDO PROJETO #6
============================================================
✅ Projeto #6 atualizado com sucesso!
   placa_id: 1
   inversor_id: 3
   kit_id: 5

🎉 SUCESSO!
============================================================
Agora teste no navegador:
1. Ctrl+F5 para limpar cache
2. Abrir modal 'Editar Orçamento'
3. Kit/Placa/Inversor devem aparecer!
```

---

## 🧪 TESTE NO NAVEGADOR

1. **Abrir:** https://erp-jsp-th5o.onrender.com/energia-solar/projetos/6/dashboard

2. **Ctrl+F5** (limpar cache)

3. **F12** → Console

4. **Clicar:** "💰 Editar Orçamento"

5. **Verificar Console:**
   ```javascript
   ✅ Kit adicionado: Kit 5.6kWp  // Em vez de "Projeto SEM kit"
   ✅ Placa adicionada: MODULO FOTOVOLTAICO 585W x26
   ✅ Inversor adicionado: 1 x ASN-10SL
   ```

6. **Verificar tabela:**
   ```
   KIT FOTOVOLTAICO - Kit 5.6kWp      | R$ 2.800,00 | 🔵 🗑️
   PLACAS SOLARES x26                 | R$ 9.100,00 | 🔵 🗑️
   INVERSOR 1 x ASN-10SL              | R$ 2.500,00 | 🔵 🗑️
   ```

---

## 🔧 SE NÃO HOUVER KIT/PLACA/INVERSOR NO CATÁLOGO

Se o script disser "❌ Nenhuma placa/inversor/kit encontrado":

### **Opção 1: Cadastrar equipamentos**

Acesse: https://erp-jsp-th5o.onrender.com/energia-solar/catalogo

- Cadastre placas, inversores e kits
- Depois execute o script novamente

### **Opção 2: Usar workaround temporário**

Vou criar um endpoint que busca dados de equipamentos salvos no próprio projeto (campos texto) e monta o orçamento dinamicamente.

---

## ⏱️ TEMPO

- **Script:** 1 minuto
- **Teste:** 2 minutos
- **Total:** 3 minutos

---

## 📞 PRÓXIMO PASSO

**RODE AGORA NO RENDER SHELL:**

```bash
python popular_projeto_6_render.py
```

Me envie o **output completo**! 📸
