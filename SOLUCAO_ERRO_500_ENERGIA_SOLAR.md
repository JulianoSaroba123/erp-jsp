# 🔧 Solução: Erro 500 em /energia-solar/ no Render

## 🐛 Problema
- URL: https://erp-jsp-th5o.onrender.com/energia-solar/
- Erro: **500 Internal Server Error**
- Console: "Failed to load resource: the server responded with a status of 500 ()"

## 🔍 Diagnóstico

O erro pode ter várias causas:

### 1. **Tabelas não criadas**
A tabela `calculo_energia_solar` pode não existir no PostgreSQL do Render.

### 2. **Usuário não autenticado**
A rota `/energia-solar/` requer `@login_required`, mas pode não ter usuário admin.

### 3. **Erro na query do banco**
A consulta SQL pode estar falhando por tipo de dado incompatível.

## ✅ Solução Passo a Passo

### Passo 1: Acessar Shell do Render

1. Acesse: https://dashboard.render.com
2. Entre no serviço **erp-jsp-th5o**
3. Clique em **Shell** (canto superior direito)

### Passo 2: Verificar/Criar Admin

Execute no Shell:

```bash
python verificar_admin_render.py
```

Se não existir, será criado automaticamente.

### Passo 3: Verificar Tabelas

Execute no Shell:

```bash
python scripts/criar_tabelas.py
```

Isso garante que todas as tabelas estão criadas.

### Passo 4: Verificar Logs

No Dashboard do Render:
1. Clique na aba **Logs**
2. Role até o final
3. Procure por:
   - `ERROR`
   - `Traceback`
   - `sqlalchemy.exc`
   - `OperationalError`

Copie o erro completo e me envie.

### Passo 5: Testar Login

1. Acesse: https://erp-jsp-th5o.onrender.com/auth/login
2. Faça login:
   - **Usuario**: `admin`
   - **Senha**: `admin123`
3. Depois acesse: https://erp-jsp-th5o.onrender.com/energia-solar/

## 🔧 Correções Alternativas

### Se o erro persistir:

#### Opção A: Forçar Recreação das Tabelas

```bash
# No Shell do Render:
python
>>> from app.app import create_app
>>> from app.extensoes import db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
...     print("Tabelas criadas!")
```

#### Opção B: Verificar Modelo

Verifique se o modelo `CalculoEnergiaSolar` está sendo importado corretamente:

```bash
# No Shell do Render:
python
>>> from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
>>> print("Model OK!")
```

#### Opção C: Desabilitar Cache de Template

Adicionar no arquivo `app/energia_solar/energia_solar_routes.py`:

```python
@energia_solar_bp.route('/')
@login_required
def dashboard():
    """Dashboard do módulo de Energia Solar"""
    try:
        calculos = CalculoEnergiaSolar.query.order_by(
            CalculoEnergiaSolar.data_calculo.desc()
        ).limit(10).all()
        
        # Estatísticas
        total_calculos = CalculoEnergiaSolar.query.count()
        potencia_total = db.session.query(
            db.func.sum(CalculoEnergiaSolar.potencia_sistema)
        ).scalar() or 0
        economia_total = db.session.query(
            db.func.sum(CalculoEnergiaSolar.economia_anual)
        ).scalar() or 0
        
        return render_template('energia_solar/dashboard.html',
                             calculos=calculos,
                             total_calculos=total_calculos,
                             potencia_total=potencia_total,
                             economia_total=economia_total)
    except Exception as e:
        logger.error(f"Erro no dashboard energia solar: {e}")
        flash(f'Erro ao carregar dashboard: {str(e)}', 'error')
        return redirect(url_for('painel.dashboard'))
```

## 📊 Checklist

- [ ] Shell do Render acessado
- [ ] Script `verificar_admin_render.py` executado
- [ ] Usuário admin existe/criado
- [ ] Login realizado com sucesso
- [ ] Tabelas verificadas
- [ ] Logs do Render verificados
- [ ] Rota `/energia-solar/` testada

## 📝 Próximos Passos

Após executar os passos acima, me informe:

1. ✅ Funcionou? Qual passo resolveu?
2. ❌ Ainda com erro? Copie o log completo do Render
3. 🤔 Outro comportamento? Descreva o que aconteceu

---

**Criado em**: 2025-01-12  
**Autor**: GitHub Copilot  
**Versão**: 1.0
