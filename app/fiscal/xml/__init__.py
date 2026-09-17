"""Infraestrutura XML da NFS-e Nacional."""

from .dps_serializer import (
    NAMESPACE_NFSE,
    VERSAO_DPS,
    criar_elemento_nfse,
    serializar_xml,
)

__all__ = [
    "NAMESPACE_NFSE",
    "VERSAO_DPS",
    "criar_elemento_nfse",
    "serializar_xml",
]
