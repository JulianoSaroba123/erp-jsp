// TESTE MANUAL DO SISTEMA DE HORAS
// Cole este código no console do navegador (F12) para testar

console.log('=== TESTE SISTEMA DE HORAS ===');

// 1. Verificar se os campos existem
const totalHoras = document.getElementById('total_horas');
const totalHorasDisplay = document.getElementById('total_horas_display');

console.log('Campo total_horas:', totalHoras ? 'ENCONTRADO' : 'NÃO ENCONTRADO');
console.log('Campo total_horas_display:', totalHorasDisplay ? 'ENCONTRADO' : 'NÃO ENCONTRADO');

if (totalHoras && totalHorasDisplay) {
    console.log('✅ Ambos os campos existem');
    
    // 2. Teste de sincronização manual
    console.log('🧪 Testando sincronização...');
    
    totalHoras.value = '5.5';
    totalHorasDisplay.value = '5.5h';
    
    console.log('Valores atualizados:');
    console.log('- total_horas:', totalHoras.value);
    console.log('- total_horas_display:', totalHorasDisplay.value);
    
    // 3. Disparar evento para testar listeners
    totalHoras.dispatchEvent(new Event('input'));
    
    setTimeout(() => {
        console.log('Após evento input:');
        console.log('- total_horas:', totalHoras.value);
        console.log('- total_horas_display:', totalHorasDisplay.value);
        
        if (totalHorasDisplay.value === '5.5h') {
            console.log('🎉 TESTE APROVADO! Sistema funcionando!');
        } else {
            console.log('❌ TESTE FALHOU! Sistema não está sincronizando');
        }
    }, 1000);
    
} else {
    console.log('❌ ERRO: Campos não encontrados na página');
}

console.log('=== FIM DO TESTE ===');