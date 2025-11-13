# 🔧 CORREÇÃO IMPLEMENTADA - BUG NOVA PROPOSTA

## ❌ PROBLEMA IDENTIFICADO

**Bug:** Quando criava uma nova proposta pela primeira vez, produtos e serviços eram perdidos/deletados. Só funcionava na edição.

**Causa:** A função `nova_proposta()` não processava produtos e serviços, apenas criava a proposta básica.

## ✅ CORREÇÃO APLICADA

### **Arquivo:** `app/proposta/proposta_routes.py`

**Função `nova_proposta()` - Linha ~165:**

Adicionado após `db.session.commit()`:

```python
# CORREÇÃO: Processar produtos e serviços na criação inicial
try:
    from app.proposta.proposta_model import PropostaProduto, PropostaServico
    
    # Processar produtos
    produtos_descricoes = request.form.getlist('produto_descricao[]')
    produtos_qtds = request.form.getlist('produto_quantidade[]')
    produtos_valores = request.form.getlist('produto_valor[]')
    
    # Validar e preparar produtos
    valor_total_produtos = 0
    produtos_validos = []
    for i in range(len(produtos_descricoes)):
        descricao = produtos_descricoes[i].strip()
        if descricao:
            qtd = converter_quantidade(produtos_qtds[i] if i < len(produtos_qtds) else '1')
            valor = converter_valor_monetario(produtos_valores[i] if i < len(produtos_valores) else '0') or 0.0
            valor_item = qtd * valor
            produtos_validos.append({
                'descricao': descricao,
                'quantidade': qtd,
                'valor_unitario': valor,
                'valor_total': valor_item
            })
            valor_total_produtos += valor_item
    
    # Processar serviços (igual aos produtos)
    servicos_descricoes = request.form.getlist('servico_descricao[]')
    servicos_qtds = request.form.getlist('servico_horas[]')
    servicos_valores = request.form.getlist('servico_valor[]')
    
    # Validar e preparar serviços
    valor_total_servicos = 0
    servicos_validos = []
    for i in range(len(servicos_descricoes)):
        descricao = servicos_descricoes[i].strip()
        if descricao:
            qtd = converter_quantidade(servicos_qtds[i] if i < len(servicos_qtds) else '1')
            valor = converter_valor_monetario(servicos_valores[i] if i < len(servicos_valores) else '0') or 0.0
            valor_item = qtd * valor
            servicos_validos.append({
                'descricao': descricao,
                'quantidade': qtd,
                'valor_unitario': valor,
                'valor_total': valor_item
            })
            valor_total_servicos += valor_item
    
    # Inserir produtos válidos no banco
    for produto in produtos_validos:
        novo_produto = PropostaProduto(
            proposta_id=nova_prop.id,
            descricao=produto['descricao'],
            quantidade=produto['quantidade'],
            valor_unitario=produto['valor_unitario'],
            valor_total=produto['valor_total'],
            ativo=True
        )
        db.session.add(novo_produto)
    
    # Inserir serviços válidos no banco
    for servico in servicos_validos:
        novo_servico = PropostaServico(
            proposta_id=nova_prop.id,
            descricao=servico['descricao'],
            quantidade=servico['quantidade'],
            valor_unitario=servico['valor_unitario'],
            valor_total=servico['valor_total'],
            ativo=True
        )
        db.session.add(novo_servico)
    
    # Calcular valor total e atualizar proposta
    desconto_valor = (valor_total_produtos + valor_total_servicos) * (nova_prop.desconto / 100) if nova_prop.desconto else 0
    valor_final = (valor_total_produtos + valor_total_servicos) - desconto_valor
    
    nova_prop.valor_produtos = valor_total_produtos
    nova_prop.valor_servicos = valor_total_servicos 
    nova_prop.valor_total = valor_final
    
    db.session.commit()
    
except Exception as e:
    logger.error(f"Erro ao processar produtos/serviços na criação: {str(e)}")
    db.session.rollback()
```

## 🎯 RESULTADO ESPERADO

**ANTES da correção:**
1. ❌ Criar nova proposta → produtos/serviços perdidos
2. ✅ Editar proposta → produtos/serviços funcionavam

**DEPOIS da correção:**
1. ✅ Criar nova proposta → produtos/serviços salvos corretamente
2. ✅ Editar proposta → continua funcionando

## 🧪 COMO TESTAR

### Teste Manual:
1. Execute `python run.py`
2. Acesse `http://127.0.0.1:5001/propostas/nova`
3. Preencha título, cliente
4. **ADICIONE produtos e serviços**
5. Clique em "Criar Proposta"
6. Verifique se os produtos/serviços foram salvos

### Teste Automatizado:
```bash
python testar_correcao_proposta.py
```

## 📊 STATUS

✅ **CORREÇÃO IMPLEMENTADA**
✅ **CÓDIGO ADICIONADO**
⏳ **TESTE PENDENTE**

---

**Próximo passo:** Testar manualmente a criação de uma nova proposta para confirmar que produtos e serviços são salvos corretamente na primeira vez.