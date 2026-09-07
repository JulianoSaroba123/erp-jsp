# Módulo financeiro - inicialização

# Mantém o saldo das contas bancárias sincronizado com lançamentos quitados.
# O registro é idempotente por processo e não altera dados históricos ao importar.
from app.financeiro.saldo_bancario_events import registrar_eventos_saldo_bancario

registrar_eventos_saldo_bancario()
