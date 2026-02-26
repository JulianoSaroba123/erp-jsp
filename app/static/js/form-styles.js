
// Forçar estilos de formulário
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 Aplicando estilos de formulário...');
    
    // Selecionar todos os inputs, textareas e selects
    const formElements = document.querySelectorAll('input, textarea, select');
    
    formElements.forEach(element => {
        // Aplicar estilos futuristas
        element.style.background = 'rgba(15, 52, 96, 0.1)';
        element.style.border = '1px solid var(--neon-blue)';
        element.style.color = 'var(--text-primary)';
        element.style.borderRadius = '15px';
        element.style.padding = '15px 20px';
        element.style.backdropFilter = 'blur(10px)';
        
        // Adicionar eventos de foco
        element.addEventListener('focus', function() {
            this.style.background = 'rgba(0, 212, 255, 0.15)';
            this.style.borderColor = 'var(--neon-cyan)';
            this.style.boxShadow = '0 0 20px rgba(0, 212, 255, 0.3)';
        });
        
        element.addEventListener('blur', function() {
            this.style.background = 'rgba(15, 52, 96, 0.1)';
            this.style.borderColor = 'var(--neon-blue)';
            this.style.boxShadow = 'none';
        });
    });
    
    // Também aplicar aos cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.background = 'rgba(15, 52, 96, 0.05)';
        card.style.border = '1px solid var(--neon-blue)';
        card.style.borderRadius = '20px';
        card.style.backdropFilter = 'blur(20px)';
    });
    
    console.log(`✅ Estilos aplicados a ${formElements.length} elementos de formulário`);
});
