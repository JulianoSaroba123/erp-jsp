/* Classificacao conservadora dos candidatos de conciliacao JSP.
 * Somente exibicao: nunca altera base financeira, nem conciliacao N:N.
 * A confirmacao permanece inteiramente manual e validada pelo servidor.
 */
(function (root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) {
        module.exports = api;
    }
    root.JSPConciliacaoMatch = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
    'use strict';

    const IGNORAR = new Set([
        'ltda', 'me', 'eireli', 'epp', 's a', 'sa', 'cia', 'comercio',
        'comercial', 'empresa', 'servico', 'servicos', 'industrial',
        'industriais', 'pagamento', 'pago', 'recebimento', 'recebida',
        'recebido', 'compra', 'pix', 'transferencia', 'transf',
        'banco', 'qr', 'code', 'de', 'da', 'do', 'das', 'dos', 'e',
        'posto', 'auto', 'proposta', 'referente', 'materiais',
        'material', 'despesa', 'retirada', 'parcela', 'conta',
        'limitada', 'instituicao', 'credito', 'debito'
    ]);

    function texto(valor) {
        return String(valor == null ? '' : valor)
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .toLowerCase().replace(/[^a-z0-9]+/g, ' ')
            .replace(/\s+/g, ' ').trim();
    }

    function centavos(valor) {
        const numero = Number(String(valor == null ? 0 : valor).replace(',', '.'));
        return Number.isFinite(numero) ? Math.round(Math.abs(numero) * 100) : 0;
    }

    function dataUTC(iso) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(String(iso || ''))) {
            return null;
        }
        const [ano, mes, dia] = iso.split('-').map(Number);
        const tempo = Date.UTC(ano, mes - 1, dia);
        const data = new Date(tempo);
        if (data.getUTCFullYear() !== ano ||
            data.getUTCMonth() + 1 !== mes || data.getUTCDate() !== dia) {
            return null;
        }
        return tempo;
    }

    function dias(extrato, titulo) {
        const a = dataUTC(extrato);
        const b = dataUTC(titulo);
        return a === null || b === null ? null : Math.round((a - b) / 86400000);
    }

    function tokens(valor) {
        return texto(valor).split(' ').filter(p => p.length >= 4 && !IGNORAR.has(p));
    }

    function documento(valor) {
        return String(valor || '').replace(/\D/g, '');
    }

    function evidenciaIdentidade(extrato, titulo) {
        const banco = texto([extrato.documento, extrato.descricao].join(' '));
        const docBanco = documento(extrato.documento);
        const documentos = [titulo.documentoCliente, titulo.documentoFornecedor];
        if ((docBanco.length === 11 || docBanco.length === 14) &&
            documentos.some(d => documento(d) === docBanco)) {
            return 3; // Mesmo CPF/CNPJ.
        }

        const nomes = [
            titulo.clienteNome, titulo.clienteRazao, titulo.clienteFantasia,
            titulo.fornecedorNome, titulo.fornecedorFantasia
        ];
        const tokensBanco = new Set(tokens(banco));
        for (const nome of nomes) {
            const t = tokens(nome);
            if (!t.length) continue;
            const iguais = t.filter(p => tokensBanco.has(p)).length;
            if (iguais >= 2 && iguais >= Math.min(2, t.length)) {
                return 2;
            }
            const nomeLimpo = texto(nome);
            if (nomeLimpo.length >= 8 && banco.includes(nomeLimpo)) {
                return 2;
            }
        }

        // Ultima opcao: descricao livre pode mencionar fornecedor.
        // Exigir 2 tokens informativos; palavras como "pagamento" nao contam.
        const palavras = tokens(titulo.descricao);
        const iguais = new Set(palavras.filter(p => tokensBanco.has(p)));
        return iguais.size >= 2 ? 1 : 0;
    }

    function compativel(tipoExtrato, tipoLancamento) {
        return tipoExtrato === 'credito'
            ? ['receita', 'conta_receber'].includes(tipoLancamento)
            : tipoExtrato === 'debito'
                ? ['despesa', 'conta_pagar'].includes(tipoLancamento)
                : false;
    }

    function avaliar(extrato, titulo) {
        const valido = Boolean(extrato && titulo &&
            compativel(extrato.tipo, titulo.tipo));
        const semDestaque = {
            compativel: valido,
            ocultarPadrao: true,
            pontuacao: -1,
            badge: '',
            classe: '',
            motivo: 'sem_indicios'
        };
        if (!valido) {
            return { ...semDestaque, motivo: 'natureza_incompativel' };
        }

        const valorBanco = centavos(extrato.valor);
        const valorTitulo = centavos(titulo.valor);
        if (!valorBanco || !valorTitulo || !dataUTC(extrato.data)) {
            return { ...semDestaque, motivo: 'dados_insuficientes' };
        }

        const dataReferencia = titulo.status === 'pago' ||
            titulo.status === 'recebido'
            ? (titulo.dataPagamento || titulo.dataLancamento || titulo.dataVencimento)
            : (titulo.dataVencimento || titulo.dataLancamento);
        const atraso = dias(extrato.data, dataReferencia);
        const proximidade = atraso === null ? 9999 : Math.abs(atraso);
        const liquidado = titulo.status === 'pago' || titulo.status === 'recebido';
        const valorIgual = Math.abs(valorBanco - valorTitulo) <= 1;
        const identidade = evidenciaIdentidade(extrato, titulo);

        // Um pagamento ja quitado ha semanas nao deve reaparecer como se
        // fosse um novo desembolso. Pode ser revelado manualmente, se legitimo.
        if (liquidado && atraso !== null && (atraso > 10 || atraso < -10)) {
            return { ...semDestaque, motivo: 'pagamento_antigo' };
        }

        // A conta pendente nunca fica bloqueada: e apenas retirada da
        // lista padrao quando nao ha indicios. Pode-se reve-la para 1:N/N:1.
        const atual = proximidade <= 14;
        const relevantePorIdentidade = identidade >= 2 &&
            (proximidade <= 90 || valorIgual);
        const relevantePorDescricao = identidade === 1 &&
            (proximidade <= 30 || valorIgual);
        const relevantePorValor = valorIgual &&
            (atual || titulo.status === 'pendente');
        const possivelParcial = !liquidado &&
            proximidade <= 5 && valorTitulo <= valorBanco &&
            valorTitulo >= valorBanco * 0.20;

        if (!relevantePorIdentidade && !relevantePorDescricao &&
            !relevantePorValor && !possivelParcial) {
            return { ...semDestaque, motivo: 'sem_indicios' };
        }

        const pontuacao = (identidade === 3 ? 180 :
            identidade === 2 ? 140 : identidade === 1 ? 70 : 0) +
            (valorIgual ? 60 : 0) +
            Math.max(0, 24 - Math.min(proximidade, 24)) +
            (possivelParcial ? 10 : 0);

        let badge = '';
        let classe = '';
        if (identidade >= 2 && valorIgual) {
            badge = 'Favorecido e valor compatíveis';
            classe = 'entidade';
        } else if (identidade >= 2) {
            badge = 'Favorecido compatível · confira o valor';
            classe = 'entidade';
        } else if (identidade === 1 && valorIgual) {
            badge = 'Descrição e valor compatíveis';
            classe = 'entidade';
        } else if (valorIgual && atual) {
            badge = 'Valor igual · confira a origem';
            classe = 'exato';
        } else if (identidade === 1) {
            badge = 'Descrição compatível · confira';
            classe = 'entidade';
        }
        // Uma data proxima e valor parcial, isoladamente, nao justificam
        // um selo de "melhor candidato".
        return {
            compativel: true, ocultarPadrao: false, pontuacao,
            badge, classe, motivo: 'candidato'
        };
    }

    return { avaliar, compativel, centavos, dias, evidenciaIdentidade };
});
