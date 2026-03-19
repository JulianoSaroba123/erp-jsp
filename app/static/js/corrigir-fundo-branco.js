// =====================================================
// CORREÇÃO DINÂMICA DE FUNDO BRANCO - FORMULÁRIOS
// =====================================================

document.addEventListener('DOMContentLoaded', function() {
    
    function corrigirFundoBranco() {
        // Selecionar todos os elementos que podem ter fundo branco
        const elementos = document.querySelectorAll('*');
        
        elementos.forEach(element => {
            const computedStyle = window.getComputedStyle(element);
            const backgroundColor = computedStyle.backgroundColor;
            
            // Detectar fundos brancos ou claros
            const fundosBrancos = [
                'rgb(255, 255, 255)',
                'rgba(255, 255, 255, 1)',
                'white',
                '#ffffff',
                '#fff',
                'rgb(248, 249, 250)', // bg-light do Bootstrap
                'rgb(108, 117, 125)', // bg-secondary do Bootstrap
                'rgb(233, 236, 239)'  // outro cinza claro
            ];
            
            if (fundosBrancos.includes(backgroundColor)) {
                // Aplicar fundo escuro futurista
                element.style.setProperty('background', 'rgba(15, 52, 96, 0.05)', 'important');
                element.style.setProperty('color', '#E8F4FD', 'important');
                element.style.setProperty('border', '1px solid #00D4FF', 'important');
                element.style.setProperty('border-radius', '15px', 'important');
            }
            
            // Verificar e corrigir cards especificamente
            if (element.classList.contains('card') || element.classList.contains('card-body')) {
                element.style.setProperty('background', 'rgba(15, 52, 96, 0.05)', 'important');
                element.style.setProperty('border', '1px solid #00D4FF', 'important');
                element.style.setProperty('border-radius', '20px', 'important');
                element.style.setProperty('backdrop-filter', 'blur(20px)', 'important');
            }
        });
    }
    
    // Executar correção inicial
    corrigirFundoBranco();
    
    // Observar mudanças no DOM para corrigir elementos dinâmicos
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Aguardar um momento para DOM se estabilizar
                setTimeout(corrigirFundoBranco, 100);
            }
        });
    });
    
    // Iniciar observação
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Executar correção também quando a página estiver totalmente carregada
window.addEventListener('load', function() {
    setTimeout(function() {
        // Correção final mais agressiva
        const todosElementos = document.querySelectorAll('*');
        todosElementos.forEach(el => {
            const style = window.getComputedStyle(el);
            
            if (style.backgroundColor === 'rgb(255, 255, 255)' || 
                style.backgroundColor === 'white' ||
                style.backgroundColor === 'rgba(255, 255, 255, 1)') {
                
                el.style.setProperty('background', 'rgba(15, 52, 96, 0.05)', 'important');
                el.style.setProperty('color', '#E8F4FD', 'important');
            }
        });
    }, 1000);
});

console.log('🎨 Sistema de correção de fundo branco carregado!');