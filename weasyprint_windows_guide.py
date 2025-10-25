# -*- coding: utf-8 -*-
"""
Guia de Instalação WeasyPrint Windows
===================================

Instala WeasyPrint com todas as dependências necessárias no Windows.

IMPORTANTE: WeasyPrint no Windows requer GTK3+ que é complexo de instalar.
Para produção, recomendamos usar Docker ou Linux.

Alternativas mais simples:
1. Usar o template HTML (já funcionando) 
2. Usar bibliotecas como ReportLab ou fpdf
3. Usar serviços online como Puppeteer/Chrome headless
"""

def install_weasyprint_windows():
    """Guia de instalação do WeasyPrint no Windows."""
    
    print("=" * 60)
    print("🚀 JSP ERP v3.0 - Instalação WeasyPrint Windows")
    print("=" * 60)
    
    print("\n📋 OPÇÕES DISPONÍVEIS:")
    print("\n1. 💻 USANDO TEMPLATE HTML (RECOMENDADO)")
    print("   ✅ Já funcionando")
    print("   ✅ Não requer dependências extras") 
    print("   ✅ Compatível com todos os navegadores")
    print("   ✅ Pode ser salvo como PDF pelo navegador")
    
    print("\n2. 🐳 USANDO DOCKER (PARA PRODUÇÃO)")
    print("   - Instalar Docker Desktop")
    print("   - Criar Dockerfile com WeasyPrint")
    print("   - Mais estável e confiável")
    
    print("\n3. 🔧 INSTALAÇÃO MANUAL WINDOWS (COMPLEXA)")
    print("   - Instalar GTK3+ for Windows")
    print("   - Instalar Cairo, Pango, GObject")
    print("   - Configurar variáveis de ambiente")
    print("   - Pode ter conflitos")
    
    print("\n4. ☁️ SERVIÇO EXTERNO (ALTERNATIVA)")
    print("   - Puppeteer + Chrome headless")
    print("   - APIs de conversão HTML→PDF")
    print("   - Mais simples e confiável")
    
    print("\n" + "=" * 60)
    print("✅ SOLUÇÃO ATUAL: Template HTML funcionando!")
    print("Os usuários podem:")
    print("  • Visualizar o relatório completo")
    print("  • Imprimir diretamente do navegador")
    print("  • Salvar como PDF usando Ctrl+P → 'Salvar como PDF'")
    print("  • Funciona em qualquer dispositivo")
    print("=" * 60)

if __name__ == '__main__':
    install_weasyprint_windows()