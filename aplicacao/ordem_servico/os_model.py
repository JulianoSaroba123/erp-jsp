# ordem_servico/os_model.py

from aplicacao.extensoes import db
from datetime import datetime, timedelta
import json

class OrdemServico(db.Model):
    __tablename__ = 'ordens_servico'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    
    # 1. Relacionamento com Cliente
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    cliente = db.relationship('Cliente', backref='ordens_servico')
    
    # 2. Dados da OS
    data_emissao = db.Column(db.Date, default=datetime.utcnow)
    previsao_conclusao = db.Column(db.Date)
    data_conclusao = db.Column(db.Date)  # Campo habilitado - coluna criada no banco
    # Novos campos
    solicitante = db.Column(db.String(100))
    contato = db.Column(db.String(100))
    
    # 3. Classificação
    tipo_servico = db.Column(db.String(50))  # Manutenção, Instalação, Reparo, etc
    prioridade = db.Column(db.String(20), default='Normal')  # Baixa, Normal, Alta, Urgente
    status = db.Column(db.String(20), default='Aberta')  # Aberta, Em Andamento, Concluída, Cancelada
    
    # 4. Responsáveis
    tecnico_responsavel = db.Column(db.String(100))
    supervisor = db.Column(db.String(100))
    
    # 5. Equipamento/Local do Serviço
    equipamento_nome = db.Column(db.String(120))
    equipamento_marca = db.Column(db.String(80))
    equipamento_modelo = db.Column(db.String(80))
    equipamento_numero_serie = db.Column(db.String(50))
    equipamento_acessorios = db.Column(db.Text)
    equipamento_problema = db.Column(db.Text)
    local_instalacao = db.Column(db.String(200))
    
    # 6. Horários
    hora_inicio = db.Column(db.Time)
    hora_termino = db.Column(db.Time)
    total_horas = db.Column(db.Float)  # Horas trabalhadas
    
    # 7. Descrição dos Trabalhos
    problema_descrito = db.Column(db.Text)  # Problema descrito pelo cliente
    descricao_problema = db.Column(db.Text)
    descricao_servico_realizado = db.Column(db.Text)
    solucao_aplicada = db.Column(db.Text)
    
    # 8. Deslocamento
    km_inicial = db.Column(db.Float)
    km_final = db.Column(db.Float)
    km_total = db.Column(db.Float)
    valor_deslocamento = db.Column(db.Float, default=0.0)
    
    # 9. Valores Financeiros
    valor_mao_obra = db.Column(db.Float, default=0.0)
    valor_produtos = db.Column(db.Float, default=0.0)
    valor_servicos = db.Column(db.Float, default=0.0)
    valor_descontos = db.Column(db.Float, default=0.0)
    valor_total = db.Column(db.Float, default=0.0)
    
    # 10. Condições de Pagamento
    forma_pagamento = db.Column(db.String(50))  # pix, dinheiro, boleto, cartao
    condicoes_pagamento = db.Column(db.String(200))
    data_vencimento = db.Column(db.Date)
    
    # 10.1 Novos campos para integração financeira
    condicao_pagamento = db.Column(db.String(50))  # 'avista' ou 'parcelado'
    qtd_parcelas = db.Column(db.Integer)  # Quantidade de parcelas
    valor_entrada = db.Column(db.Numeric(10, 2))  # Valor de entrada
    status_pagamento = db.Column(db.String(20))  # 'pendente', 'pago'
    schedule_json = db.Column(db.Text)  # JSON de cronograma personalizado

    # 9.x. Blocos JSON persistidos (usados no template/rotas)
    servicos_dados = db.Column(db.Text)     # JSON de serviços
    produtos_dados = db.Column(db.Text)     # JSON de produtos
    parcelas_json  = db.Column(db.Text)     # JSON de parcelas (novo nome)

    # 11. Observações
    observacoes_tecnico = db.Column(db.Text)
    observacoes_cliente = db.Column(db.Text)
    observacoes_internas = db.Column(db.Text)
    outras_informacoes = db.Column(db.Text)  # Campo genérico para observações

    # 12. Controle
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    

    # 13. Campos para Assinaturas/Aprovações
    assinatura_tecnico = db.Column(db.String(100))
    assinatura_cliente = db.Column(db.String(100))
    data_assinatura = db.Column(db.DateTime)

    # 14. Campos JSON para dados de serviços, produtos e parcelas
    servicos_dados = db.Column(db.Text)   # JSON string
    produtos_dados = db.Column(db.Text)   # JSON string
    parcelas_json = db.Column(db.Text)    # JSON string (renomeado de 'parcelas')
    anexos_dados = db.Column(db.Text)     # JSON string para anexos

    def __repr__(self):
        return f'<OrdemServico {self.codigo}>'
    
    def recalcular_valores(self):
        """
        Recalcula automaticamente todos os valores da OS baseado nos dados JSON
        Chamado sempre que a OS for atualizada para garantir consistência
        """
        try:
            from .os_calculos import CalculadoraOS
            import json
            
            # Carregar dados JSON
            servicos_data = json.loads(self.servicos_dados) if self.servicos_dados else []
            produtos_data = json.loads(self.produtos_dados) if self.produtos_dados else []
            
            # Preparar dados para cálculo
            dados_form = {
                'hora_inicio': self.hora_inicio.strftime('%H:%M') if self.hora_inicio else None,
                'hora_termino': self.hora_termino.strftime('%H:%M') if self.hora_termino else None,
                'km_inicial': self.km_inicial,
                'km_final': self.km_final
            }
            
            # Calcular valores
            calculos = CalculadoraOS.calcular_todos_valores(dados_form, servicos_data, produtos_data)
            
            # Atualizar valores (SEMPRE)
            self.total_horas = calculos['total_horas']
            self.km_total = calculos['km_total']
            self.valor_deslocamento = calculos['valor_deslocamento']
            self.valor_servicos = calculos['valor_servicos']
            self.valor_produtos = calculos['valor_produtos']
            self.valor_total = calculos['valor_total']
            
            print(f"[RECÁLCULO] OS {self.codigo}: Serviços={self.valor_servicos}, Produtos={self.valor_produtos}, Total={self.valor_total}")
            
        except Exception as e:
            print(f"Erro ao recalcular valores da OS {self.codigo}: {e}")
    
    def before_save(self):
        """Hook chamado antes de salvar - recalcula valores automaticamente"""
        self.recalcular_valores()
    
    def gerar_codigo(self):
        """Gera código automático para ordem de serviço"""
        ultima_os = OrdemServico.query.order_by(OrdemServico.id.desc()).first()
        if ultima_os:
            numero = int(ultima_os.codigo[2:]) + 1
        else:
            numero = 350
        return f'OS{numero:04d}'
    
    def calcular_total_horas(self):
        """Calcula total de horas trabalhadas"""
        if self.hora_inicio and self.hora_termino:
            inicio = datetime.combine(datetime.today(), self.hora_inicio)
            termino = datetime.combine(datetime.today(), self.hora_termino)
            
            # Se termino for menor que inicio, significa que passou da meia-noite
            if termino < inicio:
                termino += timedelta(days=1)
            
            diferenca = termino - inicio
            self.total_horas = diferenca.total_seconds() / 3600
            return self.total_horas
        return 0
    
    def calcular_km_total(self):
        """Calcula quilometragem total"""
        if self.km_inicial and self.km_final:
            self.km_total = self.km_final - self.km_inicial
            return self.km_total
        return 0
    
    def calcular_valor_total(self):
        """Calcula valor total da OS"""
        total = 0
        if self.valor_mao_obra:
            total += self.valor_mao_obra
        if self.valor_produtos:
            total += self.valor_produtos
        if self.valor_servicos:
            total += self.valor_servicos
        if self.valor_deslocamento:
            total += self.valor_deslocamento
        if self.valor_descontos:
            total -= self.valor_descontos
        
        self.valor_total = total
        return self.valor_total
    
    def get_status_badge_class(self):
        """Retorna classe CSS para badge de status"""
        status_classes = {
            'Aberta': 'bg-primary',
            'Em Andamento': 'bg-warning text-dark',
            'Concluída': 'bg-success',
            'Cancelada': 'bg-danger',
            'Pausada': 'bg-secondary'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def get_prioridade_badge_class(self):
        """Retorna classe CSS para badge de prioridade"""
        prioridade_classes = {
            'Baixa': 'bg-info',
            'Normal': 'bg-secondary',
            'Alta': 'bg-warning text-dark',
            'Urgente': 'bg-danger'
        }
        return prioridade_classes.get(self.prioridade, 'bg-secondary')
    
    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'cliente_nome': self.cliente.nome if self.cliente else '',
            'tipo_servico': self.tipo_servico,
            'status': self.status,
            'prioridade': self.prioridade,
            'data_emissao': self.data_emissao.strftime('%d/%m/%Y') if self.data_emissao else '',
            'valor_total': self.valor_total,
            'tecnico_responsavel': self.tecnico_responsavel
        }

    def criar_lancamento_financeiro(self):
        """
        Cria lançamento financeiro automático quando OS é concluída e paga
        """
        # Só cria lançamento se estiver concluída e paga
        if self.status != 'Concluída' or self.status_pagamento != 'pago':
            return None
            
        # Verificar se já existe lançamento para esta OS
        from aplicacao.financeiro.financeiro_model import LancamentoFinanceiro
        lancamento_existente = LancamentoFinanceiro.query.filter_by(
            categoria=f'Ordem de Serviço {self.codigo}'
        ).first()
        
        if lancamento_existente:
            return lancamento_existente  # Já existe, não cria duplicado
            
        # Criar novo lançamento financeiro
        try:
            novo_lancamento = LancamentoFinanceiro(
                tipo='Receita',
                categoria=f'Ordem de Serviço {self.codigo}',
                descricao=f'Receita da OS {self.codigo} - Cliente: {self.cliente.nome if self.cliente else "N/A"}',
                valor=float(self.valor_total or 0),
                data=datetime.now().date(),
                forma_pagamento=self.condicao_pagamento or 'N/A',
                status='Pago',
                observacoes=f'Lançamento automático gerado da OS {self.codigo}'
            )
            
            db.session.add(novo_lancamento)
            db.session.commit()
            
            print(f"DEBUG: Lançamento financeiro criado para OS {self.codigo} - Valor: R$ {self.valor_total}")
            return novo_lancamento
            
        except Exception as e:
            print(f"ERRO ao criar lançamento financeiro para OS {self.codigo}: {str(e)}")
            db.session.rollback()
            return None


