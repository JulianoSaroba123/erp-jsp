/* Testes sem DOM e sem banco. Execução: node scripts_manutencao/testes/js/test_conciliacao_match.cjs */
'use strict';
const assert = require('node:assert/strict');
const m = require('../../../app/static/js/conciliacao_match.js');

function extrato(adicionais = {}) {
    return {
        tipo: 'debito',
        valor: 100,
        data: '2026-10-01',
        documento: 'SAN RAPHAELL CENT',
        descricao: 'Compra no débito',
        ...adicionais
    };
}
function titulo(adicionais = {}) {
    return {
        tipo: 'conta_pagar',
        valor: 100,
        status: 'pago',
        dataLancamento: '2026-10-01',
        dataVencimento: '2026-10-01',
        dataPagamento: '2026-10-01',
        descricao: 'Compra operacional',
        ...adicionais
    };
}

// DAS 04/2026 liquidado em agosto: não é "melhor" para débito outubro.
let r = m.avaliar(extrato(), titulo({
    descricao: 'DAS Simples Nacional competência 04/2026',
    valor: 1237.49, dataLancamento: '2026-08-29',
    dataPagamento: '2026-08-31', dataVencimento: '2026-08-31'
}));
assert.equal(r.ocultarPadrao, true);
assert.equal(r.motivo, 'pagamento_antigo');
assert.equal(r.badge, '');

// Pró-labore pendente, valor incompatível e sem evidência de favorecido.
r = m.avaliar(extrato(), titulo({
    descricao: 'Pró-labore setembro/2026',
    tipo: 'conta_pagar', status: 'pendente', valor: 2613.90,
    dataLancamento: '2026-08-29', dataVencimento: '2026-09-10', dataPagamento: ''
}));
assert.equal(r.ocultarPadrao, true);
assert.equal(r.badge, '');

// Um título de agosto pago não deve reaparecer apenas porque tem mesmo valor.
r = m.avaliar(extrato(), titulo({
    descricao: 'Abastecimento antigo',
    dataLancamento: '2026-08-31', dataPagamento: '',
    dataVencimento: '2026-08-31'
}));
assert.equal(r.ocultarPadrao, true);

// Outro pagamento de setembro já quitado não aparece em outubro sem contexto.
r = m.avaliar(extrato(), titulo({
    dataLancamento: '2026-09-15',
    dataVencimento: '2026-09-15',
    dataPagamento: '2026-09-15'
}));
assert.equal(r.ocultarPadrao, true);

// Pagamento dentro da janela, valor igual, mas favorecido diferente:
// pode sugerir comparação de VALOR, nunca "melhor" ou "fornecedor conferido".
r = m.avaliar(extrato(), titulo({
    descricao: 'Abastecimento Auto Posto Vila Real',
    fornecedorNome: 'Auto Posto Vila Real'
}));
assert.equal(r.ocultarPadrao, false);
assert.match(r.badge, /^Valor igual/);
assert.doesNotMatch(r.badge, /melhor candidato/i);

// Fornecedor e valor conferem por nome.
r = m.avaliar(extrato({
    data: '2026-10-09', valor: 82.65, documento: 'F F BORTOLAZO LIMITADA',
    descricao: 'Pgto QR Code Pix'
}), titulo({
    tipo: 'despesa', valor: 82.65, fornecedorNome: 'F F Bortolazo',
    descricao: 'Compra de ferramentas',
    dataLancamento: '2026-10-09', dataPagamento: '2026-10-09',
    dataVencimento: '2026-10-09'
}));
assert.equal(r.ocultarPadrao, false);
assert.match(r.badge, /Favorecido e valor/);

// Mesmo beneficiário com valores diferentes: permitir conciliação parcial N:N.
for (const valor of [450, 540]) {
    r = m.avaliar(extrato({
        tipo: 'credito', data: '2026-10-03', valor: 990,
        documento: 'MR Jacky', descricao: 'Transf Pix recebida'
    }), titulo({
        tipo: 'conta_receber', status: 'recebido', valor,
        clienteNome: 'MR Jacky',
        dataLancamento: '2026-10-02', dataVencimento: '2026-10-03',
        dataPagamento: '2026-10-03'
    }));
    assert.equal(r.ocultarPadrao, false);
    assert.match(r.badge, /Favorecido/);
}

// Pagamentos de títulos vencidos em meses anteriores são visíveis se valor igual
// e ainda pendentes, para quitação bancária real em outubro.
r = m.avaliar(extrato({valor: 200}), titulo({
    tipo: 'conta_pagar', status: 'pendente', valor: 200,
    dataLancamento: '2026-08-10', dataVencimento: '2026-09-01',
    dataPagamento: ''
}));
assert.equal(r.ocultarPadrao, false);

// Parcelamento N:N sem favorecido comprovado continua acessível, mas sem selo.
r = m.avaliar(extrato({valor: 400}), titulo({
    status: 'pendente', valor: 100, dataPagamento: ''
}));
assert.equal(r.ocultarPadrao, false);
assert.equal(r.badge, '');

// Crédito não pode casar com conta a pagar.
r = m.avaliar(extrato({tipo: 'credito'}), titulo());
assert.equal(r.compativel, false);
assert.equal(r.ocultarPadrao, true);

// Verificações defensivas contra data inválida, valores não numéricos e mutação.
const e = extrato({data:'2026-02-30',valor:'invalido'});
const l = titulo();
const eAntes = JSON.stringify(e), lAntes = JSON.stringify(l);
r = m.avaliar(e, l);
assert.equal(r.ocultarPadrao, true);
assert.equal(JSON.stringify(e), eAntes);
assert.equal(JSON.stringify(l), lAntes);

console.log('Testes do ranking conservador da conciliação: aprovados');
