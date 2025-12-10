# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Models Base
===========================

Classes base para todos os models do sistema.
Define campos comuns e métodos padrão.

Autor: JSP Soluções
Data: 2025
"""

from datetime import datetime
from app.extensoes import db

class BaseModel(db.Model):
    """
    Model base para todas as entidades do sistema.
    
    Fornece campos comuns como ID, timestamps e métodos úteis.
    Todas as entidades devem herdar desta classe.
    """
    __abstract__ = True
    
    # Chave primária
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Timestamps automáticos
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Campos de auditoria (para futura implementação)
    ativo = db.Column(db.Boolean, default=True, nullable=False, server_default='true')
    
    def save(self):
        """
        Salva o registro no banco de dados.
        
        Returns:
            self: O próprio objeto para method chaining
        """
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """
        Remove o registro do banco de dados.
        
        Returns:
            bool: True se removido com sucesso
        """
        db.session.delete(self)
        db.session.commit()
        return True
    
    def soft_delete(self):
        """
        Faz uma exclusão lógica (marca como inativo).
        
        Returns:
            self: O próprio objeto para method chaining
        """
        self.ativo = False
        return self.save()
    
    def to_dict(self):
        """
        Converte o objeto para dicionário.
        
        Returns:
            dict: Representação em dicionário do objeto
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    @classmethod
    def get_all_active(cls):
        """
        Retorna todos os registros ativos.
        
        Returns:
            list: Lista de objetos ativos
        """
        return cls.query.filter_by(ativo=True).all()
    
    @classmethod
    def get_by_id(cls, id):
        """
        Busca um registro pelo ID.
        
        Args:
            id (int): ID do registro
            
        Returns:
            object: Objeto encontrado ou None
        """
        return cls.query.filter_by(id=id, ativo=True).first()
    
    def __repr__(self):
        """Representação string do objeto."""
        return f'<{self.__class__.__name__} {self.id}>'