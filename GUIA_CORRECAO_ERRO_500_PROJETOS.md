# 🚨 GUIA DE CORREÇÃO - Erro 500 em /energia-solar/projetos

## 📋 Problema Identificado

O erro 500 está acontecendo porque a tabela `projeto_solar` no Render não tem os campos que o template `projetos_lista.html` está tentando acessar:
- `circuito` (usado para mostrar tipo de instalação)
- `status_orcamento` (usado para mostrar status do orçamento)

## ✅ Solução

### Opção 1: Executar no Render Shell (RECOMENDADO)

1. **Acesse o Render Dashboard**
   - Vá para https://dashboard.render.com
   - Selecione seu web service `erp-jsp-th5o`

2. **Abra o Shell**
   - Clique na aba "Shell" no canto direito
   - Aguarde o terminal carregar

3. **Execute o script de correção**
   ```bash
   python fix_render_campos_faltantes.py
   ```

4. **Aguarde a confirmação**
   - Você verá: `✅ CORREÇÃO CONCLUÍDA!`
   - Campos adicionados: 15

5. **Teste a aplicação**
   - Acesse: https://erp-jsp-th5o.onrender.com/energia-solar/projetos
   - A página deve carregar sem erro 500

### Opção 2: Executar via Deploy Manual

Se preferir fazer via deploy:

1. **Commit e push das alterações**
   ```bash
   git add .
   git commit -m "fix: adiciona campos faltantes em projeto_solar"
   git push origin main
   ```

2. **O Render fará auto-deploy**
   - As migrações serão executadas automaticamente
   - O app será reiniciado

## 🔍 O que o script faz?

O script `fix_render_campos_faltantes.py` adiciona os seguintes campos:

```sql
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS circuito VARCHAR(20);
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS status_orcamento VARCHAR(20) DEFAULT 'pendente';
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS numero VARCHAR(20);
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS tipo_instalacao VARCHAR(20) DEFAULT 'monofasica';
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS taxa_disponibilidade DOUBLE PRECISION;
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS economia_mensal DOUBLE PRECISION;
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS tempo_retorno DOUBLE PRECISION;
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS economia_25_anos DOUBLE PRECISION;
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS economia_anual DOUBLE PRECISION;
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS payback_anos DOUBLE PRECISION;
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS modalidade_gd VARCHAR(50);
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS aliquota_fio_b DOUBLE PRECISION;
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS usuario_criador VARCHAR(100);
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS data_atualizacao TIMESTAMP;
```

E sincroniza dados existentes:
```sql
UPDATE projeto_solar 
SET circuito = CASE 
    WHEN tipo_instalacao = 'monofasica' THEN 'Monofásico'
    WHEN tipo_instalacao = 'bifasica' THEN 'Bifásico'
    WHEN tipo_instalacao = 'trifasica' THEN 'Trifásico'
    ELSE circuito
END
WHERE circuito IS NULL AND tipo_instalacao IS NOT NULL;
```

## 🧪 Verificação

Após executar, verifique:

1. **No Shell do Render**:
   ```python
   python diagnostico_projetos_render.py
   ```
   
2. **No navegador**:
   - https://erp-jsp-th5o.onrender.com/energia-solar/projetos
   - Deve listar os projetos sem erro

## 📝 Arquivos Modificados

- ✅ `app/energia_solar/catalogo_model.py` - Modelo atualizado
- ✅ `fix_render_campos_faltantes.py` - Script de correção
- ✅ `diagnostico_projetos_render.py` - Script de diagnóstico

## 🆘 Se o erro persistir

1. Verifique os logs do Render:
   ```
   Dashboard > Logs > Recent Logs
   ```

2. Execute diagnóstico completo:
   ```bash
   python diagnostico_projetos_render.py
   ```

3. Verifique se a tabela tem todos os campos:
   ```python
   from app.app import create_app
   from app.extensoes import db
   
   app = create_app()
   with app.app_context():
       result = db.session.execute(db.text("""
           SELECT column_name 
           FROM information_schema.columns 
           WHERE table_name = 'projeto_solar'
           ORDER BY ordinal_position
       """))
       for row in result:
           print(row[0])
   ```

## ✨ Próximos Passos

Após corrigir, você poderá:
- ✅ Listar projetos solares
- ✅ Criar novos projetos
- ✅ Editar projetos existentes
- ✅ Ver dashboard de projetos
- ✅ Gerar propostas em PDF

---

**Criado em**: 12/01/2026  
**Versão**: 1.0
