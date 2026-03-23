/**
 * Sistema de Cálculo de Horários Detalhado
 * 6 campos de entrada + cálculo automático em tempo real
 */

function calcularTotalHoras() {
    const entradaManha = document.getElementById('hora_entrada_manha')?.value;
    const saidaAlmoco = document.getElementById('hora_saida_almoco')?.value;
    const retornoAlmoco = document.getElementById('hora_retorno_almoco')?.value;
    const saida = document.getElementById('hora_saida')?.value;
    const entradaExtra = document.getElementById('hora_entrada_extra')?.value;
    const saidaExtra = document.getElementById('hora_saida_extra')?.value;
    
    const horasNormaisField = document.getElementById('horasNormais');
    const horasExtrasField = document.getElementById('horasExtras');
    const totalHorasDisplay = document.getElementById('totalHorasDisplay');
    const totalHorasNormaisDisplay = document.getElementById('totalHorasNormaisDisplay');
    const totalHorasExtrasDisplay = document.getElementById('totalHorasExtrasDisplay');
    
    let horasNormaisMinutos = 0;
    let horasExtrasMinutos = 0;
    
    // Calcular horas normais: (Saída Almoço - Entrada Manhã) + (Saída - Retorno Almoço)
    if (entradaManha && saidaAlmoco) {
        const [hEntrada, mEntrada] = entradaManha.split(':').map(Number);
        const [hSaida, mSaida] = saidaAlmoco.split(':').map(Number);
        
        let minutosEntrada = hEntrada * 60 + mEntrada;
        let minutosSaida = hSaida * 60 + mSaida;
        
        if (minutosSaida > minutosEntrada) {
            horasNormaisMinutos += (minutosSaida - minutosEntrada);
        }
    }
    
    if (retornoAlmoco && saida) {
        const [hRetorno, mRetorno] = retornoAlmoco.split(':').map(Number);
        const [hSaida2, mSaida2] = saida.split(':').map(Number);
        
        let minutosRetorno = hRetorno * 60 + mRetorno;
        let minutosSaida2 = hSaida2 * 60 + mSaida2;
        
        if (minutosSaida2 > minutosRetorno) {
            horasNormaisMinutos += (minutosSaida2 - minutosRetorno);
        }
    }
    
    // Calcular horas extras: Saída Extra - Entrada Extra
    if (entradaExtra && saidaExtra) {
        const [hEntradaEx, mEntradaEx] = entradaExtra.split(':').map(Number);
        const [hSaidaEx, mSaidaEx] = saidaExtra.split(':').map(Number);
        
        let minutosEntradaEx = hEntradaEx * 60 + mEntradaEx;
        let minutosSaidaEx = hSaidaEx * 60 + mSaidaEx;
        
        if (minutosSaidaEx > minutosEntradaEx) {
            horasExtrasMinutos += (minutosSaidaEx - minutosEntradaEx);
        }
    }
    
    // Formatar horas normais
    if (horasNormaisMinutos > 0) {
        const h = Math.floor(horasNormaisMinutos / 60);
        const m = horasNormaisMinutos % 60;
        const textoFormatado = `${h}h ${m.toString().padStart(2, '0')}min`;
        
        if (horasNormaisField) horasNormaisField.value = textoFormatado;
        if (totalHorasNormaisDisplay) totalHorasNormaisDisplay.textContent = textoFormatado;
    } else {
        if (horasNormaisField) horasNormaisField.value = '';
        if (totalHorasNormaisDisplay) totalHorasNormaisDisplay.textContent = '0h 00min';
    }
    
    // Formatar horas extras
    if (horasExtrasMinutos > 0) {
        const h = Math.floor(horasExtrasMinutos / 60);
        const m = horasExtrasMinutos % 60;
        const textoFormatado = `${h}h ${m.toString().padStart(2, '0')}min`;
        
        if (horasExtrasField) horasExtrasField.value = textoFormatado;
        if (totalHorasExtrasDisplay) totalHorasExtrasDisplay.textContent = textoFormatado;
    } else {
        if (horasExtrasField) horasExtrasField.value = '';
        if (totalHorasExtrasDisplay) totalHorasExtrasDisplay.textContent = '0h 00min';
    }
    
    // Calcular total
    const totalMinutos = horasNormaisMinutos + horasExtrasMinutos;
    if (totalMinutos > 0 && totalHorasDisplay) {
        const h = Math.floor(totalMinutos / 60);
        const m = totalMinutos % 60;
        totalHorasDisplay.textContent = `${h}h ${m.toString().padStart(2, '0')}min`;
    } else if (totalHorasDisplay) {
        totalHorasDisplay.textContent = '0h 00min';
    }
}

