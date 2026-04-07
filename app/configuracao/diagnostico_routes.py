"""
Rotas de diagnóstico para debug de configuração e logo
"""
from flask import Blueprint, jsonify
from app.extensoes import db
from app.configuracao.configuracao_model import Configuracao

bp_diagnostico = Blueprint('diagnostico_config', __name__)


@bp_diagnostico.route('/diagnostico/config')
def diagnostico_config():
    """
    Rota de diagnóstico para verificar configuração e logo.
    Retorna informações detalhadas sobre o estado atual.
    """
    try:
        config = Configuracao.get_solo()
        
        resultado = {
            'status': 'success',
            'config_encontrada': config is not None,
            'dados': {}
        }
        
        if config:
            # Dados básicos
            resultado['dados']['id'] = config.id
            resultado['dados']['nome_fantasia'] = config.nome_fantasia
            resultado['dados']['razao_social'] = config.razao_social
            resultado['dados']['cnpj'] = config.cnpj
            
            # Informações da logo
            resultado['dados']['tem_logo_base64'] = bool(config.logo_base64)
            
            if config.logo_base64:
                # Analisar logo base64
                logo_len = len(config.logo_base64)
                primeiros_50 = config.logo_base64[:50]
                
                resultado['dados']['logo'] = {
                    'tamanho': logo_len,
                    'tamanho_kb': round(logo_len / 1024, 2),
                    'primeiros_50_chars': primeiros_50,
                    'tem_prefixo_data_uri': config.logo_base64.startswith('data:image'),
                    'formato_detectado': 'Desconhecido'
                }
                
                # Detectar formato
                if config.logo_base64.startswith('data:image/png'):
                    resultado['dados']['logo']['formato_detectado'] = 'PNG'
                elif config.logo_base64.startswith('data:image/jpeg') or config.logo_base64.startswith('data:image/jpg'):
                    resultado['dados']['logo']['formato_detectado'] = 'JPEG'
                elif config.logo_base64.startswith('data:image/gif'):
                    resultado['dados']['logo']['formato_detectado'] = 'GIF'
                elif config.logo_base64.startswith('/9j/'):
                    resultado['dados']['logo']['formato_detectado'] = 'JPEG (sem prefixo)'
                    resultado['dados']['logo']['PROBLEMA'] = 'Logo sem prefixo data:image - execute /configuracao/fix-logo-base64'
                elif config.logo_base64.startswith('iVBOR'):
                    resultado['dados']['logo']['formato_detectado'] = 'PNG (sem prefixo)'
                    resultado['dados']['logo']['PROBLEMA'] = 'Logo sem prefixo data:image - execute /configuracao/fix-logo-base64'
                
                # Validações
                if not config.logo_base64.startswith('data:image'):
                    resultado['dados']['logo']['status'] = 'ERRO: Logo sem prefixo data URI'
                    resultado['dados']['logo']['solucao'] = 'Acesse: /configuracao/fix-logo-base64'
                else:
                    resultado['dados']['logo']['status'] = 'OK: Logo no formato correto'
            else:
                resultado['dados']['logo'] = {
                    'status': 'ERRO: Logo não configurada',
                    'solucao': 'Faça upload da logo em /configuracao/'
                }
            
            # Campo logo (arquivo)
            resultado['dados']['tem_logo_arquivo'] = bool(config.logo)
            if config.logo:
                resultado['dados']['logo_arquivo_path'] = config.logo
        else:
            resultado['status'] = 'error'
            resultado['message'] = 'Configuração não encontrada no banco de dados'
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Erro ao diagnosticar: {str(e)}'
        }), 500


@bp_diagnostico.route('/diagnostico/logo-preview')
def logo_preview():
    """
    Página HTML simples para visualizar a logo atual.
    """
    try:
        config = Configuracao.get_solo()
        
        if not config or not config.logo_base64:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Preview Logo - ERP JSP</title>
                <style>
                    body { font-family: Arial; background: #0a1929; color: #fff; padding: 40px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .error { background: #dc3545; color: white; padding: 20px; border-radius: 10px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔴 Logo não encontrada</h1>
                    <div class="error">
                        <p>A logo não está configurada no banco de dados.</p>
                        <p><strong>Solução:</strong> Acesse <a href="/configuracao/" style="color: #ffc107;">/configuracao/</a> e faça upload da logo.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        tem_prefixo = config.logo_base64.startswith('data:image')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Preview Logo - ERP JSP</title>
            <style>
                body {{ font-family: Arial; background: #0a1929; color: #fff; padding: 40px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .preview {{ background: white; padding: 30px; border-radius: 10px; text-align: center; margin: 20px 0; }}
                .info {{ background: #1a2d42; padding: 20px; border-radius: 10px; margin: 10px 0; }}
                .success {{ background: #28a745; color: white; padding: 15px; border-radius: 5px; }}
                .warning {{ background: #ffc107; color: #000; padding: 15px; border-radius: 5px; }}
                img {{ max-width: 300px; max-height: 300px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🖼️ Preview da Logo - ERP JSP</h1>
                
                <div class="info">
                    <h3>Informações:</h3>
                    <p><strong>Empresa:</strong> {config.nome_fantasia}</p>
                    <p><strong>Tamanho:</strong> {len(config.logo_base64)} caracteres ({round(len(config.logo_base64)/1024, 2)} KB)</p>
                    <p><strong>Prefixo correto:</strong> {'✅ SIM' if tem_prefixo else '❌ NÃO'}</p>
                    <p><strong>Primeiros 50 chars:</strong> <code>{config.logo_base64[:50]}</code></p>
                </div>
                
                {'<div class="success"><strong>✅ Logo está no formato correto!</strong></div>' if tem_prefixo else '<div class="warning"><strong>⚠️ Logo SEM prefixo data URI!</strong><br>Execute: <a href="/configuracao/fix-logo-base64">/configuracao/fix-logo-base64</a></div>'}
                
                <div class="preview">
                    <h3>Preview:</h3>
                    <img src="{config.logo_base64}" alt="Logo" 
                         onerror="this.onerror=null; this.innerHTML='❌ ERRO: Logo não pode ser exibida';">
                </div>
                
                <div class="info">
                    <h3>Ações:</h3>
                    <p><a href="/configuracao/" style="color: #00d4ff;">➡️ Configurações</a></p>
                    <p><a href="/configuracao/fix-logo-base64" style="color: #00d4ff;">🔧 Corrigir Logo (JSON)</a></p>
                    <p><a href="/diagnostico/config" style="color: #00d4ff;">📊 Diagnóstico Completo (JSON)</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Erro</title></head>
        <body style="font-family: Arial; padding: 40px; background: #0a1929; color: #fff;">
            <h1>❌ Erro</h1>
            <p>{str(e)}</p>
        </body>
        </html>
        """, 500
