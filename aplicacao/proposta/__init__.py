"""
Pacote 'proposta'

Este arquivo evita importações pesadas no momento da importação do pacote,
previne importações circulares e delega o registro de blueprints ao
módulo de inicialização da aplicação (`aplicacao.__init__`).
"""

def init_app(app):
    """Placeholder para compatibilidade - registro é feito externamente."""
    return
