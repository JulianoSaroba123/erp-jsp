# 🎯 APLICAR TUDO NO RENDER - GUIA COMPLETO

## ✅ O que foi implementado localmente:

### 1️⃣ **Intervalo de Almoço**
- ✅ Campo "Intervalo Almoço (min)" adicionado ao formulário
- ✅ Cálculo automático: Total = (Hora Final - Hora Inicial) - Intervalo
- ✅ Coluna `intervalo_almoco` adicionada ao banco PostgreSQL local
- ✅ Backend salva e carrega o valor

### 2️⃣ **Colaboradores no PDF**
- ✅ Seção detalhada com tabela de colaboradores
- ✅ Mostra: Nome | Data | Entrada | Saída | Total
- ✅ **Horas Normais** (até 8h) em verde
- ✅ **Horas Extras** (acima de 8h) em vermelho
- ✅ Legenda com cores

### 3️⃣ **Ocultação de Valores para Colaboradores**
- ✅ Formulário: Seções financeiras ocultas
- ✅ Visualização: Valores totais, condições de pagamento e parcelas ocultos
- ✅ Colaboradores veem apenas: tempo, KM, descrição

---

## 🔄 APLICAR NO RENDER (Ordem de Execução):

### **Passo 1: Migração do Banco de Dados**

No **Render Shell**, execute:

```bash
# 1. Entrar no Python
python
```

Copie e cole este bloco completo:

```python
from app.app import app
from app.extensoes import db
from sqlalchemy import text, inspect

with app.app_context():
    inspector = inspect(db.engine)
    colunas = [col['name'] for col in inspector.get_columns('ordem_servico')]
    
    if 'intervalo_almoco' in colunas:
        print("✅ Coluna intervalo_almoco JÁ EXISTE!")
    else:
        db.session.execute(text("ALTER TABLE ordem_servico ADD COLUMN intervalo_almoco INTEGER DEFAULT 60"))
        db.session.commit()
        print("✅ Coluna intervalo_almoco ADICIONADA!")

exit()
```

---

### **Passo 2: Configurar Usuários Colaboradores**

Ainda no **Render Shell**:

```bash
python
```

Copie e cole:

```python
from app.app import app
from app.extensoes import db
from app.auth.usuario_model import Usuario

with app.app_context():
    # Verificar/criar colaborador
    colaborador = Usuario.query.filter_by(usuario='colaborador').first()
    
    if colaborador:
        if colaborador.tipo_usuario != 'colaborador':
            colaborador.tipo_usuario = 'colaborador'
            db.session.commit()
            print("✅ Usuário atualizado para tipo colaborador!")
        else:
            print("✅ Usuário colaborador já configurado!")
    else:
        novo = Usuario(
            usuario='colaborador',
            nome='Técnico Colaborador',
            email='colaborador@jsp.com',
            tipo_usuario='colaborador',
            ativo=True
        )
        novo.set_password('123456')
        db.session.add(novo)
        db.session.commit()
        print("✅ Usuário colaborador criado!")
    
    # Listar todos
    usuarios = Usuario.query.filter_by(ativo=True).all()
    for u in usuarios:
        tipo = u.tipo_usuario if hasattr(u, 'tipo_usuario') else 'indefinido'
        print(f"{u.usuario} | {tipo}")

exit()
```

---

### **Passo 3: Deploy do Código Novo**

No **Render Dashboard**:

1. Acesse seu serviço `erp-jsp`
2. Clique em **"Manual Deploy"** → **"Deploy latest commit"**
3. Aguarde o deploy completar (~5-10 min)
4. ✅ Quando aparecer "Live", o serviço está atualizado

---

## 🧪 TESTAR NO RENDER:

### **Teste 1: Login como Colaborador**
```
URL: https://erp-jsp.onrender.com
Usuário: colaborador
Senha: 123456
```

**Verificar:**
- ✅ Menu mostra APENAS "Ordens de Serviço"
- ✅ Lista mostra APENAS OS operacionais
- ❌ NÃO mostra: Totais, Condições de Pagamento, Valores

### **Teste 2: Criar OS Operacional**
1. Clicar em "Nova Ordem de Serviço"
2. Preencher:
   - Cliente
   - Descrição
   - **Hora Inicial:** 08:00
   - **Hora Final:** 17:00
   - **Intervalo Almoço:** 60 (padrão)
   - **Total calculado:** 8h 00min ✅
3. Salvar
4. ✅ Valores financeiros NÃO devem aparecer

### **Teste 3: Gerar PDF**
1. Abrir uma OS com colaboradores
2. Gerar PDF
3. ✅ Deve mostrar tabela de colaboradores com:
   - Nome, Data, Entrada, Saída
   - Horas Normais (verde)
   - Horas Extras (vermelho)

---

## 📊 RESUMO DAS MIGRAÇÕES:

| Item | Local | Render | Status |
|------|-------|--------|--------|
| Coluna intervalo_almoco | ✅ | ⏳ | Executar Passo 1 |
| Usuário colaborador | ✅ | ⏳ | Executar Passo 2 |
| Código atualizado | ✅ | ⏳ | Executar Passo 3 |
| PDF com colaboradores | ✅ | ⏳ | Após deploy |
| Ocultação de valores | ✅ | ⏳ | Após deploy |

---

## 🆘 TROUBLESHOOTING:

### Erro: "column intervalo_almoco does not exist"
→ Execute o Passo 1 novamente

### Colaborador ainda vê valores
→ Verifique se o tipo_usuario está como 'colaborador' (Passo 2)

### PDF não mostra colaboradores
→ Verifique se a OS tem colaboradores vinculados

---

✅ **PRONTO!** Após executar os 3 passos, o sistema estará completo no Render!
