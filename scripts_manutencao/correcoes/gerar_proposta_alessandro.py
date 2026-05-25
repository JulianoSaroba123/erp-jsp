"""
Gerar proposta do Projeto #3 (Alessandro) - cliente real
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.energia_solar.catalogo_model import ProjetoSolar
from app.energia_solar.proposta_word_service import gerar_docx_proposta

app = create_app()

with app.app_context():
    projeto = ProjetoSolar.query.get(3)
    
    if not projeto:
        print("❌ Projeto #3 não encontrado!")
    else:
        template_path = Path("app/energia_solar/templates_word/proposta_solar_modelo.docx")
        output_dir = Path("app/energia_solar/documentos_gerados")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"proposta_alessandro_projeto_{projeto.id}.docx"
        
        print(f"🔧 Gerando proposta para: {projeto.id}")
        gerar_docx_proposta(projeto, str(template_path), str(output_path))
        print(f"\n✅ PROPOSTA GERADA!")
        print(f"📄 {output_path}")
        print(f"\n💡 Este documento tem o LAYOUT BONITO do seu template")
        print(f"   + TODOS os dados reais do Alessandro!")
