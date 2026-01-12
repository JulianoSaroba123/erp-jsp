# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Concessionária
=======================================

Define a estrutura de dados para concessionárias de energia elétrica.
Armazena tarifas (TE, TUSD) e impostos (PIS, COFINS, ICMS).

Autor: JSP Soluções
Data: 2026
"""

from app.extensoes import db
from app.models import BaseModel
from datetime import date

class Concessionaria(BaseModel):
    """
    Model para representar concessionárias de energia elétrica.
    
    Armazena informações tarifárias e tributárias para cálculos
    de economia em projetos de energia solar.
    """
    __tablename__ = 'concessionarias'
    
    # === DADOS PRINCIPAIS ===
    nome = db.Column(db.String(200), nullable=False, index=True)
    regiao = db.Column(db.String(100))  # Estado, cidade ou área de atuação
    
    # === TARIFAS (R$/kWh) ===
    te = db.Column(db.Numeric(10, 4))  # Tarifa de Energia
    tusd = db.Column(db.Numeric(10, 4))  # Tarifa de Uso do Sistema de Distribuição
    
    # === IMPOSTOS (%) ===
    pis = db.Column(db.Numeric(5, 2))  # PIS
    cofins = db.Column(db.Numeric(5, 2))  # COFINS
    icms = db.Column(db.Numeric(5, 2))  # ICMS
    
    # === CONTROLE ===
    data_atualizacao = db.Column(db.Date, default=date.today)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f'<Concessionaria {self.nome}>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'regiao': self.regiao,
            'te': float(self.te) if self.te else None,
            'tusd': float(self.tusd) if self.tusd else None,
            'pis': float(self.pis) if self.pis else None,
            'cofins': float(self.cofins) if self.cofins else None,
            'icms': float(self.icms) if self.icms else None,
            'data_atualizacao': self.data_atualizacao.strftime('%d/%m/%Y') if self.data_atualizacao else None,
            'ativo': self.ativo
        }
    
    @property
    def tarifa_total(self):
        """Calcula a tarifa total (TE + TUSD)"""
        te_val = float(self.te) if self.te else 0
        tusd_val = float(self.tusd) if self.tusd else 0
        return te_val + tusd_val
    
    @property
    def tarifa_final(self):
        """Calcula a tarifa final incluindo impostos"""
        tarifa_base = self.tarifa_total
        
        # Percentuais de impostos
        pis_val = float(self.pis) if self.pis else 0
        cofins_val = float(self.cofins) if self.cofins else 0
        icms_val = float(self.icms) if self.icms else 0
        
        # Fator multiplicador: 1 + (impostos / 100)
        fator = 1 + (pis_val + cofins_val + icms_val) / 100
        
        return tarifa_base * fator
