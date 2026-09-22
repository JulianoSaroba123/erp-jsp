"""Infraestrutura XML da NFS-e Nacional."""

from .dps_serializer import (
    NAMESPACE_NFSE,
    VERSAO_DPS,
    SerializacaoDpsInvalida,
    adicionar_elemento_nfse,
    criar_elemento_nfse,
    montar_xml_dps,
    serializar_xml,
)

__all__ = [
    "NAMESPACE_NFSE",
    "VERSAO_DPS",
    "SerializacaoDpsInvalida",
    "adicionar_elemento_nfse",
    "criar_elemento_nfse",
    "montar_xml_dps",
    "serializar_xml",
]
