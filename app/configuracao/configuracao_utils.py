# Utilitários para carregar a configuração global do sistema
# Fornece função `get_config()` para uso em templates e outros módulos

from app.configuracao.configuracao_model import Configuracao
from datetime import datetime, timedelta

_cached = None
_cache_time = None
_cache_duration = timedelta(seconds=30)  # Cache válido por 30 segundos


class ConfigSnapshot(dict):
    """Snapshot simples da configuração, sem vínculo com a sessão SQLAlchemy.

    Mantém compatibilidade com os usos existentes por atributo
    (`config.logo_base64`) e como dicionário (`config.get('logo_base64')`).
    """

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value


def _snapshot_config(config):
    """Copia todos os campos mapeados enquanto a instância ORM está vinculada."""
    if config is None:
        return None

    return ConfigSnapshot({
        coluna.name: getattr(config, coluna.name)
        for coluna in Configuracao.__table__.columns
    })


def get_config(force_reload=False):
    """Retorna um snapshot seguro da configuração global.

    O cache nunca mantém uma instância ORM entre requisições. Isso evita
    `DetachedInstanceError` quando o SQLAlchemy encerra a sessão ao final de
    uma requisição e outro template reutiliza a configuração dentro do TTL.
    """
    global _cached, _cache_time

    needs_reload = (
        force_reload
        or _cached is None
        or _cache_time is None
        or (datetime.now() - _cache_time) > _cache_duration
    )

    if needs_reload:
        _cached = _snapshot_config(Configuracao.get_solo())
        _cache_time = datetime.now()

    return _cached


def invalidate_cache():
    """Invalida o cache forçando reload na próxima chamada."""
    global _cached, _cache_time
    _cached = None
    _cache_time = None
