# -*- coding: utf-8 -*-
"""
Utilitário de compatibilidade de banco de dados
================================================
Garante que o app funcione mesmo se migrations não rodaram ainda.
"""

from functools import wraps
import logging

logger = logging.getLogger(__name__)

def safe_attribute(default=None):
    """
    Decorator que retorna um valor padrão se o atributo não existir no DB.
    
    Uso:
        @safe_attribute(default=None)
        def hora_entrada_manha(self):
            return self._hora_entrada_manha
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except AttributeError as e:
                logger.warning(f"Coluna não existe no DB: {e}. Retornando {default}")
                return default
        return wrapper
    return decorator


def safe_query(query_func):
    """
    Decorator para queries que podem falhar por colunas inexistentes.
    
    Uso:
        @safe_query
        def get_all_os():
            return OrdemServico.query.all()
    """
    @wraps(query_func)
    def wrapper(*args, **kwargs):
        try:
            return query_func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()
            if 'column' in error_msg or 'does not exist' in error_msg:
                logger.error(f"Erro de schema no banco: {e}")
                logger.error("Execute as migrations: python migrate_db.py")
                raise RuntimeError(
                    "Banco de dados desatualizado. "
                    "Execute 'python migrate_db.py' para atualizar o schema."
                ) from e
            raise
    return wrapper
