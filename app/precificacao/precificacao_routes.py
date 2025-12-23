from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from app.extensoes import db
from .precificacao_model import ConfigPrecificacao
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

precificacao_bp = Blueprint(
    "precificacao", __name__, template_folder="templates", url_prefix="/precificacao"
)

def converter_valor_monetario(valor_str):
    """Converte string monetária brasileira para float."""
    if not valor_str:
        return 0.0
    # Remove espaços e converte vírgula para ponto
    valor_limpo = str(valor_str).strip().replace(',', '.')
    try:
        return float(valor_limpo)
    except (ValueError, TypeError):
        return 0.0

@precificacao_bp.route("/")
def index():
    """Página principal - redireciona para calculadora."""
    return redirect(url_for('precificacao.calculadora'))

@precificacao_bp.route("/calculadora", methods=["GET", "POST"])
def calculadora():
    """
    Formulário avançado de precificação com todos os parâmetros detalhados.
    """
    try:
        if request.method == "GET":
            # Buscar última configuração para reutilizar valores
            config_atual = ConfigPrecificacao.query.order_by(
                ConfigPrecificacao.data_simulacao.desc()
            ).first()
            
            return render_template(
                "precificacao/calculadora.html",
                config=config_atual
            )
        
        # POST - Processar dados do formulário
        logger.debug("Processando formulário de precificação...")
        
        # Validar dados obrigatórios
        nome_simulacao = request.form.get('nome_simulacao', 'Simulação').strip()
        if not nome_simulacao:
            nome_simulacao = f'Simulação {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        
        # Criar nova configuração
        nova_config = ConfigPrecificacao(
            nome_simulacao=nome_simulacao,
            
            # Custos fixos
            custo_aluguel=converter_valor_monetario(request.form.get('custo_aluguel', 0)),
            custo_energia=converter_valor_monetario(request.form.get('custo_energia', 0)),
            custo_internet=converter_valor_monetario(request.form.get('custo_internet', 0)),
            custo_contabilidade=converter_valor_monetario(request.form.get('custo_contabilidade', 0)),
            custo_impostos=converter_valor_monetario(request.form.get('custo_impostos', 0)),
            custo_seguros=converter_valor_monetario(request.form.get('custo_seguros', 0)),
            custo_financiamento=converter_valor_monetario(request.form.get('custo_financiamento', 0)),
            custo_outros_fixos=converter_valor_monetario(request.form.get('custo_outros_fixos', 0)),
            
            # Custos variáveis
            custo_combustivel=converter_valor_monetario(request.form.get('custo_combustivel', 0)),
            custo_ferramentas=converter_valor_monetario(request.form.get('custo_ferramentas', 0)),
            custo_materiais=converter_valor_monetario(request.form.get('custo_materiais', 0)),
            custo_comissoes=converter_valor_monetario(request.form.get('custo_comissoes', 0)),
            custo_marketing=converter_valor_monetario(request.form.get('custo_marketing', 0)),
            custo_manutencao=converter_valor_monetario(request.form.get('custo_manutencao', 0)),
            custo_outros_variaveis=converter_valor_monetario(request.form.get('custo_outros_variaveis', 0)),
            
            # Colaboradores
            colaboradores_fixos_qtd=int(request.form.get('colaboradores_fixos_qtd', 0)),
            salario_medio_fixo=converter_valor_monetario(request.form.get('salario_medio_fixo', 0)),
            colaboradores_diaristas_qtd=int(request.form.get('colaboradores_diaristas_qtd', 0)),
            valor_diaria=converter_valor_monetario(request.form.get('valor_diaria', 0)),
            dias_trabalhados_mes=int(request.form.get('dias_trabalhados_mes', 0)),
            
            # Produtividade
            horas_mensais_colaborador=float(request.form.get('horas_mensais_colaborador', 160)),
            colaboradores_produtivos=int(request.form.get('colaboradores_produtivos', 1)),
            
            # Margem e parâmetros de cálculo
            margem_lucro_percentual=float(request.form.get('margem_lucro_percentual', 30)),
            percentual_encargos=float(request.form.get('percentual_encargos', 80)),
            percentual_impostos=float(request.form.get('percentual_impostos', 13.33)),
            horas_improdutivas_percentual=float(request.form.get('horas_improdutivas_percentual', 20)),
            
            # Observações
            observacoes=request.form.get('observacoes', '').strip()
        )
        
        # Executar cálculos
        nova_config.calcular_precificacao()
        
        # Salvar no banco
        db.session.add(nova_config)
        db.session.commit()
        
        logger.debug(f"Nova configuração criada: {nova_config.id}")
        flash('Precificação calculada com sucesso!', 'success')
        
        return redirect(url_for('precificacao.resultado', id=nova_config.id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao processar precificação: {str(e)}")
        flash(f'Erro ao calcular precificação: {str(e)}', 'error')
        return redirect(url_for('precificacao.calculadora'))

@precificacao_bp.route("/resultado/<int:id>")
def resultado(id):
    """Exibe os resultados da precificação em cards visuais com gráficos."""
    try:
        config = ConfigPrecificacao.query.get_or_404(id)
        
        # Preparar dados para gráficos
        dados_grafico = config.get_dados_grafico()
        resumo_custos = config.get_resumo_custos()
        
        return render_template(
            "precificacao/resultado.html",
            resultado=config,  # Mudança aqui: resultado ao invés de config
            config=config,
            dados_grafico=dados_grafico,
            resumo_custos=resumo_custos
        )
        
    except Exception as e:
        logger.error(f"Erro ao exibir resultado {id}: {str(e)}")
        flash(f'Erro ao carregar resultado: {str(e)}', 'error')
        return redirect(url_for('precificacao.calculadora'))

@precificacao_bp.route("/historico")
def historico():
    """Lista das simulações anteriores."""
    try:
        simulacoes = ConfigPrecificacao.query.filter_by(ativo=True).order_by(
            ConfigPrecificacao.data_simulacao.desc()
        ).limit(20).all()
        
        return render_template(
            "precificacao/historico.html",
            simulacoes=simulacoes
        )
        
    except Exception as e:
        logger.error(f"Erro ao carregar histórico: {str(e)}")
        flash(f'Erro ao carregar histórico: {str(e)}', 'error')
        return redirect(url_for('precificacao.calculadora'))

@precificacao_bp.route("/excluir/<int:id>", methods=['POST'])
def excluir_simulacao(id):
    """Exclui uma simulação (soft delete)."""
    try:
        config = ConfigPrecificacao.query.get_or_404(id)
        config.ativo = False
        db.session.commit()
        
        flash('Simulação excluída com sucesso!', 'success')
        return redirect(url_for('precificacao.historico'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir simulação {id}: {str(e)}")
        flash(f'Erro ao excluir simulação: {str(e)}', 'error')
        return redirect(url_for('precificacao.historico'))

@precificacao_bp.route("/api/dados-grafico/<int:id>")
def api_dados_grafico(id):
    """API para fornecer dados do gráfico via AJAX."""
    try:
        config = ConfigPrecificacao.query.get_or_404(id)
        dados = config.get_dados_grafico()
        
        return jsonify(dados)
        
    except Exception as e:
        logger.error(f"Erro na API de dados gráfico {id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@precificacao_bp.route("/pdf/<int:id>")
def gerar_pdf(id):
    """Gera PDF com relatório detalhado da precificação."""
    try:
        config = ConfigPrecificacao.query.get_or_404(id)
        resumo_custos = config.get_resumo_custos()
        
        # Tentar importar WeasyPrint
        try:
            import weasyprint
            
            # Renderizar template HTML
            html_content = render_template(
                'precificacao/pdf_relatorio.html',
                config=config,
                resumo_custos=resumo_custos
            )
            
            # Gerar PDF
            pdf = weasyprint.HTML(string=html_content).write_pdf()
            
            # Criar resposta
            response = make_response(pdf)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=precificacao_{config.id}.pdf'
            
            return response
            
        except ImportError:
            # WeasyPrint não disponível - retornar HTML
            logger.warning("WeasyPrint não encontrado - retornando HTML")
            flash('Biblioteca PDF não disponível - exibindo versão HTML', 'warning')
            return render_template(
                'precificacao/pdf_relatorio.html',
                config=config,
                resumo_custos=resumo_custos
            )
            
    except Exception as e:
        logger.error(f"Erro ao gerar PDF da precificação {id}: {str(e)}")
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('precificacao.resultado', id=id))


@precificacao_bp.route("/dashboard")
def dashboard():
    """Rota de compatibilidade - redireciona para a página principal de cálculo."""
    from flask import redirect, url_for
    return redirect(url_for('precificacao.calculadora'))