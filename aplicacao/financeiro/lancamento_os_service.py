from datetime import date, timedelta
from decimal import Decimal
import json
import logging

from aplicacao.extensoes import db
from aplicacao.financeiro.lancamento_os_model import LancamentoFinanceiroOS

# Configuração de logging
logger = logging.getLogger(__name__)

def remover_lancamentos_da_os(os_id: int):
    """Remove todos os lançamentos financeiros associados a uma OS específica."""
    logger.info(f"Removendo lançamentos financeiros existentes para OS ID: {os_id}")
    LancamentoFinanceiroOS.query.filter_by(os_id=os_id).delete()
    db.session.flush()
    logger.info(f"Lançamentos financeiros removidos para OS ID: {os_id}")

def gerar_lancamentos_financeiro(
    os, *,
    forma_pagamento: str,
    valor_total: Decimal,
    parcelas: int = 1,
    entrada: Decimal = Decimal("0.00"),
    schedule_custom: list[tuple[Decimal, date]] | None = None,
    descricao_prefixo: str = "OS"
) -> list[LancamentoFinanceiroOS]:
    """
    Gera lançamentos financeiros para a OS.

    - Idempotente: remove e recria lançamentos da OS.
    - schedule_custom: lista [(valor, data)], ignora regra de 30 dias e usa exatamente o informado.
    
    Args:
        os: Instância da ordem de serviço
        forma_pagamento: Forma de pagamento (pix, dinheiro, boleto, cartao)
        valor_total: Valor total da OS
        parcelas: Número de parcelas (padrão: 1)
        entrada: Valor da entrada (padrão: 0.00)
        schedule_custom: Cronograma personalizado [(valor, data), ...]
        descricao_prefixo: Prefixo para descrição dos lançamentos
        
    Returns:
        Lista de objetos LancamentoFinanceiroOS criados
    """
    # Log inicial
    logger.info(f"Gerando lançamentos financeiros para OS ID: {os.id}, Código: {os.codigo}, " +
                f"Valor Total: {valor_total}, Parcelas: {parcelas}, Entrada: {entrada}")
    
    # Garante idempotência removendo lançamentos existentes
    remover_lancamentos_da_os(os.id)

    lancs: list[LancamentoFinanceiroOS] = []
    desc_base = f"{descricao_prefixo} {os.codigo} - {getattr(os.cliente, 'nome', '').strip() or 'Cliente'}"

    # Schedule custom tem prioridade
    if schedule_custom:
        logger.info(f"Usando cronograma personalizado com {len(schedule_custom)} parcelas para OS ID: {os.id}")
        for idx, (valor, dt) in enumerate(schedule_custom, start=1):
            lancs.append(LancamentoFinanceiroOS(
                os_id=os.id,
                descricao=f"Parcela {idx}/{len(schedule_custom)} - {desc_base}",
                valor=Decimal(valor),
                data_vencimento=dt,
                forma_pagamento=forma_pagamento,
                parcela=idx,
                total_parcelas=len(schedule_custom),
            ))
        db.session.add_all(lancs)
        db.session.commit()
        logger.info(f"Criados {len(lancs)} lançamentos financeiros personalizados para OS ID: {os.id}")
        return lancs

    # Processamento de entrada quando especificada
    if entrada and entrada > 0:
        logger.info(f"Processando entrada de {entrada} para OS ID: {os.id}")
        lancs.append(LancamentoFinanceiroOS(
            os_id=os.id,
            descricao=f"Entrada - {desc_base}",
            valor=Decimal(entrada),
            data_vencimento=date.today(),
            forma_pagamento=forma_pagamento,
            parcela=0,
            total_parcelas=parcelas if parcelas and parcelas > 1 else 1,
        ))
        valor_total = Decimal(valor_total) - Decimal(entrada)
        parcelas = max(1, (parcelas or 1) - 1)

    # Pagamento à vista
    if (parcelas or 1) <= 1:
        logger.info(f"Criando lançamento à vista de {valor_total} para OS ID: {os.id}")
        lancs.append(LancamentoFinanceiroOS(
            os_id=os.id,
            descricao=f"Pagamento à vista - {desc_base}",
            valor=Decimal(valor_total),
            data_vencimento=date.today(),
            forma_pagamento=forma_pagamento,
            parcela=1,
            total_parcelas=1,
        ))
    else:
        # Pagamento parcelado
        logger.info(f"Criando {parcelas} parcelas de aproximadamente {valor_total/parcelas} para OS ID: {os.id}")
        parcelas = int(parcelas)
        valor_parcela = (Decimal(valor_total) / parcelas).quantize(Decimal("0.01"))
        
        # Ajusta a última parcela para garantir soma exata
        ultima_parcela = valor_total - (valor_parcela * (parcelas - 1))
        ultima_parcela = ultima_parcela.quantize(Decimal("0.01"))
        
        for i in range(parcelas):
            venc = date.today() + timedelta(days=30*(i+1))
            
            # Valor ajustado para a última parcela
            valor = ultima_parcela if i == parcelas - 1 else valor_parcela
            
            lancs.append(LancamentoFinanceiroOS(
                os_id=os.id,
                descricao=f"Parcela {i+1}/{parcelas} - {desc_base}",
                valor=valor,
                data_vencimento=venc,
                forma_pagamento=forma_pagamento,
                parcela=i+1,
                total_parcelas=parcelas,
            ))

    # Persiste no banco
    db.session.add_all(lancs)
    db.session.commit()
    logger.info(f"Total de {len(lancs)} lançamentos financeiros criados para OS ID: {os.id}")
    return lancs

def parse_schedule_custom(schedule_json_str):
    """
    Converte string JSON de schedule para lista de tuplas (valor, data)
    
    Args:
        schedule_json_str: String JSON no formato [{"valor": "100.00", "data": "2023-01-01"}, ...]
        
    Returns:
        Lista de tuplas [(Decimal("100.00"), date(2023, 1, 1)), ...]
    """
    if not schedule_json_str:
        return None
        
    try:
        schedule_list = json.loads(schedule_json_str)
        return [(Decimal(item["valor"]), date.fromisoformat(item["data"])) 
                for item in schedule_list]
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Erro ao processar cronograma personalizado: {e}")
        return None