# Tabela de relacionamento para itens de produtos na OS (COMENTADA TEMPORARIAMENTE)
# class OrdemServicoItem(db.Model):
#     __tablename__ = 'ordem_servico_itens'
#     
#     id = db.Column(db.Integer, primary_key=True)
#     ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
#     
#     # Tipo do item: 'produto' ou 'servico'
#     tipo_item = db.Column(db.String(20), nullable=False)
#     
#     # Referências (podem ser nulas dependendo do tipo)
#     produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'))
#     servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'))
#     
#     # Dados do item (independente se for produto ou serviço)
#     descricao = db.Column(db.String(200), nullable=False)
#     quantidade = db.Column(db.Float, nullable=False, default=1)
#     valor_unitario = db.Column(db.Float, nullable=False, default=0)
#     valor_total = db.Column(db.Float, nullable=False, default=0)
#     
#     # Relacionamentos
#     ordem_servico = db.relationship('OrdemServico', backref='itens')
#     produto = db.relationship('Produto')
#     servico = db.relationship('Servico')
#     
#     def __repr__(self):
#         return f'<OrdemServicoItem {self.descricao}>'
#     
#     def calcular_total(self):
#         """Calcula valor total do item"""
#         self.valor_total = self.quantidade * self.valor_unitario
#         return self.valor_total
