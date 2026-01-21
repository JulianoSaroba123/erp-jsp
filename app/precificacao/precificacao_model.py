from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Boolean
from app.extensoes import db
from datetime import datetime

class ConfigPrecificacao(db.Model):
    """Modelo para armazenar configurações e simulações de precificação."""
    
    __tablename__ = 'config_precificacao'
    
    id = Column(Integer, primary_key=True)
    
    # Metadados da simulação
    nome_simulacao = Column(String(100), nullable=False, default='Simulação')
    data_simulacao = Column(DateTime, default=datetime.utcnow)
    
    # Custos Fixos Mensais
    custo_aluguel = Column(Float, default=0.0)
    custo_energia = Column(Float, default=0.0)
    custo_internet = Column(Float, default=0.0)
    custo_contabilidade = Column(Float, default=0.0)
    custo_impostos = Column(Float, default=0.0)
    custo_seguros = Column(Float, default=0.0)
    custo_financiamento = Column(Float, default=0.0)
    custo_outros_fixos = Column(Float, default=0.0)
    
    # Custos Variáveis Mensais
    custo_combustivel = Column(Float, default=0.0)
    custo_ferramentas = Column(Float, default=0.0)
    custo_materiais = Column(Float, default=0.0)
    custo_comissoes = Column(Float, default=0.0)
    custo_marketing = Column(Float, default=0.0)
    custo_manutencao = Column(Float, default=0.0)
    custo_outros_variaveis = Column(Float, default=0.0)
    
    # Mão de Obra Fixa
    colaboradores_fixos_qtd = Column(Integer, default=0)
    salario_medio_fixo = Column(Float, default=0.0)
    
    # Mão de Obra Diarista
    colaboradores_diaristas_qtd = Column(Integer, default=0)
    valor_diaria = Column(Float, default=0.0)
    dias_trabalhados_mes = Column(Integer, default=0)
    
    # Parâmetros de Produtividade
    horas_mensais_colaborador = Column(Float, default=160.0)  # 8h x 20 dias
    colaboradores_produtivos = Column(Integer, default=1)
    
    # Margem e Estratégia
    margem_lucro_percentual = Column(Float, default=30.0)
    percentual_encargos = Column(Float, default=80.0)  # Encargos trabalhistas (INSS, FGTS, férias, 13º)
    percentual_impostos = Column(Float, default=13.33)  # Simples Nacional (média)
    horas_improdutivas_percentual = Column(Float, default=20.0)  # Tempo perdido, administrativo, etc
    
    # === CAMPOS AVANÇADOS - CONSULTORIA FINANCEIRA ===
    
    # Gestão de Riscos
    percentual_inadimplencia = Column(Float, default=5.0)  # % de calote histórico
    reserva_tecnica_percentual = Column(Float, default=3.0)  # Fundo de reserva para imprevistos
    
    # Análise de Investimento
    capital_investido = Column(Float, default=0.0)  # Capital inicial investido no negócio
    roi_desejado_anual = Column(Float, default=20.0)  # ROI esperado por ano (%)
    
    # Gestão de Capacidade
    percentual_utilizacao_esperada = Column(Float, default=70.0)  # % de horas que espera vender
    
    # Análise de Mercado
    preco_mercado_hora = Column(Float, default=0.0)  # Preço médio do mercado/concorrência
    preco_mercado_dia = Column(Float, default=0.0)
    estrategia_pricing = Column(String(50), default='competitivo')  # competitivo, premium, penetracao
    
    # Precificação por Complexidade
    multiplicador_simples = Column(Float, default=0.8)  # Serviço simples = 80% do preço base
    multiplicador_medio = Column(Float, default=1.0)  # Serviço médio = 100%
    multiplicador_complexo = Column(Float, default=1.3)  # Serviço complexo = 130%
    multiplicador_urgente = Column(Float, default=1.5)  # Urgência = +50%
    
    # === RESULTADOS CALCULADOS ===
    total_custos_fixos = Column(Float, default=0.0)
    total_custos_variaveis = Column(Float, default=0.0)
    total_custo_fixo_colaboradores = Column(Float, default=0.0)
    total_custo_diaristas = Column(Float, default=0.0)
    custo_total_mensal = Column(Float, default=0.0)
    
    # Valores Base
    valor_hora_base = Column(Float, default=0.0)
    valor_hora_final = Column(Float, default=0.0)
    valor_dia_final = Column(Float, default=0.0)
    valor_empreita_final = Column(Float, default=0.0)
    
    # Ponto de Equilíbrio
    horas_ponto_equilibrio = Column(Float, default=0.0)
    faturamento_ponto_equilibrio = Column(Float, default=0.0)
    
    # Análise de Cenários
    valor_hora_otimista = Column(Float, default=0.0)  # 90% utilização
    valor_hora_realista = Column(Float, default=0.0)  # Utilização esperada
    valor_hora_pessimista = Column(Float, default=0.0)  # 50% utilização
    
    # Precificação por Complexidade (calculados)
    valor_hora_simples = Column(Float, default=0.0)
    valor_hora_medio = Column(Float, default=0.0)
    valor_hora_complexo = Column(Float, default=0.0)
    valor_hora_urgente = Column(Float, default=0.0)
    
    # Indicadores Financeiros
    markup_percentual = Column(Float, default=0.0)
    margem_contribuicao = Column(Float, default=0.0)
    roi_mensal_calculado = Column(Float, default=0.0)
    
    # Campos Auxiliares
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
    
    def calcular_precificacao(self):
        """
        Executa todos os cálculos de precificação PROFISSIONAL.
        Inclui: ponto de equilíbrio, análise de cenários, ROI, precificação dinâmica.
        """
        
        # ===================================================================
        # ETAPA 1: CALCULAR CUSTOS TOTAIS
        # ===================================================================
        
        self.total_custos_fixos = (
            self.custo_aluguel + 
            self.custo_energia + 
            self.custo_internet + 
            self.custo_contabilidade + 
            self.custo_impostos + 
            self.custo_seguros + 
            self.custo_financiamento + 
            self.custo_outros_fixos
        )
        
        self.total_custos_variaveis = (
            self.custo_combustivel + 
            self.custo_ferramentas + 
            self.custo_materiais + 
            self.custo_comissoes + 
            self.custo_marketing + 
            self.custo_manutencao + 
            self.custo_outros_variaveis
        )
        
        # Custos de colaboradores COM ENCARGOS
        custo_fixos_bruto = self.colaboradores_fixos_qtd * self.salario_medio_fixo
        self.total_custo_fixo_colaboradores = custo_fixos_bruto * (1 + self.percentual_encargos / 100)
        
        custo_diaristas_bruto = (
            self.colaboradores_diaristas_qtd * 
            self.valor_diaria * 
            self.dias_trabalhados_mes
        )
        self.total_custo_diaristas = custo_diaristas_bruto * (1 + self.percentual_encargos / 100)
        
        # Custo total mensal
        self.custo_total_mensal = (
            self.total_custos_fixos + 
            self.total_custos_variaveis + 
            self.total_custo_fixo_colaboradores + 
            self.total_custo_diaristas
        )
        
        # ===================================================================
        # ETAPA 2: ADICIONAR CUSTO DE OPORTUNIDADE (ROI)
        # ===================================================================
        
        # Custo de oportunidade mensal = capital investido * ROI anual / 12
        if self.capital_investido > 0 and self.roi_desejado_anual > 0:
            custo_oportunidade_mensal = (self.capital_investido * self.roi_desejado_anual / 100) / 12
            self.custo_total_mensal += custo_oportunidade_mensal
        
        # ===================================================================
        # ETAPA 3: CAPACIDADE E HORAS DISPONÍVEIS
        # ===================================================================
        
        total_horas_teoricas = self.colaboradores_produtivos * self.horas_mensais_colaborador
        total_horas_produtivas = total_horas_teoricas * (1 - self.horas_improdutivas_percentual / 100)
        
        # Horas que espera realmente vender (utilização esperada)
        horas_venda_esperada = total_horas_produtivas * (self.percentual_utilizacao_esperada / 100)
        
        # ===================================================================
        # ETAPA 4: PONTO DE EQUILÍBRIO (BEP - Break Even Point)
        # ===================================================================
        
        if total_horas_produtivas > 0:
            # Ponto de equilíbrio: quantas horas precisa vender para cobrir custos
            self.horas_ponto_equilibrio = self.custo_total_mensal / (
                self.custo_total_mensal / total_horas_produtivas
            )
            
            # Faturamento mínimo necessário
            custo_hora_puro = self.custo_total_mensal / total_horas_produtivas
            self.faturamento_ponto_equilibrio = self.custo_total_mensal
        else:
            self.horas_ponto_equilibrio = 0.0
            self.faturamento_ponto_equilibrio = 0.0
        
        # ===================================================================
        # ETAPA 5: CÁLCULO DE VALOR/HORA COM RATEIO INTELIGENTE
        # ===================================================================
        
        if horas_venda_esperada > 0:
            # Valor hora base: rateio de custos pelas horas que ESPERA vender
            self.valor_hora_base = self.custo_total_mensal / horas_venda_esperada
            
            # ===================================================================
            # ETAPA 6: ADICIONAR PROTEÇÕES E MARGENS
            # ===================================================================
            
            # 6.1 - Adicionar margem de lucro
            valor_com_lucro = self.valor_hora_base * (1 + self.margem_lucro_percentual / 100)
            
            # 6.2 - Adicionar reserva para inadimplência
            valor_com_inadimplencia = valor_com_lucro / (1 - self.percentual_inadimplencia / 100)
            
            # 6.3 - Adicionar reserva técnica (fundo de emergência)
            valor_com_reserva = valor_com_inadimplencia / (1 - self.reserva_tecnica_percentual / 100)
            
            # 6.4 - Adicionar impostos sobre venda (gross-up)
            self.valor_hora_final = valor_com_reserva / (1 - self.percentual_impostos / 100)
            
            # ===================================================================
            # ETAPA 7: CALCULAR MARKUP E MARGEM DE CONTRIBUIÇÃO
            # ===================================================================
            
            if self.valor_hora_base > 0:
                self.markup_percentual = ((self.valor_hora_final - self.valor_hora_base) / self.valor_hora_base) * 100
                
            # Margem de contribuição = (Preço - Custo Variável) / Preço
            custo_variavel_hora = self.total_custos_variaveis / horas_venda_esperada if horas_venda_esperada > 0 else 0
            if self.valor_hora_final > 0:
                self.margem_contribuicao = ((self.valor_hora_final - custo_variavel_hora) / self.valor_hora_final) * 100
            
        else:
            self.valor_hora_base = 0.0
            self.valor_hora_final = 0.0
            self.markup_percentual = 0.0
            self.margem_contribuicao = 0.0
        
        # ===================================================================
        # ETAPA 8: ANÁLISE DE CENÁRIOS (OTIMISTA, REALISTA, PESSIMISTA)
        # ===================================================================
        
        if total_horas_produtivas > 0:
            # CENÁRIO OTIMISTA: 90% de utilização
            horas_otimista = total_horas_produtivas * 0.90
            self.valor_hora_otimista = self._calcular_valor_hora_cenario(horas_otimista)
            
            # CENÁRIO REALISTA: utilização esperada
            self.valor_hora_realista = self.valor_hora_final
            
            # CENÁRIO PESSIMISTA: 50% de utilização
            horas_pessimista = total_horas_produtivas * 0.50
            self.valor_hora_pessimista = self._calcular_valor_hora_cenario(horas_pessimista)
        
        # ===================================================================
        # ETAPA 9: PRECIFICAÇÃO POR COMPLEXIDADE
        # ===================================================================
        
        self.valor_hora_simples = self.valor_hora_final * self.multiplicador_simples
        self.valor_hora_medio = self.valor_hora_final * self.multiplicador_medio
        self.valor_hora_complexo = self.valor_hora_final * self.multiplicador_complexo
        self.valor_hora_urgente = self.valor_hora_final * self.multiplicador_urgente
        
        # ===================================================================
        # ETAPA 10: VALORES DIÁRIA E EMPREITA
        # ===================================================================
        
        self.valor_dia_final = self.valor_hora_final * 8
        self.valor_empreita_final = self.valor_dia_final * 10
        
        # ===================================================================
        # ETAPA 11: CALCULAR ROI REAL DO PERÍODO
        # ===================================================================
        
        if self.capital_investido > 0 and horas_venda_esperada > 0:
            faturamento_esperado = self.valor_hora_final * horas_venda_esperada
            lucro_liquido_mensal = faturamento_esperado - self.custo_total_mensal
            self.roi_mensal_calculado = (lucro_liquido_mensal / self.capital_investido) * 100
        else:
            self.roi_mensal_calculado = 0.0
    
    def _calcular_valor_hora_cenario(self, horas_disponiveis):
        """Calcula valor/hora para um cenário específico de utilização."""
        if horas_disponiveis <= 0:
            return 0.0
            
        valor_base = self.custo_total_mensal / horas_disponiveis
        valor_lucro = valor_base * (1 + self.margem_lucro_percentual / 100)
        valor_inadimplencia = valor_lucro / (1 - self.percentual_inadimplencia / 100)
        valor_reserva = valor_inadimplencia / (1 - self.reserva_tecnica_percentual / 100)
        valor_final = valor_reserva / (1 - self.percentual_impostos / 100)
        
        return valor_final
    
    def get_resumo_custos(self):
        """Retorna um dicionário com resumo organizado dos custos."""
        return {
            'custos_fixos': {
                'Aluguel': self.custo_aluguel,
                'Energia': self.custo_energia,
                'Internet': self.custo_internet,
                'Contabilidade': self.custo_contabilidade,
                'Impostos': self.custo_impostos,
                'Seguros': self.custo_seguros,
                'Financiamento': self.custo_financiamento,
                'Outros Fixos': self.custo_outros_fixos,
                'Total': self.total_custos_fixos
            },
            'custos_variaveis': {
                'Combustível': self.custo_combustivel,
                'Ferramentas': self.custo_ferramentas,
                'Materiais': self.custo_materiais,
                'Comissões': self.custo_comissoes,
                'Marketing': self.custo_marketing,
                'Manutenção': self.custo_manutencao,
                'Outros Variáveis': self.custo_outros_variaveis,
                'Total': self.total_custos_variaveis
            },
            'colaboradores': {
                'Fixos': self.total_custo_fixo_colaboradores,
                'Diaristas': self.total_custo_diaristas,
                'Total': self.total_custo_fixo_colaboradores + self.total_custo_diaristas
            },
            'total_geral': self.custo_total_mensal
        }
    
    def get_analise_ponto_equilibrio(self):
        """Retorna análise detalhada do ponto de equilíbrio."""
        total_horas_disponiveis = self.colaboradores_produtivos * self.horas_mensais_colaborador
        total_horas_produtivas = total_horas_disponiveis * (1 - self.horas_improdutivas_percentual / 100)
        
        if total_horas_produtivas > 0:
            percentual_break_even = (self.horas_ponto_equilibrio / total_horas_produtivas) * 100
        else:
            percentual_break_even = 0
            
        return {
            'horas_necessarias': self.horas_ponto_equilibrio,
            'faturamento_minimo': self.faturamento_ponto_equilibrio,
            'percentual_capacidade': percentual_break_even,
            'horas_disponiveis': total_horas_produtivas,
            'margem_seguranca': total_horas_produtivas - self.horas_ponto_equilibrio,
            'status': 'Saudável' if percentual_break_even < 70 else 'Crítico' if percentual_break_even > 85 else 'Atenção'
        }
    
    def get_analise_cenarios(self):
        """Retorna análise completa dos 3 cenários de utilização."""
        return {
            'otimista': {
                'nome': 'Cenário Otimista',
                'utilizacao': '90%',
                'valor_hora': self.valor_hora_otimista,
                'faturamento_mensal': self.valor_hora_otimista * (self.colaboradores_produtivos * self.horas_mensais_colaborador * 0.9),
                'lucro_estimado': (self.valor_hora_otimista * (self.colaboradores_produtivos * self.horas_mensais_colaborador * 0.9)) - self.custo_total_mensal
            },
            'realista': {
                'nome': 'Cenário Realista',
                'utilizacao': f'{self.percentual_utilizacao_esperada}%',
                'valor_hora': self.valor_hora_realista,
                'faturamento_mensal': self.valor_hora_realista * (self.colaboradores_produtivos * self.horas_mensais_colaborador * (self.percentual_utilizacao_esperada/100)),
                'lucro_estimado': (self.valor_hora_realista * (self.colaboradores_produtivos * self.horas_mensais_colaborador * (self.percentual_utilizacao_esperada/100))) - self.custo_total_mensal
            },
            'pessimista': {
                'nome': 'Cenário Pessimista',
                'utilizacao': '50%',
                'valor_hora': self.valor_hora_pessimista,
                'faturamento_mensal': self.valor_hora_pessimista * (self.colaboradores_produtivos * self.horas_mensais_colaborador * 0.5),
                'lucro_estimado': (self.valor_hora_pessimista * (self.colaboradores_produtivos * self.horas_mensais_colaborador * 0.5)) - self.custo_total_mensal
            }
        }
    
    def get_precificacao_complexidade(self):
        """Retorna tabela de preços por complexidade."""
        return {
            'simples': {
                'nome': 'Serviço Simples',
                'multiplicador': self.multiplicador_simples,
                'valor_hora': self.valor_hora_simples,
                'valor_dia': self.valor_hora_simples * 8,
                'exemplo': 'Manutenção básica, tarefas rotineiras'
            },
            'medio': {
                'nome': 'Serviço Médio',
                'multiplicador': self.multiplicador_medio,
                'valor_hora': self.valor_hora_medio,
                'valor_dia': self.valor_hora_medio * 8,
                'exemplo': 'Instalações padrão, reparos comuns'
            },
            'complexo': {
                'nome': 'Serviço Complexo',
                'multiplicador': self.multiplicador_complexo,
                'valor_hora': self.valor_hora_complexo,
                'valor_dia': self.valor_hora_complexo * 8,
                'exemplo': 'Projetos customizados, alta especialização'
            },
            'urgente': {
                'nome': 'Serviço Urgente',
                'multiplicador': self.multiplicador_urgente,
                'valor_hora': self.valor_hora_urgente,
                'valor_dia': self.valor_hora_urgente * 8,
                'exemplo': 'Demanda imediata, fora do horário'
            }
        }
    
    def get_comparacao_mercado(self):
        """Compara preços calculados com mercado."""
        if self.preco_mercado_hora > 0:
            diferenca_hora = self.valor_hora_final - self.preco_mercado_hora
            percentual_diferenca = (diferenca_hora / self.preco_mercado_hora) * 100
            
            if percentual_diferenca > 20:
                posicionamento = 'Premium (+20%)'
                cor = 'warning'
            elif percentual_diferenca > 0:
                posicionamento = 'Competitivo'
                cor = 'success'
            elif percentual_diferenca > -10:
                posicionamento = 'Agressivo'
                cor = 'info'
            else:
                posicionamento = 'Risco (abaixo do mercado)'
                cor = 'danger'
                
            return {
                'tem_referencia': True,
                'preco_mercado': self.preco_mercado_hora,
                'preco_calculado': self.valor_hora_final,
                'diferenca': diferenca_hora,
                'percentual': percentual_diferenca,
                'posicionamento': posicionamento,
                'cor_badge': cor,
                'recomendacao': self._get_recomendacao_pricing(percentual_diferenca)
            }
        else:
            return {'tem_referencia': False}
    
    def _get_recomendacao_pricing(self, percentual_diferenca):
        """Retorna recomendação estratégica de pricing."""
        if percentual_diferenca > 30:
            return 'Preço muito acima do mercado. Justifique com diferenciais claros.'
        elif percentual_diferenca > 20:
            return 'Posicionamento premium. Invista em branding e qualidade comprovada.'
        elif percentual_diferenca > 10:
            return 'Preço competitivo com margem saudável. Bom equilíbrio.'
        elif percentual_diferenca > 0:
            return 'Preço ligeiramente acima. Ótima posição competitiva.'
        elif percentual_diferenca > -10:
            return 'Preço agressivo para ganhar mercado. Monitore lucratividade.'
        else:
            return 'ALERTA: Preço abaixo do mercado pode indicar subcusto. Revise cálculos.'
    
    def get_indicadores_financeiros(self):
        """Retorna dashboard de indicadores chave."""
        total_horas_disponiveis = self.colaboradores_produtivos * self.horas_mensais_colaborador
        total_horas_produtivas = total_horas_disponiveis * (1 - self.horas_improdutivas_percentual / 100)
        horas_venda_esperada = total_horas_produtivas * (self.percentual_utilizacao_esperada / 100)
        
        faturamento_esperado = self.valor_hora_final * horas_venda_esperada
        lucro_esperado = faturamento_esperado - self.custo_total_mensal
        
        return {
            'markup': self.markup_percentual,
            'margem_contribuicao': self.margem_contribuicao,
            'roi_mensal': self.roi_mensal_calculado,
            'roi_anual_projetado': self.roi_mensal_calculado * 12,
            'faturamento_esperado': faturamento_esperado,
            'lucro_esperado': lucro_esperado,
            'margem_liquida': (lucro_esperado / faturamento_esperado * 100) if faturamento_esperado > 0 else 0,
            'ponto_equilibrio_dias': self.horas_ponto_equilibrio / 8 if self.horas_ponto_equilibrio > 0 else 0
        }
    
    
    def get_dados_grafico(self):
        """Retorna dados formatados para gráficos Chart.js."""
        return {
            'labels': ['Custos Fixos', 'Custos Variáveis', 'Colaboradores Fixos', 'Diaristas'],
            'values': [
                self.total_custos_fixos,
                self.total_custos_variaveis,
                self.total_custo_fixo_colaboradores,
                self.total_custo_diaristas
            ],
            'colors': ['#00ffff', '#0099cc', '#006699', '#004080']
        }
    
    def __repr__(self):
        return f'<ConfigPrecificacao {self.nome_simulacao} - {self.data_simulacao.strftime("%d/%m/%Y")}>'

    @property
    def data_formatada(self):
        """Retorna a data da simulação formatada."""
        return self.data_simulacao.strftime('%d/%m/%Y %H:%M')
    
    @property
    def data_criacao_formatada(self):
        """Retorna a data da simulação formatada."""
        return self.data_simulacao.strftime('%d/%m/%Y %H:%M')
    
    @property
    def margem_formatada(self):
        """Retorna a margem formatada com %."""
        return f"{self.margem_lucro_percentual:.1f}%"
    
    @property
    def valor_hora_formatado(self):
        """Retorna valor hora formatado em R$."""
        return f"R$ {self.valor_hora_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def valor_hora_ideal_formatado(self):
        """Retorna valor hora formatado em R$."""
        return f"R$ {self.valor_hora_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def valor_dia_formatado(self):
        """Retorna valor dia formatado em R$."""
        return f"R$ {self.valor_dia_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def valor_dia_ideal_formatado(self):
        """Retorna valor dia formatado em R$."""
        return f"R$ {self.valor_dia_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def valor_empreita_formatado(self):
        """Retorna valor empreita formatado em R$."""
        return f"R$ {self.valor_empreita_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def custo_total_formatado(self):
        """Retorna custo total formatado em R$."""
        return f"R$ {self.custo_total_mensal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def custo_total_mensal_formatado(self):
        """Retorna custo total formatado em R$."""
        return f"R$ {self.custo_total_mensal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def custo_fixo_total(self):
        """Retorna o total de custos fixos."""
        return self.total_custos_fixos
    
    @property
    def custo_fixo_total_formatado(self):
        """Retorna custos fixos formatados em R$."""
        return f"R$ {self.total_custos_fixos:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def custo_variavel_total(self):
        """Retorna o total de custos variáveis."""
        return self.total_custos_variaveis
    
    @property
    def custo_variavel_total_formatado(self):
        """Retorna custos variáveis formatados em R$."""
        return f"R$ {self.total_custos_variaveis:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def custo_mao_obra_total(self):
        """Retorna o total de custos com mão de obra."""
        return self.total_custo_fixo_colaboradores + self.total_custo_diaristas
    
    @property
    def custo_mao_obra_total_formatado(self):
        """Retorna custos de mão de obra formatados em R$."""
        total = self.total_custo_fixo_colaboradores + self.total_custo_diaristas
        return f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def salario_medio_fixo_formatado(self):
        """Retorna salário médio formatado em R$."""
        return f"R$ {self.salario_medio_fixo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def valor_diaria_formatado(self):
        """Retorna valor da diária formatado em R$."""
        return f"R$ {self.valor_diaria:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # === PROPERTIES FORMATADAS - NOVOS CAMPOS ===
    
    def _formatar_moeda(self, valor):
        """Helper para formatar valores em moeda brasileira."""
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def valor_hora_otimista_fmt(self):
        return self._formatar_moeda(self.valor_hora_otimista)
    
    @property
    def valor_hora_realista_fmt(self):
        return self._formatar_moeda(self.valor_hora_realista)
    
    @property
    def valor_hora_pessimista_fmt(self):
        return self._formatar_moeda(self.valor_hora_pessimista)
    
    @property
    def valor_hora_simples_fmt(self):
        return self._formatar_moeda(self.valor_hora_simples)
    
    @property
    def valor_hora_medio_fmt(self):
        return self._formatar_moeda(self.valor_hora_medio)
    
    @property
    def valor_hora_complexo_fmt(self):
        return self._formatar_moeda(self.valor_hora_complexo)
    
    @property
    def valor_hora_urgente_fmt(self):
        return self._formatar_moeda(self.valor_hora_urgente)
    
    @property
    def faturamento_ponto_equilibrio_fmt(self):
        return self._formatar_moeda(self.faturamento_ponto_equilibrio)
    
    @property
    def preco_mercado_hora_fmt(self):
        return self._formatar_moeda(self.preco_mercado_hora)
    
    @property
    def capital_investido_fmt(self):
        return self._formatar_moeda(self.capital_investido)
    
    @property
    def markup_fmt(self):
        return f"{self.markup_percentual:.1f}%"
    
    @property
    def margem_contribuicao_fmt(self):
        return f"{self.margem_contribuicao:.1f}%"
    
    @property
    def roi_mensal_fmt(self):
        return f"{self.roi_mensal_calculado:.2f}%"
    
    @property
    def roi_anual_fmt(self):
        return f"{self.roi_mensal_calculado * 12:.2f}%"