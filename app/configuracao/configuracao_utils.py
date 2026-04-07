# Utilitários para carregar a configuração global do sistema
# Fornece função `get_config()` para uso em templates e outros módulos

from app.configuracao.configuracao_model import Configuracao
from datetime import datetime, timedelta

_cached = None
_cache_time = None
_cache_duration = timedelta(seconds=30)  # Cache válido por 30 segundos


def get_config(force_reload=False):
    """Retorna a instância única de Configuracao.

    Usa cache em memória com TTL de 30 segundos para evitar consultas repetidas,
    mas garante que dados não ficam muito desatualizados.
    
    Use force_reload=True para forçar leitura do banco imediatamente.
    """
    global _cached, _cache_time
    
    # Verificar se precisa recarregar
    needs_reload = (
        force_reload or 
        _cached is None or 
        _cache_time is None or 
        (datetime.now() - _cache_time) > _cache_duration
    )
    
    if needs_reload:
        _cached = Configuracao.get_solo()
        _cache_time = datetime.now()
    
    return _cached


def invalidate_cache():
    """Invalida o cache forçando reload na próxima chamada."""
    global _cached, _cache_time
    _cached = None
    _cache_time = None
