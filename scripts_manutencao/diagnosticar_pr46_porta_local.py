# -*- coding: utf-8 -*-
"""Diagnóstico SOMENTE LEITURA do banco configurado no processo da porta 5001.

Não importa app, não se conecta a banco e jamais imprime DATABASE_URL.
Requer psutil para identificar processo e ler seu ambiente no Windows.
Se for desconhecido, encerra como NÃO VERIFICADO (código 2).
"""
from pathlib import Path
from urllib.parse import urlsplit
import os
import sys


def _classificar_url(valor):
    if not valor:
        return ("INDETERMINADO", 2)
    texto = str(valor).strip()
    try:
        parsed = urlsplit(texto)
    except ValueError:
        return ("INDETERMINADO", 2)
    esquema = parsed.scheme.lower()
    if esquema == "sqlite":
        return ("SQLITE (local, sem endereço PostgreSQL)", 0)
    if esquema.startswith("postgres"):
        host = (parsed.hostname or "").lower()
        if host in {"127.0.0.1", "localhost", "::1"}:
            return ("POSTGRESQL LOCAL (confirmar base de testes)", 0)
        return ("POSTGRESQL REMOTO - NAO EXECUTAR TESTES DE ESCRITA", 3)
    return ("BANCO INDETERMINADO - NAO EXECUTAR TESTES DE ESCRITA", 2)


def _ler_dotenv_sem_expor(diretorio):
    raiz = Path(diretorio)
    candidatos = [raiz / ".env", raiz.parent / ".env"]
    for arquivo in candidatos:
        if not arquivo.is_file():
            continue
        try:
            from dotenv import dotenv_values
            return dotenv_values(arquivo).get("DATABASE_URL")
        except (OSError, ImportError):
            return None
    return None


def diagnosticar(porta=5001):
    try:
        import psutil
    except ImportError:
        print("NAO VERIFICADO: psutil ausente. Nao executar testes contra a porta.")
        print("Para instalar localmente, se autorizado: python -m pip install psutil")
        return 2

    try:
        processos = sorted({
            info.pid for info in psutil.net_connections(kind="inet")
            if info.laddr and info.laddr.port == porta
            and info.status == psutil.CONN_LISTEN and info.pid
        })
    except (OSError, psutil.Error):
        print("NAO VERIFICADO: sem permissão para inspecionar processos locais.")
        return 2

    if len(processos) != 1:
        print(f"NAO VERIFICADO: encontrado(s) {len(processos)} processo(s) ouvindo na porta {porta}.")
        return 2

    pid = processos[0]
    try:
        proc = psutil.Process(pid)
        ambiente = proc.environ()
        cwd = proc.cwd()
    except (OSError, psutil.Error):
        print("NAO VERIFICADO: não foi possível inspecionar o processo.")
        return 2

    uri = ambiente.get("DATABASE_URL") or _ler_dotenv_sem_expor(cwd)
    tipo, resultado = _classificar_url(uri)

    print(f"Porta: {porta} | PID: {pid}")
    print(f"Classificação da conexão: {tipo}")
    print("Por segurança, nenhuma URL, credencial ou senha foi exibida.")
    if resultado != 0:
        print("BLOQUEADO: investigar o banco antes de testar gravação.")
    return resultado


if __name__ == "__main__":
    sys.exit(diagnosticar())