function calcularTotalKm() {
    const kmInicial = parseFloat(document.querySelector('input[name="km_inicial"]')?.value) || 0;
    const kmFinal = parseFloat(document.querySelector('input[name="km_final"]')?.value) || 0;
    const totalKmField = document.getElementById('totalKm');
    const kmTotalDisplay = document.getElementById('totalKmDisplay');
    
    if (kmFinal > kmInicial) {
        const totalKm = kmFinal - kmInicial;
        if (totalKmField) totalKmField.value = `${totalKm} km`;
        if (kmTotalDisplay) kmTotalDisplay.textContent = `${totalKm} km`;
    } else {
        if (totalKmField) totalKmField.value = '';
        if (kmTotalDisplay) kmTotalDisplay.textContent = '0 km';
    }
}

function inicializarCalculoHorarios() {
    console.log('✅ Inicializando sistema de cálculo de horários...');
    
    const horaEntradaManhaInput = document.getElementById('hora_entrada_manha');
    const horaSaidaAlmocoInput = document.getElementById('hora_saida_almoco');
    const horaRetornoAlmocoInput = document.getElementById('hora_retorno_almoco');
    const horaSaidaInput = document.getElementById('hora_saida');
    const horaEntradaExtraInput = document.getElementById('hora_entrada_extra');
    const horaSaidaExtraInput = document.getElementById('hora_saida_extra');
    const kmInicialInput = document.querySelector('input[name="km_inicial"]');
    const kmFinalInput = document.querySelector('input[name="km_final"]');
    
    // Adicionar listeners 'input' e 'change' para cálculo instantâneo
    if (horaEntradaManhaInput) {
        horaEntradaManhaInput.addEventListener('input', calcularTotalHoras);
        horaEntradaManhaInput.addEventListener('change', calcularTotalHoras);
    }
    if (horaSaidaAlmocoInput) {
        horaSaidaAlmocoInput.addEventListener('input', calcularTotalHoras);
        horaSaidaAlmocoInput.addEventListener('change', calcularTotalHoras);
    }
    if (horaRetornoAlmocoInput) {
        horaRetornoAlmocoInput.addEventListener('input', calcularTotalHoras);
        horaRetornoAlmocoInput.addEventListener('change', calcularTotalHoras);
    }
    if (horaSaidaInput) {
        horaSaidaInput.addEventListener('input', calcularTotalHoras);
        horaSaidaInput.addEventListener('change', calcularTotalHoras);
    }
    if (horaEntradaExtraInput) {
        horaEntradaExtraInput.addEventListener('input', calcularTotalHoras);
        horaEntradaExtraInput.addEventListener('change', calcularTotalHoras);
    }
    if (horaSaidaExtraInput) {
        horaSaidaExtraInput.addEventListener('input', calcularTotalHoras);
        horaSaidaExtraInput.addEventListener('change', calcularTotalHoras);
    }
    
    if (kmInicialInput) {
        kmInicialInput.addEventListener('input', calcularTotalKm);
        kmInicialInput.addEventListener('change', calcularTotalKm);
    }
    if (kmFinalInput) {
        kmFinalInput.addEventListener('input', calcularTotalKm);
        kmFinalInput.addEventListener('change', calcularTotalKm);
    }
    
    // Calcular valores iniciais
    setTimeout(() => {
        calcularTotalHoras();
        calcularTotalKm();
    }, 100);
    
    console.log('✅ Sistema de cálculo de horários pronto!');
}

// Exportar funções para uso global
window.calcularTotalHoras = calcularTotalHoras;
window.calcularTotalKm = calcularTotalKm;
window.inicializarCalculoHorarios = inicializarCalculoHorarios;
