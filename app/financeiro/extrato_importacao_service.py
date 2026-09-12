from __future__ import annotations

import csv
import hashlib
import html
import io
import os
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable


class ErroImportacaoExtrato(ValueError):
    """Erro estrutural que impede a leitura do arquivo de extrato."""


@dataclass
class ResultadoParseExtrato:
    movimentos: list[dict] = field(default_factory=list)
    erros: list[dict] = field(default_factory=list)
    formato: str = ""


# ---------------------------------------------------------------------------
# Normalizacao
# ---------------------------------------------------------------------------

def _sem_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto or "")
    return "".join(ch for ch in normalizado if not unicodedata.combining(ch))


def _normalizar_cabecalho(texto: str) -> str:
    texto = _sem_acentos(texto).casefold().strip()
    return re.sub(r"\s+", " ", texto)


def _normalizar_texto_chave(texto: str | None) -> str:
    texto = html.unescape(texto or "")
    texto = _sem_acentos(texto).casefold().strip()
    return re.sub(r"\s+", " ", texto)


def _limpar_texto(texto: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(texto or "").strip())


def _decodificar(conteudo: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return conteudo.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ErroImportacaoExtrato("Nao foi possivel identificar a codificacao do arquivo.")


def _parse_valor(valor_raw: str) -> Decimal:
    texto = (valor_raw or "").strip()
    texto = texto.replace("R$", "").replace(" ", "")
    if not texto:
        raise ErroImportacaoExtrato("Valor vazio.")

    # Suporta 1.234,56, 1,234.56, 1234,56 e 1234.56.
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(".", "").replace(",", ".")

    try:
        return Decimal(texto)
    except InvalidOperation as exc:
        raise ErroImportacaoExtrato(f"Valor invalido: {valor_raw!r}.") from exc


def _parse_data_csv(data_raw: str) -> date:
    texto = (data_raw or "").strip()

    match = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", texto)
    if match:
        dia, mes, ano = map(int, match.groups())
    else:
        match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", texto)
        if not match:
            raise ErroImportacaoExtrato(f"Formato de data nao suportado: {data_raw!r}.")
        ano, mes, dia = map(int, match.groups())

    try:
        return date(ano, mes, dia)
    except ValueError as exc:
        raise ErroImportacaoExtrato(f"Data invalida: {data_raw!r}.") from exc


def _tipo_movimento(tipo_raw: str | None, valor: Decimal) -> tuple[str, Decimal]:
    tipo = _normalizar_cabecalho(tipo_raw or "")
    mapa = {
        "credito": "credito",
        "credit": "credito",
        "c": "credito",
        "debito": "debito",
        "debit": "debito",
        "d": "debito",
    }
    tipo_normalizado = mapa.get(tipo)

    # Quando o arquivo informa o tipo, ele prevalece sobre o sinal do valor.
    # Isso preserva compatibilidade com o CSV legado, que pode trazer debito positivo.
    if tipo_normalizado == "credito":
        return "credito", abs(valor)
    if tipo_normalizado == "debito":
        return "debito", -abs(valor)

    if valor < 0:
        return "debito", valor
    return "credito", valor


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

def _detectar_delimitador(texto: str) -> str:
    amostra = texto[:4096]
    try:
        return csv.Sniffer().sniff(amostra, delimiters=",;").delimiter
    except csv.Error:
        linhas = amostra.splitlines()
        primeira_linha = linhas[0] if linhas else ""
        return ";" if primeira_linha.count(";") > primeira_linha.count(",") else ","


def _resolver_colunas(fieldnames: Iterable[str] | None) -> tuple[dict[str, str | None], str]:
    normalizadas = {
        _normalizar_cabecalho(nome): nome
        for nome in (fieldnames or [])
        if nome is not None
    }

    def achar(*aliases: str) -> str | None:
        for alias in aliases:
            encontrado = normalizadas.get(_normalizar_cabecalho(alias))
            if encontrado:
                return encontrado
        return None

    colunas = {
        "data": achar("Data"),
        "descricao": achar("Transacao", "Descricao"),
        "tipo": achar("Tipo Transacao", "Tipo", "Tipo Movimento"),
        "identificacao": achar("Identificacao"),
        "documento": achar("Documento"),
        "valor": achar("Valor"),
    }

    faltantes = [nome for nome in ("data", "descricao", "valor") if not colunas[nome]]
    if faltantes:
        raise ErroImportacaoExtrato(
            "Colunas obrigatorias ausentes: " + ", ".join(faltantes) + "."
        )

    cabecalhos = set(normalizadas)
    formato = "cora_csv" if {
        "data", "transacao", "tipo transacao", "identificacao", "valor"
    }.issubset(cabecalhos) else "csv_legado"

    return colunas, formato


def parse_csv(conteudo: bytes) -> ResultadoParseExtrato:
    """Le o CSV real do Cora e mantem compatibilidade com o formato legado."""
    texto = _decodificar(conteudo)
    delimitador = _detectar_delimitador(texto)
    reader = csv.DictReader(io.StringIO(texto, newline=None), delimiter=delimitador)
    colunas, formato = _resolver_colunas(reader.fieldnames)

    resultado = ResultadoParseExtrato(formato=formato)

    for numero_linha, row in enumerate(reader, start=2):
        valores_texto = [valor for valor in row.values() if isinstance(valor, str)]
        if not any((valor or "").strip() for valor in valores_texto):
            continue

        try:
            data_movimento = _parse_data_csv(row.get(colunas["data"] or "", ""))
            descricao = _limpar_texto(row.get(colunas["descricao"] or "", ""))
            if not descricao:
                raise ErroImportacaoExtrato("Descricao vazia.")

            valor_lido = _parse_valor(row.get(colunas["valor"] or "", ""))
            tipo_raw = row.get(colunas["tipo"] or "", "") if colunas["tipo"] else ""
            tipo, valor_assinado = _tipo_movimento(tipo_raw, valor_lido)

            identificacao = ""
            if colunas["identificacao"]:
                identificacao = _limpar_texto(
                    row.get(colunas["identificacao"] or "", "")
                )

            documento = ""
            if colunas["documento"]:
                documento = _limpar_texto(row.get(colunas["documento"] or "", ""))
                if not identificacao:
                    identificacao = documento

            resultado.movimentos.append({
                "data_movimento": data_movimento,
                "descricao": descricao,
                "identificacao": identificacao,
                "documento": documento,
                "valor_assinado": valor_assinado,
                "valor": abs(valor_assinado),
                "tipo_movimento": tipo,
                "identificador_externo": None,
                "origem": formato,
                "linha_origem": numero_linha,
            })
        except Exception as exc:
            resultado.erros.append({
                "linha": numero_linha,
                "erro": str(exc),
            })

    if not resultado.movimentos and not resultado.erros:
        raise ErroImportacaoExtrato("Nenhum movimento foi encontrado no CSV.")

    return resultado


# ---------------------------------------------------------------------------
# OFX Cora 1.x / SGML
# ---------------------------------------------------------------------------

def _tag(bloco: str, nome: str) -> str:
    # Funciona tanto com folha fechada (<TAG>x</TAG>) quanto com OFX SGML 1.x.
    match = re.search(
        rf"<{re.escape(nome)}>\s*([^<\r\n]*)",
        bloco,
        flags=re.IGNORECASE,
    )
    return _limpar_texto(match.group(1)) if match else ""


def _parse_data_ofx(valor: str) -> date:
    match = re.match(r"^(\d{4})(\d{2})(\d{2})", (valor or "").strip())
    if not match:
        raise ErroImportacaoExtrato(f"DTPOSTED invalido: {valor!r}.")
    ano, mes, dia = map(int, match.groups())
    try:
        return date(ano, mes, dia)
    except ValueError as exc:
        raise ErroImportacaoExtrato(f"DTPOSTED invalido: {valor!r}.") from exc


def _parse_memo_cora(memo: str) -> tuple[str, str, str]:
    # Cora: "Transacao - Identificacao - CPF/CNPJ".
    # O \s* final e importante para casos de cartao que terminam apenas em " -".
    partes = re.split(r"\s+-\s*", memo.strip(), maxsplit=2)
    descricao = _limpar_texto(partes[0] if partes else memo)
    identificacao = _limpar_texto(partes[1] if len(partes) > 1 else "")
    documento = _limpar_texto(partes[2] if len(partes) > 2 else "")
    return descricao, identificacao, documento


def parse_ofx(conteudo: bytes) -> ResultadoParseExtrato:
    """Le OFX SGML 1.x do Cora sem dependencia externa."""
    texto = _decodificar(conteudo)
    blocos = re.findall(
        r"<STMTTRN>(.*?)</STMTTRN>",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not blocos:
        raise ErroImportacaoExtrato("Nenhuma transacao STMTTRN foi encontrada no OFX.")

    resultado = ResultadoParseExtrato(formato="cora_ofx")

    for indice, bloco in enumerate(blocos, start=1):
        try:
            data_movimento = _parse_data_ofx(_tag(bloco, "DTPOSTED"))
            valor_lido = _parse_valor(_tag(bloco, "TRNAMT"))
            tipo, valor_assinado = _tipo_movimento(_tag(bloco, "TRNTYPE"), valor_lido)
            fitid = _tag(bloco, "FITID") or None
            memo = _tag(bloco, "MEMO") or _tag(bloco, "NAME")
            descricao, identificacao, documento = _parse_memo_cora(memo)
            if not descricao:
                raise ErroImportacaoExtrato("MEMO/NAME vazio.")

            resultado.movimentos.append({
                "data_movimento": data_movimento,
                "descricao": descricao,
                "identificacao": identificacao,
                "documento": documento,
                "valor_assinado": valor_assinado,
                "valor": abs(valor_assinado),
                "tipo_movimento": tipo,
                "identificador_externo": fitid,
                "origem": "cora_ofx",
                "linha_origem": indice,
            })
        except Exception as exc:
            resultado.erros.append({
                "linha": indice,
                "erro": str(exc),
            })

    return resultado


# ---------------------------------------------------------------------------
# Entrada unica + fingerprint
# ---------------------------------------------------------------------------

def parse_arquivo(conteudo: bytes, nome_arquivo: str) -> ResultadoParseExtrato:
    extensao = os.path.splitext((nome_arquivo or "").lower())[1]
    if extensao == ".ofx":
        return parse_ofx(conteudo)
    if extensao == ".csv":
        return parse_csv(conteudo)
    raise ErroImportacaoExtrato(
        f"Formato nao suportado: {extensao or 'sem extensao'}. Use .ofx ou .csv."
    )


def gerar_fingerprints(movimentos: list[dict], conta_chave: str = "") -> list[dict]:
    """
    Gera fingerprint deterministico comum a CSV e OFX.

    O contador de ocorrencia preserva duas compras legitimamente identicas no mesmo dia,
    como ocorre no extrato real do Cora.
    """
    ocorrencias: defaultdict[str, int] = defaultdict(int)

    for movimento in movimentos:
        valor = Decimal(movimento["valor_assinado"]).quantize(Decimal("0.01"))
        base = "|".join([
            _normalizar_texto_chave(conta_chave),
            movimento["data_movimento"].isoformat(),
            format(valor, "f"),
            _normalizar_texto_chave(movimento["tipo_movimento"]),
            _normalizar_texto_chave(movimento["descricao"]),
            _normalizar_texto_chave(movimento.get("identificacao")),
        ])

        ocorrencias[base] += 1
        material = f"{base}|{ocorrencias[base]}"
        movimento["fingerprint"] = hashlib.sha256(
            material.encode("utf-8")
        ).hexdigest()
        movimento["ocorrencia"] = ocorrencias[base]

    return movimentos


def resumir_movimentos(movimentos: list[dict]) -> dict:
    creditos = [m for m in movimentos if m["tipo_movimento"] == "credito"]
    debitos = [m for m in movimentos if m["tipo_movimento"] == "debito"]

    total_creditos = sum(
        (Decimal(m["valor"]) for m in creditos),
        Decimal("0.00"),
    )
    total_debitos = sum(
        (Decimal(m["valor"]) for m in debitos),
        Decimal("0.00"),
    )

    return {
        "movimentos": len(movimentos),
        "creditos": len(creditos),
        "debitos": len(debitos),
        "total_creditos": total_creditos.quantize(Decimal("0.01")),
        "total_debitos": total_debitos.quantize(Decimal("0.01")),
        "liquido": (total_creditos - total_debitos).quantize(Decimal("0.01")),
    }
