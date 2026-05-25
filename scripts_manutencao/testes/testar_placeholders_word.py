"""
Script para validar todos os placeholders do modelo Word de propostas
"""
import sys
import os
from pathlib import Path
import re
import zipfile

# Adicionar pasta app ao path
sys.path.insert(0, str(Path(__file__).parent))

# Configurar Flask
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('DATABASE_URL', 'sqlite:///database/database.db')

from app.app import create_app
from app.energia_solar.catalogo_model import ProjetoSolar
from app.energia_solar.proposta_word_service import montar_contexto_proposta

app = create_app()


def extrair_placeholders_do_template(template_path):
    """Extrai todos os placeholders {{VARIAVEL}} do template Word"""
    placeholders = set()
    
    try:
        with zipfile.ZipFile(template_path, 'r') as docx_zip:
            # Arquivos XML que podem conter placeholders
            xml_files = [
                'word/document.xml',
                'word/header1.xml',
                'word/header2.xml',
                'word/footer1.xml',
                'word/footer2.xml',
            ]
            
            for xml_file in xml_files:
                try:
                    content = docx_zip.read(xml_file).decode('utf-8', errors='ignore')
                    # Buscar padrões {{VARIAVEL}} ou {VARIAVEL}
                    matches = re.findall(r'\{\{?([A-Z_0-9]+)\}?\}', content)
                    placeholders.update(matches)
                except KeyError:
                    pass  # Arquivo XML não existe no template
                    
    except Exception as e:
        print(f"❌ Erro ao ler template: {e}")
        return set()
    
    return placeholders


def testar_placeholders():
    """Testa se todos os placeholders do template têm valores"""
    
    print("=" * 80)
    print("🧪 TESTE DE PLACEHOLDERS DO MODELO WORD")
    print("=" * 80)
    print()
    
    with app.app_context():
        # Buscar um projeto real para teste
        projeto = ProjetoSolar.query.filter_by(status='ativo').first()
        
        if not projeto:
            projeto = ProjetoSolar.query.first()
        
        if not projeto:
            print("❌ Nenhum projeto encontrado no banco de dados!")
            print("   Crie um projeto antes de rodar este teste.")
            return
        
        print(f"📋 Testando com Projeto #{projeto.id}")
        print(f"   Cliente: {projeto.nome_cliente}")
        print()
        
        # Montar contexto
        print("🔧 Montando contexto de variáveis...")
        contexto = montar_contexto_proposta(projeto)
        print(f"   ✅ {len(contexto)} variáveis disponíveis no contexto")
        print()
        
        # Extrair placeholders do template
        template_path = Path(__file__).parent / 'app' / 'energia_solar' / 'templates_word' / 'proposta_solar_modelo.docx'
        
        if not template_path.exists():
            print(f"❌ Template não encontrado: {template_path}")
            return
        
        print(f"📄 Analisando template: {template_path.name}")
        placeholders_template = extrair_placeholders_do_template(template_path)
        print(f"   ✅ {len(placeholders_template)} placeholders encontrados no template")
        print()
        
        # Verificar quais placeholders estão mapeados
        print("=" * 80)
        print("📊 RESULTADO DA VALIDAÇÃO")
        print("=" * 80)
        print()
        
        mapeados = []
        nao_mapeados = []
        
        for placeholder in sorted(placeholders_template):
            if placeholder in contexto:
                valor = contexto[placeholder]
                # Verificar se o valor não está vazio
                if valor and str(valor).strip() and str(valor) != '0' and str(valor) != 'R$ 0,00':
                    mapeados.append((placeholder, valor))
                else:
                    # Valor existe mas está vazio/zero
                    nao_mapeados.append((placeholder, f"⚠️ Valor vazio/zero: {valor}"))
            else:
                nao_mapeados.append((placeholder, "❌ Não mapeado"))
        
        # Mostrar placeholders OK
        if mapeados:
            print(f"✅ PLACEHOLDERS FUNCIONANDO ({len(mapeados)}):")
            print("-" * 80)
            for ph, valor in mapeados[:10]:  # Mostrar primeiros 10
                valor_str = str(valor)[:50]  # Limitar tamanho
                print(f"   {ph:30} → {valor_str}")
            if len(mapeados) > 10:
                print(f"   ... e mais {len(mapeados) - 10} placeholders")
            print()
        
        # Mostrar placeholders com problema
        if nao_mapeados:
            print(f"⚠️ PLACEHOLDERS COM PROBLEMA ({len(nao_mapeados)}):")
            print("-" * 80)
            for ph, status in nao_mapeados:
                print(f"   {ph:30} → {status}")
            print()
        
        # Resumo
        print("=" * 80)
        print("📈 RESUMO")
        print("=" * 80)
        total = len(placeholders_template)
        ok = len(mapeados)
        problemas = len(nao_mapeados)
        
        percentual = (ok / total * 100) if total > 0 else 0
        
        print(f"   Total de placeholders no template: {total}")
        print(f"   ✅ Funcionando corretamente: {ok} ({percentual:.1f}%)")
        print(f"   ⚠️ Com problemas: {problemas}")
        print()
        
        if percentual >= 90:
            print("🎉 EXCELENTE! A maioria dos placeholders está funcionando!")
        elif percentual >= 70:
            print("👍 BOM! A maioria dos placeholders está OK, mas há alguns problemas.")
        else:
            print("⚠️ ATENÇÃO! Muitos placeholders não estão funcionando.")
        print()
        
        # Sugestões de correção
        if nao_mapeados:
            print("=" * 80)
            print("🔧 CORREÇÕES NECESSÁRIAS")
            print("=" * 80)
            print()
            print("Para corrigir os placeholders com problema:")
            print()
            print("1. Verifique se os campos estão preenchidos no projeto")
            print("2. Adicione mapeamentos em proposta_word_service.py > montar_contexto_proposta()")
            print("3. Ou ajuste os nomes dos placeholders no template Word")
            print()
        
        # Listar variáveis disponíveis mas não usadas no template
        variaveis_nao_usadas = set(contexto.keys()) - placeholders_template
        if variaveis_nao_usadas and len(variaveis_nao_usadas) > 0:
            print("=" * 80)
            print(f"💡 VARIÁVEIS DISPONÍVEIS MAS NÃO USADAS NO TEMPLATE ({len(variaveis_nao_usadas)}):")
            print("=" * 80)
            print()
            print("Estas variáveis estão no contexto mas não aparecem no template:")
            for var in sorted(list(variaveis_nao_usadas)[:15]):
                valor = contexto[var]
                valor_str = str(valor)[:50]
                print(f"   {var:30} → {valor_str}")
            if len(variaveis_nao_usadas) > 15:
                print(f"   ... e mais {len(variaveis_nao_usadas) - 15} variáveis")
            print()


if __name__ == '__main__':
    testar_placeholders()
