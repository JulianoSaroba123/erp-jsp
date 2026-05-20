# 🚀 COMANDO DIRETO NO RENDER - POPULAR PROJETO #6

## Execute este comando no Render Shell:

```bash
python -c "
from app import create_app
from app.extensoes import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Verificar dados atuais
    print('\n🔍 DADOS ATUAIS DO PROJETO #6')
    print('=' * 60)
    query = text('SELECT id, nome_cliente, kit_id, placa_id, inversor_id FROM calculo_energia_solar WHERE id = 6')
    result = db.engine.connect().execute(query).fetchone()
    if result:
        print(f'Cliente: {result[1]}')
        print(f'kit_id: {result[2] or \"NULL\"}')
        print(f'placa_id: {result[3] or \"NULL\"}')
        print(f'inversor_id: {result[4] or \"NULL\"}')
    else:
        print('❌ Projeto 6 não encontrado!')
        exit(1)
    
    # Buscar primeira placa
    print('\n🔍 BUSCANDO PLACA...')
    placa = db.engine.connect().execute(text('SELECT id, modelo FROM placa_solar LIMIT 1')).fetchone()
    if placa:
        print(f'✅ Placa ID {placa[0]}: {placa[1]}')
        placa_id = placa[0]
    else:
        print('❌ Nenhuma placa encontrada!')
        exit(1)
    
    # Buscar primeiro inversor
    print('\n🔍 BUSCANDO INVERSOR...')
    inversor = db.engine.connect().execute(text('SELECT id, modelo FROM inversor_solar LIMIT 1')).fetchone()
    if inversor:
        print(f'✅ Inversor ID {inversor[0]}: {inversor[1]}')
        inversor_id = inversor[0]
    else:
        print('❌ Nenhum inversor encontrado!')
        exit(1)
    
    # Buscar kit compatível (opcional)
    print('\n🔍 BUSCANDO KIT...')
    kit = db.engine.connect().execute(text('SELECT id, descricao FROM kit_solar WHERE placa_id = :p AND inversor_id = :i LIMIT 1'), {'p': placa_id, 'i': inversor_id}).fetchone()
    if kit:
        print(f'✅ Kit ID {kit[0]}: {kit[1]}')
        kit_id = kit[0]
    else:
        print('⚠️ Nenhum kit encontrado (OK, pode continuar sem)')
        kit_id = None
    
    # Atualizar projeto
    print('\n✍️ ATUALIZANDO PROJETO #6...')
    conn = db.engine.connect()
    conn.execute(text('UPDATE calculo_energia_solar SET placa_id = :p, inversor_id = :i, kit_id = :k WHERE id = 6'), {'p': placa_id, 'i': inversor_id, 'k': kit_id})
    conn.commit()
    
    # Verificar resultado
    print('\n✅ RESULTADO FINAL:')
    print('=' * 60)
    result = conn.execute(text('SELECT kit_id, placa_id, inversor_id FROM calculo_energia_solar WHERE id = 6')).fetchone()
    print(f'kit_id: {result[0] or \"NULL\"}')
    print(f'placa_id: {result[1]}')
    print(f'inversor_id: {result[2]}')
    print('\n🎉 SUCESSO! Agora teste no navegador (Ctrl+F5)')
"
```

---

## ⚠️ SE DER ERRO "No module named 'app'"

Execute primeiro:

```bash
cd ~/project/src
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH
```

Depois execute o comando acima.

---

## 🧪 DEPOIS DE EXECUTAR

1. **Ctrl+F5** no navegador
2. Abrir modal "Editar Orçamento"
3. Kit/Placa/Inversor devem aparecer! 🎉

---

## 📸 ME ENVIE O OUTPUT!
