"""
Gerador de PDF Simples usando HTML + CSS
Muito mais fácil de manter e atualizar
"""

try:
    from weasyprint import HTML, CSS
    HAS_WEASYPRINT = True
    print("WeasyPrint disponivel")
except ImportError as e:
    print(f"WeasyPrint nao disponivel: {e}")
    HAS_WEASYPRINT = False
except Exception as e:
    print(f"Erro ao carregar WeasyPrint: {e}")
    HAS_WEASYPRINT = False

try:
    import pdfkit
    HAS_PDFKIT = True
    print("PDFKit disponivel")
except ImportError as e:
    print(f"PDFKit nao disponivel: {e}")
    HAS_PDFKIT = False
except Exception as e:
    print(f"Erro ao carregar PDFKit: {e}")
    HAS_PDFKIT = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
    print("ReportLab disponivel")
except ImportError as e:
    print(f"ReportLab nao disponivel: {e}")
    HAS_REPORTLAB = False
except Exception as e:
    print(f"Erro ao carregar ReportLab: {e}")
    HAS_REPORTLAB = False

from flask import render_template
import tempfile
import os
import io
from datetime import datetime
import json

class SimplePDFGenerator:
    def __init__(self):
        self.use_weasyprint = HAS_WEASYPRINT
        
    def _generate_simple_html(self, os):
        """Gera HTML usando o template pdf_os.html"""
        try:
            from flask import has_request_context, request
            context = self._prepare_context(os)
            
            # Adicionar contexto de requisição se disponível
            if has_request_context():
                context['request'] = request
            else:
                context['request'] = None
                
            # Usar template pdf_os.html
            return render_template('pdf_os.html', **context)
        except Exception as e:
            print(f"[ERROR] Erro ao renderizar template pdf_os.html: {e}")
            print(f"[ERROR] Tipo do erro: {type(e)}")
            import traceback
            traceback.print_exc()
            # Em caso de erro, usar HTML simples embutido como fallback
            valor_total = f"{os.valor_total:.2f}" if os.valor_total else "0.00"
            return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OS {os.codigo} - JSP ELÉTRICA</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #003366; }}
        .header {{ border-bottom: 1px solid #003366; padding-bottom: 10px; }}
        .content {{ margin-top: 20px; }}
        .footer {{ margin-top: 30px; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>JSP ELÉTRICA</h1>
        <h2>Ordem de Serviço: {os.codigo}</h2>
    </div>
    
    <div class="content">
        <p><strong>Cliente:</strong> {os.cliente.nome if os.cliente else "N/A"}</p>
        <p><strong>Data:</strong> {os.data_emissao.strftime('%d/%m/%Y') if os.data_emissao else "N/A"}</p>
        <p><strong>Total:</strong> R$ {valor_total}</p>
        <p><strong>Forma de Pagamento:</strong> {os.forma_pagamento or "N/A"}</p>
    </div>
    
    <div class="footer">
        <p>JSP ELÉTRICA - Juliano Saroba Pereira</p>
    </div>
</body>
</html>
"""
        
        if HAS_PDFKIT and not HAS_WEASYPRINT:
            # Configurações do wkhtmltopdf como fallback
            self.options = {
                'page-size': 'A4',
                'margin-top': '1cm',
                'margin-right': '1cm',
                'margin-bottom': '1cm',
                'margin-left': '1cm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'print-media-type': None
            }
    
    def generate_pdf(self, os, output_path=None):
        """
        Gera PDF usando template HTML
        Muito mais simples que a versão anterior!
        """
        print(f"[PDF] Iniciando geracao de PDF para OS: {os.codigo}")
        print(f"[PDF] Status bibliotecas: WeasyPrint={HAS_WEASYPRINT}, ReportLab={HAS_REPORTLAB}, PDFKit={HAS_PDFKIT}")
        
        # ESTRATÉGIA: Tentar várias abordagens em sequência para garantir que uma funcione
        
        # 1. Tentar com WeasyPrint e HTML simples
        if HAS_WEASYPRINT:
            try:
                print("[TRY] Tentando com WeasyPrint e HTML simples...")
                html_content = self._generate_simple_html(os)
                return self._generate_with_weasyprint(html_content, output_path)
            except Exception as e1:
                print(f"[ERROR] Erro com WeasyPrint e HTML simples: {e1}")
        
        # 2. Tentar com ReportLab (sem depender de HTML)
        if HAS_REPORTLAB:
            try:
                print("[TRY] Tentando com ReportLab...")
                return self._generate_with_reportlab(os, output_path)
            except Exception as e2:
                print(f"[ERROR] Erro com ReportLab: {e2}")
        
        # 3. Tentativa final: PDF ultra simples
        try:
            print("[TRY] Tentando gerar PDF ultra simples...")
            return self._generate_fallback_simple(os, output_path)
        except Exception as e3:
            print(f"[ERROR] Erro no fallback simples: {e3}")
            
            # 4. Desistir e retornar mensagem de erro
            error_message = b"Erro ao gerar PDF - Contate o administrador do sistema"
            print("[ERROR] Todos os métodos falharam. Retornando mensagem de erro.")
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(error_message)
                return output_path
            else:
                return error_message
            
        except Exception as e:
            print(f"[ERROR] Erro no reportlab: {e}")
            
            try:
                # SEGUNDO: Testar com HTML estático simples
                print("[TRY] Tentando fallback com HTML simples...")
                
                # HTML simples para teste
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OS {os.codigo} - JSP ELÉTRICA</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #003366; }}
        .header {{ border-bottom: 1px solid #003366; padding-bottom: 10px; }}
        .content {{ margin-top: 20px; }}
        .footer {{ margin-top: 30px; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>JSP ELÉTRICA</h1>
        <h2>Ordem de Serviço: {os.codigo}</h2>
    </div>
    
    <div class="content">
        <p><strong>Cliente:</strong> {os.cliente.nome if os.cliente else "N/A"}</p>
        <p><strong>Data:</strong> {os.data_emissao.strftime('%d/%m/%Y') if os.data_emissao else "N/A"}</p>
        <p><strong>Total:</strong> R$ {os.valor_total or 0:.2f}</p>
        <p><strong>Forma de Pagamento:</strong> {os.forma_pagamento or "N/A"}</p>
    </div>
    
    <div class="footer">
        <p>JSP ELÉTRICA - Juliano Saroba Pereira</p>
    </div>
</body>
</html>
"""
                print(f"[OK] Template HTML estático gerado com tamanho: {len(html_content)}")
                if self.use_weasyprint and HAS_WEASYPRINT:
                    return self._generate_with_weasyprint(html_content, output_path)
                else:
                    print("WeasyPrint não disponível")
                    raise Exception("WeasyPrint não disponível")
                    
            except Exception as e2:
                print(f"[ERROR] Erro no WeasyPrint também: {e2}")
                return self._generate_fallback_simple(os, output_path)
    
    def _generate_with_weasyprint(self, html_content, output_path):
        """Gera PDF usando WeasyPrint (recomendado)"""
        try:
            print("[TRY] Tentando gerar PDF com WeasyPrint...")
            
            # Verificar se o HTML está vazio
            if not html_content or len(html_content) < 50:
                print(f"[WARN] HTML muito curto ({len(html_content) if html_content else 0} bytes)")
                raise Exception("HTML muito curto ou vazio")
                
            try:
                html_doc = HTML(string=html_content)
                print("[OK] HTML carregado com sucesso")
            except Exception as html_error:
                print(f"[ERROR] Erro ao carregar HTML: {html_error}")
                raise
                
            # Tentativa de gerar o PDF
            if output_path:
                print(f"[DOC] Gerando PDF no arquivo: {output_path}")
                html_doc.write_pdf(output_path)
                print(f"[OK] PDF salvo em: {output_path}")
                return output_path
            else:
                print("[DOC] Gerando PDF em memória...")
                pdf_bytes = html_doc.write_pdf()
                print(f"[OK] PDF gerado: {len(pdf_bytes)} bytes")
                
                # Verificar se é PDF válido
                if pdf_bytes.startswith(b'%PDF'):
                    print(f"[OK] PDF válido! Primeiros bytes: {pdf_bytes[:20]}")
                else:
                    print(f"[ERROR] PDF inválido - primeiros bytes: {pdf_bytes[:50]}")
                    raise Exception("PDF gerado é inválido")
                    
                return pdf_bytes
                
        except Exception as e:
            print(f"[ERROR] Erro no WeasyPrint: {e}")
            raise
    
    def _generate_with_pdfkit(self, html_content, output_path):
        """Gera PDF usando pdfkit (fallback)"""
        if output_path:
            pdfkit.from_string(html_content, output_path, options=self.options)
            return output_path
        else:
            pdf_bytes = pdfkit.from_string(html_content, False, options=self.options)
            return pdf_bytes
    
    def _generate_fallback(self, html_content, output_path):
        """Fallback: retorna HTML quando PDF não está disponível"""
        print("[WARN]  Bibliotecas de PDF não disponíveis, retornando HTML")
        if output_path:
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return html_path
        else:
            return html_content.encode('utf-8')
    
    def _generate_with_reportlab(self, os, output_path):
        """Gera PDF usando reportlab (fallback confiável)"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            from io import BytesIO
            
            print("[DOC] Gerando PDF com reportlab...")
            
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # Configurações
            margin = 20 * mm
            y_pos = height - margin
            line_height = 15
            
            # Cabeçalho
            p.setFont("Helvetica-Bold", 16)
            p.drawString(margin, y_pos, "JSP ELÉTRICA")
            y_pos -= 20
            
            p.setFont("Helvetica", 12)
            p.drawString(margin, y_pos, "Juliano Saroba Pereira - Eletricista")
            y_pos -= 15
            p.drawString(margin, y_pos, "Telefone: (15) 99999-9999")
            y_pos -= 30
            
            # Título da OS
            p.setFont("Helvetica-Bold", 14)
            p.drawString(margin, y_pos, f"ORDEM DE SERVIÇO Nº {os.codigo}")
            y_pos -= 30
            
            # Dados básicos
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_pos, "DADOS BÁSICOS")
            y_pos -= 20
            
            p.setFont("Helvetica", 10)
            y_pos = self._add_field(p, margin, y_pos, "Código:", os.codigo)
            y_pos = self._add_field(p, margin, y_pos, "Data Emissão:", 
                                   os.data_emissao.strftime('%d/%m/%Y') if os.data_emissao else 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Status:", os.status or 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Prioridade:", os.prioridade or 'N/A')
            y_pos -= 15
            
            # Dados do cliente
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_pos, "DADOS DO CLIENTE")
            y_pos -= 20
            
            p.setFont("Helvetica", 10)
            y_pos = self._add_field(p, margin, y_pos, "Cliente:", 
                                   os.cliente.nome if os.cliente else 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Solicitante:", os.solicitante or 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Contato:", os.contato or 'N/A')
            y_pos -= 15
            
            # Equipamento
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_pos, "EQUIPAMENTO")
            y_pos -= 20
            
            p.setFont("Helvetica", 10)
            y_pos = self._add_field(p, margin, y_pos, "Nome:", os.equipamento_nome or 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Marca:", os.equipamento_marca or 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Modelo:", os.equipamento_modelo or 'N/A')
            y_pos -= 15
            
            # Descrição do problema
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_pos, "DESCRIÇÃO DO PROBLEMA")
            y_pos -= 20
            
            p.setFont("Helvetica", 10)
            problema = os.problema_descrito or 'Nenhuma descrição informada.'
            y_pos = self._add_text_block(p, margin, y_pos, problema, width - 2*margin)
            y_pos -= 15
            
            # Serviço realizado
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_pos, "SERVIÇO REALIZADO")
            y_pos -= 20
            
            p.setFont("Helvetica", 10)
            servico = os.descricao_servico_realizado or 'Nenhuma descrição informada.'
            y_pos = self._add_text_block(p, margin, y_pos, servico, width - 2*margin)
            y_pos -= 15
            
            # Dados de execução
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_pos, "DADOS DE EXECUÇÃO")
            y_pos -= 20
            
            p.setFont("Helvetica", 10)
            y_pos = self._add_field(p, margin, y_pos, "Técnico:", os.tecnico_responsavel or 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Hora Início:", 
                                   os.hora_inicio.strftime('%H:%M') if os.hora_inicio else 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Hora Término:", 
                                   os.hora_termino.strftime('%H:%M') if os.hora_termino else 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Total Horas:", str(os.total_horas or 'N/A'))
            y_pos -= 15
            
            # Valores
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_pos, "VALORES")
            y_pos -= 20
            
            p.setFont("Helvetica", 10)
            y_pos = self._add_field(p, margin, y_pos, "Mão de Obra:", f"R$ {os.valor_mao_obra or 0:.2f}")
            y_pos = self._add_field(p, margin, y_pos, "Produtos:", f"R$ {os.valor_produtos or 0:.2f}")
            y_pos = self._add_field(p, margin, y_pos, "Serviços:", f"R$ {os.valor_servicos or 0:.2f}")
            y_pos = self._add_field(p, margin, y_pos, "Deslocamento:", f"R$ {os.valor_deslocamento or 0:.2f}")
            
            # Total destacado
            p.setFont("Helvetica-Bold", 12)
            y_pos = self._add_field(p, margin, y_pos, "TOTAL:", f"R$ {os.valor_total or 0:.2f}")
            y_pos -= 15
            
            # Pagamento
            p.setFont("Helvetica-Bold", 12)
            p.drawString(margin, y_pos, "PAGAMENTO")
            y_pos -= 20
            
            p.setFont("Helvetica", 10)
            y_pos = self._add_field(p, margin, y_pos, "Forma:", os.forma_pagamento or 'N/A')
            y_pos = self._add_field(p, margin, y_pos, "Condições:", os.condicoes_pagamento or 'N/A')
            y_pos -= 30
            
            # Assinaturas
            p.setFont("Helvetica-Bold", 10)
            p.drawString(margin, y_pos, "Técnico: ________________________")
            p.drawString(width/2, y_pos, "Cliente: ________________________")
            y_pos -= 20
            
            p.setFont("Helvetica", 8)
            p.drawString(margin, y_pos, os.tecnico_responsavel or 'Juliano Saroba Pereira')
            p.drawString(width/2, y_pos, os.cliente.nome if os.cliente else '')
            
            p.save()
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            print(f"[OK] PDF gerado com reportlab: {len(pdf_bytes)} bytes")
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                return output_path
            else:
                return pdf_bytes
                
        except Exception as e:
            print(f"[ERROR] Erro no reportlab: {e}")
            raise
    
    def _add_field(self, canvas, x, y, label, value):
        """Adiciona um campo label: valor"""
        canvas.drawString(x, y, f"{label} {value}")
        return y - 15
    
    def _add_text_block(self, canvas, x, y, text, max_width):
        """Adiciona um bloco de texto com quebra de linha"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if canvas.stringWidth(test_line, "Helvetica", 10) < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        for line in lines:
            canvas.drawString(x, y, line)
            y -= 15
        
        return y
    
    def _generate_fallback_simple(self, os, output_path):
        """Fallback super simples"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            
            p.drawString(100, 750, f"JSP ELÉTRICA - OS {os.codigo}")
            p.drawString(100, 720, f"Cliente: {os.cliente.nome if os.cliente else 'N/A'}")
            p.drawString(100, 690, f"Data: {os.data_emissao.strftime('%d/%m/%Y') if os.data_emissao else 'N/A'}")
            p.drawString(100, 660, f"Total: R$ {os.valor_total or 0:.2f}")
            p.drawString(100, 600, f"PDF gerado em modo simplificado")
            
            p.save()
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                return output_path
            else:
                return pdf_bytes
                
        except Exception as e:
            print(f"[ERROR] Erro no fallback simples: {e}")
            return b"Erro ao gerar PDF"
        """Fallback final: usar gerador antigo"""
        try:
            # from .pdf_generator import OSPDFGenerator
            # old_generator = OSPDFGenerator()
            # if hasattr(old_generator, 'generate_pdf_bytes'):
            #     return old_generator.generate_pdf_bytes(os)
            # else:
            #     return old_generator.generate_pdf(os, output_path)
            return b"PDF antigo indisponivel - usando apenas HTML template"
        except Exception as e2:
            print(f"Erro no fallback antigo também: {e2}")
            return b"Erro ao gerar PDF"
    
    def _prepare_context(self, os):
        """Prepara os dados para o template pdf_os.html"""
        context = {
            'os': os,
            'servicos_realizados': [],
            'produtos_utilizados': [],
            'parcelas_salvas': [],
            'servicos_data': [],  # Novo para template
            'produtos_data': [],  # Novo para template
            'total_servicos': 0,
            'total_produtos': 0,
            'valor_total': 0,
            'data_geracao': datetime.now()
        }
        
        # Processar dados de serviços do JSON para formato esperado pelo template
        total_servicos_calculado = 0
        if hasattr(os, 'servicos_dados') and os.servicos_dados:
            try:
                servicos_json = json.loads(os.servicos_dados) if isinstance(os.servicos_dados, str) else os.servicos_dados
                for servico in servicos_json:
                    valor_total_servico = float(servico.get('valor_total', 0))
                    # Formato para template antigo (manter compatibilidade)
                    context['servicos_realizados'].append({
                        'nome': servico.get('nome', ''),
                        'qtd_horas': float(servico.get('quantidade', 0)),
                        'valor': valor_total_servico / max(float(servico.get('quantidade', 1)), 1),  # valor unitário
                        'valor_total': valor_total_servico
                    })
                    # Formato para novo template
                    context['servicos_data'].append({
                        'nome': servico.get('nome', ''),
                        'descricao': servico.get('descricao', ''),
                        'quantidade': servico.get('quantidade', 1),
                        'valor_unitario': servico.get('valor_unitario') or servico.get('valor_hora', 0),  # Compatibilidade com valor_hora
                        'valor_total': valor_total_servico
                    })
                    total_servicos_calculado += valor_total_servico
            except Exception as e:
                print(f"Erro ao processar servicos_dados: {e}")
        
        # Processar dados de produtos do JSON para formato esperado pelo template
        total_produtos_calculado = 0
        if hasattr(os, 'produtos_dados') and os.produtos_dados:
            try:
                produtos_json = json.loads(os.produtos_dados) if isinstance(os.produtos_dados, str) else os.produtos_dados
                for produto in produtos_json:
                    valor_total_produto = float(produto.get('valor_total', 0))
                    # Formato para template antigo (manter compatibilidade)
                    context['produtos_utilizados'].append({
                        'nome': produto.get('nome', ''),
                        'quantidade': int(produto.get('quantidade', 0)),
                        'valor_unitario': float(produto.get('valor_unitario', 0)),
                        'valor_total': valor_total_produto
                    })
                    # Formato para novo template
                    context['produtos_data'].append({
                        'nome': produto.get('nome', ''),
                        'descricao': produto.get('descricao', ''),
                        'quantidade': produto.get('quantidade', 1),
                        'valor_unitario': produto.get('valor_unitario', 0),
                        'valor_total': valor_total_produto
                    })
                    total_produtos_calculado += valor_total_produto
            except Exception as e:
                print(f"Erro ao processar produtos_dados: {e}")
        
        # Processar parcelas do JSON se existir
        if hasattr(os, 'parcelas_json') and os.parcelas_json:
            try:
                parcelas_json = json.loads(os.parcelas_json) if isinstance(os.parcelas_json, str) else os.parcelas_json
                if isinstance(parcelas_json, list):
                    for parcela in parcelas_json:
                        context['parcelas_salvas'].append({
                            'vencimento': parcela.get('vencimento', ''),
                            'valor': float(parcela.get('valor', 0)),
                            'situacao': parcela.get('situacao', 'Em aberto')
                        })
            except Exception as e:
                print(f"Erro ao processar parcelas_json: {e}")
        
        # Usar os totais calculados corretamente da soma dos itens
        context['total_servicos'] = total_servicos_calculado
        context['total_produtos'] = total_produtos_calculado
        
        # Calcular o valor total correto
        valor_deslocamento = float(os.valor_deslocamento or 0) if hasattr(os, 'valor_deslocamento') else 0
        context['valor_total'] = total_servicos_calculado + total_produtos_calculado + valor_deslocamento
        
        # Processar anexos para o PDF
        context['anexos_salvos'] = []
        if hasattr(os, 'anexos_dados') and os.anexos_dados:
            try:
                anexos_json = json.loads(os.anexos_dados) if isinstance(os.anexos_dados, str) else os.anexos_dados
                for anexo in anexos_json:
                    # Adicionar informações formatadas do anexo
                    context['anexos_salvos'].append({
                        'nome_arquivo': anexo.get('nome_arquivo', ''),
                        'nome_original': anexo.get('nome_original', anexo.get('nome_arquivo', '')),
                        'tamanho': anexo.get('tamanho', 0),
                        'tamanho_formatado': anexo.get('tamanho_formatado', 'N/A'),
                        'data_upload': anexo.get('data_upload', ''),
                        'tipo_arquivo': anexo.get('tipo_arquivo', 'documento')
                    })
                print(f"DEBUG PDF: {len(context['anexos_salvos'])} anexos incluídos no contexto")
            except Exception as e:
                print(f"Erro ao processar anexos_dados para PDF: {e}")
                context['anexos_salvos'] = []
        
        # Debug
        print(f"=== DEBUG PDF RELATORIO_CLIENTE_PRINT - OS {os.codigo} ===")
        print(f"Servicos realizados: {len(context['servicos_realizados'])}")
        print(f"Produtos utilizados: {len(context['produtos_utilizados'])}")
        print(f"Parcelas: {len(context['parcelas_salvas'])}")
        print(f"Valor total: R$ {context['valor_total']}")
        print(f"=== FIM DEBUG ===")
        
        return context

# Para compatibilidade com código existente
class OSPDFGenerator(SimplePDFGenerator):
    """Alias para manter compatibilidade"""
    pass
