"""
Diagnóstico de Status das Ordens de Serviço
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Criar app minimal
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from app.ordem_servico.ordem_servico_model import OrdemServico

with app.app_context():
    print("="*60)
    print("📊 DIAGNÓSTICO DE STATUS DAS ORDENS DE SERVIÇO")
    print("="*60)
    
    # Total geral
    total = OrdemServico.query.count()
    print(f"\n✅ Total de OS no banco: {total}")
    
    # Total ativas
    ativas = OrdemServico.query.filter_by(ativo=True).count()
    print(f"✅ Total de OS ativas (ativo=True): {ativas}")
    
    # Contar por status
    print(f"\n📊 CONTAGEM POR STATUS (apenas ativas):")
    status_counts = db.session.query(
        OrdemServico.status,
        db.func.count(OrdemServico.id)
    ).filter(
        OrdemServico.ativo == True
    ).group_by(OrdemServico.status).all()
    
    for status, count in status_counts:
        print(f"   {status}: {count}")
    
    # Listar primeiras 10 OSs
    print(f"\n📋 PRIMEIRAS 10 OSs (ativas):")
    ordens = OrdemServico.query.filter_by(ativo=True).limit(10).all()
    for os in ordens:
        print(f"   ID={os.id} | Num={os.numero} | Status='{os.status}' | Cliente={os.cliente.nome if os.cliente else 'N/A'}")
    
    print("\n" + "="*60)
    print("✅ Diagnóstico concluído!")
    print("="*60)
