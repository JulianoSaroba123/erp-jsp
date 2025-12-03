# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Cliente
================================

Define a estrutura de dados para clientes.
Inclui validações e relacionamentos.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from app.models import BaseModel

class Cliente(BaseModel):
    """
    Model para representar clientes do sistema.
    
    Armazena informações completas dos clientes,
    incluindo dados pessoais e de contato.
    
    🆕 Melhorado com campos profissionais completos
    """
    __tablename__ = 'clientes'
    
    # === DADOS PRINCIPAIS ===
    nome = db.Column(db.String(150), nullable=False, index=True)
    nome_fantasia = db.Column(db.String(150), index=True)  # Para PJ
    razao_social = db.Column(db.String(200))  # Para PJ
    tipo = db.Column(db.String(20), nullable=False, default='PF')  # PF ou PJ
    
    # === DOCUMENTOS ===
    cpf_cnpj = db.Column(db.String(20), unique=True, index=True)
    rg_ie = db.Column(db.String(20))
    im = db.Column(db.String(20))  # Inscrição Municipal
    
    # === CONTATO PRINCIPAL ===
    email = db.Column(db.String(150), index=True)
    email_financeiro = db.Column(db.String(150))  # Email específico para cobrança
    telefone = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    site = db.Column(db.String(200))
    
    # === CONTATO COMERCIAL ===
    contato_nome = db.Column(db.String(100))  # Nome do responsável
    contato_cargo = db.Column(db.String(100))  # Cargo do responsável
    contato_telefone = db.Column(db.String(20))
    contato_email = db.Column(db.String(150))
    
    # === ENDEREÇO COMPLETO ===
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    pais = db.Column(db.String(50), default='Brasil')
    
    # === DADOS COMERCIAIS ===
    segmento = db.Column(db.String(100))  # Setor de atuação
    porte_empresa = db.Column(db.String(20))  # MEI, ME, EPP, Grande
    origem = db.Column(db.String(50))  # Como conheceu a empresa
    classificacao = db.Column(db.String(20), default='A')  # A, B, C (qualidade)
    
    # === CONFIGURAÇÕES FINANCEIRAS ===
    limite_credito = db.Column(db.Numeric(10, 2), default=0)
    forma_pagamento_padrao = db.Column(db.String(50))
    prazo_pagamento_padrao = db.Column(db.Integer, default=30)  # dias
    desconto_padrao = db.Column(db.Numeric(5, 2), default=0)  # %
    
    # === INFORMAÇÕES EXTRAS ===
    data_nascimento = db.Column(db.Date)  # Para PF
    data_fundacao = db.Column(db.Date)  # Para PJ
    genero = db.Column(db.String(20))  # Para PF
    estado_civil = db.Column(db.String(20))  # Para PF
    profissao = db.Column(db.String(100))  # Para PF
    
    # === OBSERVAÇÕES ===
    observacoes = db.Column(db.Text)
    observacoes_internas = db.Column(db.Text)  # Não visível em relatórios
    
    # === STATUS ===
    status = db.Column(db.String(20), default='ativo')  # ativo, inativo, bloqueado
    motivo_bloqueio = db.Column(db.String(200))
    
    def __repr__(self):
        """Representação string do cliente."""
        return f'<Cliente {self.nome_display}>'
    
    def __str__(self):
        """String do cliente para exibição."""
        return self.nome_display
    
    @property
    def nome_display(self):
        """Nome formatado para exibição."""
        if self.tipo == 'PJ' and self.nome_fantasia:
            return self.nome_fantasia.title()
        return self.nome.title() if self.nome else ''
    
    @property
    def nome_completo(self):
        """Nome completo incluindo razão social."""
        if self.tipo == 'PJ':
            if self.nome_fantasia and self.razao_social:
                return f"{self.nome_fantasia} ({self.razao_social})"
            return self.nome_fantasia or self.razao_social or self.nome
        return self.nome
    
    @property
    def documento_formatado(self):
        """Documento formatado (CPF/CNPJ)."""
        if not self.cpf_cnpj:
            return ''
        
        doc = ''.join(filter(str.isdigit, self.cpf_cnpj))
        
        if len(doc) == 11:  # CPF
            return f'{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}'
        elif len(doc) == 14:  # CNPJ
            return f'{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}'
        
        return self.cpf_cnpj
    
    @property
    def nome_exibicao(self):
        """
        Retorna o melhor nome para exibição.
        Prioridade: nome_fantasia > nome > razao_social
        (Priorizando o que foi cadastrado como nome principal)
        """
        if self.nome_fantasia and self.nome_fantasia.strip():
            return self.nome_fantasia.strip()
        elif self.nome and self.nome.strip():
            return self.nome.strip()
        elif self.razao_social and self.razao_social.strip():
            return self.razao_social.strip()
        else:
            return f"Cliente {self.id}"
    
    @property
    def telefone_principal(self):
        """Retorna o telefone principal (prioriza celular)."""
        return self.celular or self.whatsapp or self.telefone or ''
    
    @property
    def email_principal(self):
        """Retorna o email principal."""
        return self.email or self.contato_email or ''
    
    @property
    def endereco_completo(self):
        """Endereço completo formatado."""
        partes = []
        
        if self.endereco:
            endereco_base = self.endereco
            if self.numero:
                endereco_base += f', {self.numero}'
            if self.complemento:
                endereco_base += f' - {self.complemento}'
            partes.append(endereco_base)
        
        if self.bairro:
            partes.append(self.bairro)
        
        if self.cidade and self.estado:
            partes.append(f'{self.cidade}/{self.estado}')
        elif self.cidade:
            partes.append(self.cidade)
        
        if self.cep:
            cep_formatado = self.cep_formatado
            if cep_formatado:
                partes.append(f'CEP: {cep_formatado}')
        
        return ' - '.join(partes) if partes else ''
    
    @property
    def cep_formatado(self):
        """CEP formatado."""
        if not self.cep:
            return ''
        cep = ''.join(filter(str.isdigit, self.cep))
        if len(cep) == 8:
            return f'{cep[:5]}-{cep[5:]}'
        return self.cep
    
    @property
    def status_badge_class(self):
        """Classe CSS para badge de status."""
        classes = {
            'ativo': 'bg-success',
            'inativo': 'bg-secondary', 
            'bloqueado': 'bg-danger',
            'suspenso': 'bg-warning'
        }
        return classes.get(self.status, 'bg-secondary')
    
    @property
    def classificacao_cor(self):
        """Cor da classificação do cliente."""
        cores = {
            'A': 'success',  # Verde
            'B': 'warning',  # Amarelo
            'C': 'danger'    # Vermelho
        }
        return cores.get(self.classificacao, 'secondary')
    
    @property
    def idade(self):
        """Calcula idade (para PF)."""
        if not self.data_nascimento:
            return None
        from datetime import date
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
    
    @property
    def tempo_empresa(self):
        """Calcula tempo de empresa (para PJ)."""
        if not self.data_fundacao:
            return None
        from datetime import date
        hoje = date.today()
        anos = hoje.year - self.data_fundacao.year
        if anos == 1:
            return "1 ano"
        elif anos > 1:
            return f"{anos} anos"
        else:
            meses = (hoje.year - self.data_fundacao.year) * 12 + hoje.month - self.data_fundacao.month
            return f"{meses} meses" if meses > 0 else "Menos de 1 mês"
    
    @classmethod
    def buscar_por_documento(cls, documento):
        """
        Busca cliente por CPF/CNPJ.
        
        Args:
            documento (str): CPF ou CNPJ
            
        Returns:
            Cliente: Cliente encontrado ou None
        """
        doc_limpo = ''.join(filter(str.isdigit, documento))
        return cls.query.filter_by(cpf_cnpj=doc_limpo, ativo=True).first()
    
    @classmethod
    def buscar_por_nome(cls, nome):
        """
        Busca clientes por nome (busca parcial).
        
        Args:
            nome (str): Nome ou parte do nome
            
        Returns:
            list: Lista de clientes encontrados
        """
        return cls.query.filter(
            db.or_(
                cls.nome.ilike(f'%{nome}%'),
                cls.nome_fantasia.ilike(f'%{nome}%'),
                cls.razao_social.ilike(f'%{nome}%')
            ),
            cls.ativo == True
        ).order_by(cls.nome).all()
    
    @classmethod
    def buscar_por_email(cls, email):
        """Busca cliente por email."""
        return cls.query.filter(
            db.or_(
                cls.email.ilike(email),
                cls.email_financeiro.ilike(email),
                cls.contato_email.ilike(email)
            ),
            cls.ativo == True
        ).first()
    
    @classmethod
    def listar_ativos(cls):
        """Lista todos os clientes ativos ordenados por nome."""
        return cls.query.filter_by(ativo=True, status='ativo').order_by(cls.nome).all()
    
    @classmethod
    def estatisticas(cls):
        """Retorna estatísticas dos clientes."""
        total = cls.query.filter_by(ativo=True).count()
        pf = cls.query.filter_by(tipo='PF', ativo=True).count()
        pj = cls.query.filter_by(tipo='PJ', ativo=True).count()
        bloqueados = cls.query.filter_by(status='bloqueado', ativo=True).count()
        
        # Por classificação
        classe_a = cls.query.filter_by(classificacao='A', ativo=True).count()
        classe_b = cls.query.filter_by(classificacao='B', ativo=True).count()
        classe_c = cls.query.filter_by(classificacao='C', ativo=True).count()
        
        return {
            'total': total,
            'pessoa_fisica': pf,
            'pessoa_juridica': pj,
            'bloqueados': bloqueados,
            'classe_a': classe_a,
            'classe_b': classe_b,
            'classe_c': classe_c
        }
    
    def validar_documento(self):
        """
        Valida CPF/CNPJ.
        
        Returns:
            tuple: (bool, str) - (é_válido, mensagem_erro)
        """
        if not self.cpf_cnpj:
            return True, ""
        
        doc = ''.join(filter(str.isdigit, self.cpf_cnpj))
        
        if self.tipo == 'PF':
            if len(doc) != 11:
                return False, "CPF deve ter 11 dígitos"
            return self._validar_cpf(doc), "CPF inválido"
        elif self.tipo == 'PJ':
            if len(doc) != 14:
                return False, "CNPJ deve ter 14 dígitos"
            return self._validar_cnpj(doc), "CNPJ inválido"
        
        return True, ""
    
    def _validar_cpf(self, cpf):
        """Validação matemática do CPF."""
        if cpf == cpf[0] * 11:  # CPFs inválidos como 11111111111
            return False
        
        # Calcula primeiro dígito
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        if digito1 == 10:
            digito1 = 0
        
        # Calcula segundo dígito
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        if digito2 == 10:
            digito2 = 0
        
        return int(cpf[9]) == digito1 and int(cpf[10]) == digito2
    
    def _validar_cnpj(self, cnpj):
        """Validação matemática do CNPJ."""
        if cnpj == cnpj[0] * 14:  # CNPJs inválidos
            return False
        
        # Calcula primeiro dígito
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(12))
        digito1 = soma % 11
        digito1 = 0 if digito1 < 2 else 11 - digito1
        
        # Calcula segundo dígito
        pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(13))
        digito2 = soma % 11
        digito2 = 0 if digito2 < 2 else 11 - digito2
        
        return int(cnpj[12]) == digito1 and int(cnpj[13]) == digito2
    
    def bloquear(self, motivo):
        """Bloqueia o cliente."""
        self.status = 'bloqueado'
        self.motivo_bloqueio = motivo
        self.save()
    
    def desbloquear(self):
        """Desbloqueia o cliente.""" 
        self.status = 'ativo'
        self.motivo_bloqueio = None
        self.save()
    
    def pode_comprar(self):
        """Verifica se o cliente pode fazer compras."""
        return self.ativo and self.status == 'ativo'