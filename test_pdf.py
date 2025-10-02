#!/usr/bin/env python3
"""
Script para testar geração de PDF da Ordem de Serviço
"""
import sys
import os

# Adicionar o caminho do projeto
sys.path.append(os.path.abspath('.'))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.ordem_servico.os_model import OrdemServico
from aplicacao.ordem_servico.simple_pdf_generator import SimplePDFGenerator

def test_pdf_generation():
    """Testa a geração de PDF"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=== TESTE DE GERAÇÃO DE PDF ===")
            
            # Buscar uma OS existente
            os = OrdemServico.query.first()
            
            if not os:
                print("❌ Nenhuma Ordem de Serviço encontrada no banco!")
                print("   Crie uma OS primeiro através da interface web.")
                return False
                
            print(f"📋 OS encontrada: {os.codigo}")
            print(f"📋 Cliente: {os.cliente.nome if os.cliente else 'Sem cliente'}")
            print(f"📋 Data: {os.data_emissao}")
            
            # Tentar gerar PDF
            print("\n=== INICIANDO GERAÇÃO DE PDF ===")
            generator = SimplePDFGenerator()
            
            pdf_bytes = generator.generate_pdf(os)
            
            if pdf_bytes and len(pdf_bytes) > 100:
                print(f"✅ PDF gerado com sucesso! Tamanho: {len(pdf_bytes)} bytes")
                
                # Salvar PDF de teste
                output_file = f"teste_pdf_OS_{os.codigo}.pdf"
                with open(output_file, 'wb') as f:
                    f.write(pdf_bytes)
                    
                print(f"💾 PDF salvo como: {output_file}")
                return True
            else:
                print(f"❌ PDF gerado é muito pequeno ou inválido: {len(pdf_bytes) if pdf_bytes else 0} bytes")
                return False
                
        except Exception as e:
            print(f"❌ Erro durante teste: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_pdf_generation()
    sys.exit(0 if success else 1)