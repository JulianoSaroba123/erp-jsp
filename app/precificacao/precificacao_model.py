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
    
    # Resultados Calculados
    total_custos_fixos = Column(Float, default=0.0)
    total_custos_variaveis = Column(Float, default=0.0)
    total_custo_fixo_colaboradores = Column(Float, default=0.0)
    total_custo_diaristas = Column(Float, default=0.0)
    custo_total_mensal = Column(Float, default=0.0)
    
    valor_hora_base = Column(Float, default=0.0)
    valor_hora_final = Column(Float, default=0.0)
    valor_dia_final = Column(Float, default=0.0)
    valor_empreita_final = Column(Float, default=0.0)
    
    # Campos Auxiliares
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
    
    def calcular_precificacao(self):
        """Executa todos os cálculos de precificação baseado nos dados atuais."""
        
        # 1. Calcular totais de custos
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
        
        # 2. Calcular custos de colaboradores COM ENCARGOS
        custo_fixos_bruto = self.colaboradores_fixos_qtd * self.salario_medio_fixo
        self.total_custo_fixo_colaboradores = custo_fixos_bruto * (1 + self.percentual_encargos / 100)
        
        custo_diaristas_bruto = (
            self.colaboradores_diaristas_qtd * 
            self.valor_diaria * 
            self.dias_trabalhados_mes
        )
        self.total_custo_diaristas = custo_diaristas_bruto * (1 + self.percentual_encargos / 100)
        
        # 3. Custo total mensal
        self.custo_total_mensal = (
            self.total_custos_fixos + 
            self.total_custos_variaveis + 
            self.total_custo_fixo_colaboradores + 
            self.total_custo_diaristas
        )
        
        # 4. Cálculo do valor hora considerando horas produtivas
        total_horas_teoricas = (
            self.colaboradores_produtivos * self.horas_mensais_colaborador
        )
        
        # Descontar horas improdutivas
        total_horas_produtivas = total_horas_teoricas * (1 - self.horas_improdutivas_percentual / 100)
        
        if total_horas_produtivas > 0:
            # Valor hora base (custo sem margem)
            self.valor_hora_base = self.custo_total_mensal / total_horas_produtivas
            
            # Adicionar margem de lucro
            valor_com_lucro = self.valor_hora_base * (1 + self.margem_lucro_percentual / 100)
            
            # Adicionar impostos sobre venda (para que o líquido seja o planejado)
            self.valor_hora_final = valor_com_lucro / (1 - self.percentual_impostos / 100)
        else:
            self.valor_hora_base = 0.0
            self.valor_hora_final = 0.0
        
        # 5. Valor dia e empreita
        self.valor_dia_final = self.valor_hora_final * 8  # 8 horas por dia
        self.valor_empreita_final = self.valor_dia_final * 10  # Empreita padrão de 10 dias
    
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