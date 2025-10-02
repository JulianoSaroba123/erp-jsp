#!/usr/bin/env python3
from aplicacao import create_app
from aplicacao.ordem_servico.os_model import OrdemServico
from aplicacao.ordem_servico.simple_pdf_generator import SimplePDFGenerator

app = create_app()

with app.app_context():
    # Buscar uma OS que tem serviços (OS9/OS0358)
    os = OrdemServico.query.filter_by(codigo='OS0358').first()
    
    if os:
        print(f"Testando geração de PDF para {os.codigo}")
        print(f"Cliente: {os.cliente.nome if os.cliente else 'N/A'}")
        print(f"Serviços JSON: {os.servicos_dados[:100] if os.servicos_dados else 'Nenhum'}...")
        print(f"Produtos JSON: {os.produtos_dados[:100] if os.produtos_dados else 'Nenhum'}...")
        
        # Tentar gerar PDF
        try:
            generator = SimplePDFGenerator()
            pdf_bytes = generator.generate_pdf(os)
            
            if pdf_bytes:
                # Salvar PDF para teste
                with open(f'teste_pdf_{os.codigo}_novo.pdf', 'wb') as f:
                    f.write(pdf_bytes)
                print(f"✅ PDF gerado com sucesso! Tamanho: {len(pdf_bytes)} bytes")
                print(f"📄 Arquivo salvo como: teste_pdf_{os.codigo}_novo.pdf")
            else:
                print("❌ Erro: PDF não foi gerado")
                
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ OS0358 não encontrada")