from aplicacao import create_app
from aplicacao.ordem_servico.os_model import OrdemServico
import json

# Criar app context
app = create_app()
with app.app_context():
    # Buscar ordem 9
    ordem = OrdemServico.query.get(9)
    
    print(f"Ordem {ordem.codigo} (ID: {ordem.id})")
    print(f"Anexos dados raw: {repr(ordem.anexos_dados)}")
    
    if ordem.anexos_dados:
        try:
            anexos = json.loads(ordem.anexos_dados)
            print(f"Anexos parseados: {len(anexos)} anexo(s)")
            for i, anexo in enumerate(anexos):
                print(f"  {i+1}: {anexo}")
        except Exception as e:
            print(f"ERRO ao parsear anexos: {e}")
    else:
        print("Nenhum anexo encontrado")