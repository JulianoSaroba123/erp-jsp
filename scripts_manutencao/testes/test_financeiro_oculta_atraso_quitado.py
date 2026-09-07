from pathlib import Path


def test_listagem_nao_exibe_alerta_de_vencimento_para_quitados():
    template = Path(
        "app/financeiro/templates/financeiro/listar_lancamentos.html"
    ).read_text(encoding="utf-8")

    guard = "{% if lancamento.status not in ['pago', 'recebido', 'cancelado'] %}"
    bloco_atraso = "{{ lancamento.dias_vencimento|abs }} dia(s) atrasado"

    assert guard in template
    assert bloco_atraso in template
    assert template.index(guard) < template.index(bloco_atraso)
