# 🔧 Correção do Cliente ID 20 no Render

## 🔍 Problema Identificado

Cliente ID 20 existe no banco de dados do Render mas tem **dados corrompidos** que causam erro 500 ao tentar editar.

### Erro Observado
- **URL**: `https://erp-jsp-th5o.onrender.com/cliente/20/editar`
- **Status**: Internal Server Error (500)
- **Causa**: Campos obrigatórios nulos/inválidos ou properties com erros

## ✅ Solução

### Opção 1: Via Dashboard do Render (RECOMENDADO)

1. **Acesse o Render Dashboard**
   - URL: https://dashboard.render.com/
   - Clique no serviço `erp-jsp-th5o`

2. **Abra o Shell**
   - No menu lateral, clique em **Shell**
   - Aguarde o terminal carregar

3. **Execute o comando de correção**
   ```bash
   python corrigir_cliente_20_render.py
   ```

4. **Verifique o resultado**
   - O script irá mostrar os problemas encontrados
   - Aplicará as correções automaticamente
   - Testará os properties do cliente

5. **Teste no navegador**
   - Recarregue a página: `https://erp-jsp-th5o.onrender.com/cliente/20/editar`
   - Deve abrir normalmente

### Opção 2: Via Python Shell no Render

Execute este código Python diretamente no Shell do Render:

```python
from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente

app = create_app()
with app.app_context():
    cliente = Cliente.query.get(20)
    if not cliente:
        print('❌ Cliente 20 não existe')
    else:
        print(f'✅ Cliente: {cliente.nome}')
        
        # Corrigir campos obrigatórios
        if not cliente.nome or cliente.nome.strip() == '':
            cliente.nome = cliente.nome_fantasia or f'Cliente {cliente.id}'
        
        if not cliente.tipo or cliente.tipo not in ['PF', 'PJ']:
            cliente.tipo = 'PF'
        
        cliente.status = cliente.status or 'ativo'
        cliente.ativo = True
        cliente.limite_credito = cliente.limite_credito or 0
        cliente.desconto_padrao = cliente.desconto_padrao or 0
        cliente.prazo_pagamento_padrao = cliente.prazo_pagamento_padrao or 30
        cliente.classificacao = cliente.classificacao if cliente.classificacao in ['A','B','C'] else 'A'
        
        db.session.commit()
        print('✅ Corrigido!')
```

### Opção 3: Desativar/Excluir o Cliente

Se preferir apenas remover o cliente problemático:

```python
from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente

app = create_app()
with app.app_context():
    cliente = Cliente.query.get(20)
    if cliente:
        cliente.ativo = False
        db.session.commit()
        print('✅ Cliente 20 desativado')
```

## 🧪 Validação

Após aplicar a correção, teste:

1. **Listar clientes**: https://erp-jsp-th5o.onrender.com/cliente/
2. **Visualizar cliente 20**: https://erp-jsp-th5o.onrender.com/cliente/20
3. **Editar cliente 20**: https://erp-jsp-th5o.onrender.com/cliente/20/editar

## 📋 Campos Corrigidos

O script corrige automaticamente:

- ✅ `nome` - Garante que não esteja vazio
- ✅ `tipo` - Define como PF ou PJ válido
- ✅ `status` - Define como 'ativo'
- ✅ `ativo` - Define como True
- ✅ `limite_credito` - Define como 0 se nulo
- ✅ `desconto_padrao` - Define como 0 se nulo
- ✅ `prazo_pagamento_padrao` - Define como 30 se nulo
- ✅ `classificacao` - Define como 'A' se inválido

## 🔒 Prevenção Futura

Para evitar que isso aconteça novamente, os handlers de erro foram adicionados em `cliente_routes.py`:

```python
@cliente_bp.errorhandler(404)
def cliente_nao_encontrado(e):
    flash('Cliente não encontrado.', 'error')
    return redirect(url_for('cliente.listar'))

@cliente_bp.errorhandler(500)
def erro_interno_cliente(e):
    flash(f'Erro interno ao processar cliente: {str(e)}', 'error')
    return redirect(url_for('cliente.listar'))
```

## 🚀 Deploy Automático

Para aplicar as correções via commit Git:

```bash
git add corrigir_cliente_20_render.py
git commit -m "fix: adiciona script para corrigir cliente 20 corrompido"
git push origin main
```

O Render fará deploy automático e o script estará disponível no servidor.

---

**Status**: ⏳ Aguardando correção no Render  
**Prioridade**: 🔴 Alta (impede edição de cliente)  
**Tempo estimado**: 2-3 minutos
