# Utilitários para carregar a configuração global do sistema
# Fornece função `get_config()` para uso em templates e outros módulos

from app.configuracao.configuracao_model import Configuracao

_cached = None


def get_config(force_reload=False):
    """Retorna a instância única de Configuracao.

    Usa cache em memória para evitar consultas repetidas. Use force_reload=True
    para forçar leitura do banco.
    """
    global _cached
    if _cached is None or force_reload:
        _cached = Configuracao.get_solo()
    return _cached
