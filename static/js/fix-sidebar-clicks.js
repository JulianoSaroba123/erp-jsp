/* ============================================
   🔧 CORREÇÃO DOS CLIQUES NA SIDEBAR
============================================ */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Iniciando correção dos cliques na sidebar...');
    
    // Verificar se a sidebar existe
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) {
        console.error('❌ Sidebar não encontrada!');
        return;
    }
    
    // Garantir que a sidebar tenha z-index adequado
    sidebar.style.zIndex = '1000';
    sidebar.style.pointerEvents = 'auto';
    
    // Verificar todos os links da sidebar
    const navLinks = sidebar.querySelectorAll('.nav-link');
    console.log(`🔍 Encontrados ${navLinks.length} links na sidebar`);
    
    navLinks.forEach((link, index) => {
        // Garantir que o link seja clicável
        link.style.pointerEvents = 'auto';
        link.style.position = 'relative';
        link.style.zIndex = '1001';
        
        // Remover qualquer event listener que possa estar bloqueando
        const newLink = link.cloneNode(true);
        link.parentNode.replaceChild(newLink, link);
        
        // Adicionar novo event listener limpo
        newLink.addEventListener('click', function(e) {
            console.log(`🎯 Clique detectado no link: ${newLink.href}`);
            
            // Verificar se é um link válido
            if (newLink.href && newLink.href !== '#') {
                // Adicionar indicador visual de carregamento
                newLink.style.opacity = '0.7';
                setTimeout(() => {
                    if (newLink.style) {
                        newLink.style.opacity = '1';
                    }
                }, 200);
                
                // Permitir navegação normal
                return true;
            } else {
                console.warn('⚠️ Link sem href válido');
                e.preventDefault();
                return false;
            }
        });
        
        console.log(`✅ Link ${index + 1} configurado: ${newLink.textContent.trim()}`);
    });
    
    // Verificar elementos que podem estar sobrepondo
    const allElements = document.querySelectorAll('*');
    let overlappingElements = [];
    
    allElements.forEach(el => {
        const style = window.getComputedStyle(el);
        const zIndex = parseInt(style.zIndex);
        const position = style.position;
        
        // Verificar elementos com z-index alto que podem sobrepor
        if (zIndex > 1000 && (position === 'fixed' || position === 'absolute')) {
            const rect = el.getBoundingClientRect();
            
            // Verificar se o elemento está na área da sidebar (geralmente à esquerda)
            if (rect.left < 300) {
                overlappingElements.push({
                    element: el,
                    zIndex: zIndex,
                    className: el.className,
                    id: el.id
                });
            }
        }
    });
    
    if (overlappingElements.length > 0) {
        console.warn('⚠️ Elementos que podem estar sobrepondo a sidebar:');
        overlappingElements.forEach(item => {
            console.log('  -', item.element, 'z-index:', item.zIndex);
            
            // Se não for um modal ou dropdown importante, reduzir o z-index
            if (!item.className.includes('modal') && 
                !item.className.includes('dropdown') && 
                !item.className.includes('tooltip')) {
                item.element.style.zIndex = '999';
                console.log('  -> z-index reduzido para 999');
            }
        });
    }
    
    // Função de teste para os links
    window.testSidebarLinks = function() {
        console.log('🧪 Testando todos os links da sidebar...');
        const links = document.querySelectorAll('.sidebar .nav-link');
        
        links.forEach((link, index) => {
            console.log(`Link ${index + 1}:`, {
                href: link.href,
                text: link.textContent.trim(),
                style: {
                    pointerEvents: window.getComputedStyle(link).pointerEvents,
                    zIndex: window.getComputedStyle(link).zIndex,
                    position: window.getComputedStyle(link).position
                }
            });
        });
    };
    
    // Função para forçar clique em um link específico
    window.forceClickSidebarLink = function(linkText) {
        const links = document.querySelectorAll('.sidebar .nav-link');
        const targetLink = Array.from(links).find(link => 
            link.textContent.trim().toLowerCase().includes(linkText.toLowerCase())
        );
        
        if (targetLink) {
            console.log(`🎯 Forçando clique em: ${targetLink.textContent.trim()}`);
            window.location.href = targetLink.href;
        } else {
            console.error(`❌ Link não encontrado: ${linkText}`);
        }
    };
    
    console.log('✅ Correção dos cliques na sidebar concluída!');
    console.log('💡 Use testSidebarLinks() para verificar os links');
    console.log('💡 Use forceClickSidebarLink("nome") para navegar');
});

/* Correção adicional para mobile */
document.addEventListener('touchstart', function(e) {
    const target = e.target.closest('.nav-link');
    if (target && target.closest('.sidebar')) {
        console.log('📱 Touch detectado na sidebar');
        target.style.backgroundColor = 'rgba(0, 212, 255, 0.1)';
        
        setTimeout(() => {
            if (target.style) {
                target.style.backgroundColor = '';
            }
        }, 200);
    }
}, { passive: true });