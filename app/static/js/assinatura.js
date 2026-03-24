/**
 * Sistema de Assinaturas Digitais para Ordens de Serviço
 * Utiliza Signature Pad para captura de assinaturas
 */

class AssinaturaManager {
    constructor() {
        this.signaturePads = {};
        this.canvases = {};
    }

    /**
     * Inicializa um canvas de assinatura
     * @param {string} tipo - 'cliente' ou 'tecnico'
     */
    inicializar(tipo) {
        const canvasId = `canvas-assinatura-${tipo}`;
        const canvas = document.getElementById(canvasId);
        
        if (!canvas) {
            console.error(`Canvas ${canvasId} não encontrado`);
            return;
        }

        // Ajusta o tamanho do canvas para tela retina
        const ratio = Math.max(window.devicePixelRatio || 1, 1);
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * ratio;
        canvas.height = rect.height * ratio;
        canvas.getContext('2d').scale(ratio, ratio);
        
        // Inicializa o Signature Pad
        this.signaturePads[tipo] = new SignaturePad(canvas, {
            backgroundColor: 'rgb(255, 255, 255)',
            penColor: 'rgb(0, 0, 0)',
            minWidth: 1,
            maxWidth: 2.5,
            velocityFilterWeight: 0.7
        });

        this.canvases[tipo] = canvas;
        
        console.log(`✓ Assinatura ${tipo} inicializada`);
    }

    /**
     * Abre o modal de assinatura
     * @param {string} tipo - 'cliente' ou 'tecnico'
     */
    abrirModal(tipo) {
        const modalId = `modal-assinatura-${tipo}`;
        const modal = document.getElementById(modalId);
        
        if (!modal) {
            console.error(`Modal ${modalId} não encontrado`);
            return;
        }

        // Mostra o modal usando Bootstrap
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        // Aguarda o modal estar visível para inicializar o canvas
        setTimeout(() => {
            this.inicializar(tipo);
            
            // Carrega assinatura existente se houver
            const inputAssinatura = document.getElementById(`assinatura_${tipo}`);
            if (inputAssinatura && inputAssinatura.value) {
                this.carregarAssinatura(tipo, inputAssinatura.value);
            }
        }, 300);
    }

    /**
     * Limpa o canvas de assinatura
     * @param {string} tipo - 'cliente' ou 'tecnico'
     */
    limpar(tipo) {
        if (this.signaturePads[tipo]) {
            this.signaturePads[tipo].clear();
            console.log(`✓ Assinatura ${tipo} limpa`);
        }
    }

    /**
     * Salva a assinatura
     * @param {string} tipo - 'cliente' ou 'tecnico'
     */
    salvar(tipo) {
        const signaturePad = this.signaturePads[tipo];
        
        if (!signaturePad) {
            alert('Erro: Canvas de assinatura não inicializado');
            return;
        }

        if (signaturePad.isEmpty()) {
            alert('Por favor, faça a assinatura antes de salvar');
            return;
        }

        // Obtém a assinatura em formato base64 (PNG)
        const dataURL = signaturePad.toDataURL('image/png');
        
        // Salva no campo hidden do formulário
        const inputAssinatura = document.getElementById(`assinatura_${tipo}`);
        if (inputAssinatura) {
            inputAssinatura.value = dataURL;
        }

        // Atualiza o nome de quem assinou
        const inputNome = document.getElementById(`assinatura_${tipo}_nome`);
        const nomeInput = document.getElementById(`nome-assinante-${tipo}`);
        if (inputNome && nomeInput) {
            inputNome.value = nomeInput.value || '';
        }

        // Salva a data/hora atual
        const inputData = document.getElementById(`assinatura_${tipo}_data`);
        if (inputData) {
            const agora = new Date();
            inputData.value = agora.toISOString();
        }

        // Mostra preview da assinatura
        this.mostrarPreview(tipo, dataURL);

        // Fecha o modal
        const modalId = `modal-assinatura-${tipo}`;
        const modal = document.getElementById(modalId);
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) {
            bsModal.hide();
        }

        console.log(`✓ Assinatura ${tipo} salva`);
        
        // Feedback visual
        const btn = document.querySelector(`[onclick*="'${tipo}'"]`);
        if (btn) {
            btn.classList.remove('btn-outline-primary');
            btn.classList.add('btn-success');
            btn.innerHTML = '<i class="fas fa-check me-2"></i>Assinatura Salva';
        }
    }

    /**
     * Carrega uma assinatura existente no canvas
     * @param {string} tipo - 'cliente' ou 'tecnico'
     * @param {string} dataURL - Imagem em base64
     */
    carregarAssinatura(tipo, dataURL) {
        const signaturePad = this.signaturePads[tipo];
        const canvas = this.canvases[tipo];
        
        if (!signaturePad || !canvas) return;

        signaturePad.clear();
        
        const img = new Image();
        img.onload = () => {
            const ctx = canvas.getContext('2d');
            const ratio = Math.max(window.devicePixelRatio || 1, 1);
            ctx.drawImage(img, 0, 0, canvas.width / ratio, canvas.height / ratio);
            
            // Converte o canvas para dados do SignaturePad
            signaturePad.fromDataURL(dataURL);
        };
        img.src = dataURL;
    }

    /**
     * Mostra preview da assinatura salva
     * @param {string} tipo - 'cliente' ou 'tecnico'
     * @param {string} dataURL - Imagem em base64
     */
    mostrarPreview(tipo, dataURL) {
        const previewId = `preview-assinatura-${tipo}`;
        let preview = document.getElementById(previewId);
        
        if (!preview) {
            // Cria elemento de preview se não existir
            const container = document.querySelector(`.assinatura-${tipo}-container`);
            if (container) {
                preview = document.createElement('img');
                preview.id = previewId;
                preview.className = 'img-fluid border rounded mt-2';
                preview.style.maxHeight = '100px';
                preview.style.backgroundColor = '#fff';
                container.appendChild(preview);
            }
        }

        if (preview) {
            preview.src = dataURL;
            preview.style.display = 'block';
        }
    }

    /**
     * Remove a assinatura
     * @param {string} tipo - 'cliente' ou 'tecnico'
     */
    remover(tipo) {
        if (!confirm('Tem certeza que deseja remover esta assinatura?')) {
            return;
        }

        // Limpa os campos
        const inputAssinatura = document.getElementById(`assinatura_${tipo}`);
        if (inputAssinatura) {
            inputAssinatura.value = '';
        }

        const inputNome = document.getElementById(`assinatura_${tipo}_nome`);
        if (inputNome) {
            inputNome.value = '';
        }

        const inputData = document.getElementById(`assinatura_${tipo}_data`);
        if (inputData) {
            inputData.value = '';
        }

        // Remove preview
        const preview = document.getElementById(`preview-assinatura-${tipo}`);
        if (preview) {
            preview.style.display = 'none';
        }

        // Atualiza botão
        const btn = document.querySelector(`[onclick*="'${tipo}'"]`);
        if (btn) {
            btn.classList.remove('btn-success');
            btn.classList.add('btn-outline-primary');
            btn.innerHTML = '<i class="fas fa-signature me-2"></i>Assinar';
        }

        console.log(`✓ Assinatura ${tipo} removida`);
    }
}

// Instância global
const assinaturaManager = new AssinaturaManager();

// Funções globais para uso nos botões
function abrirModalAssinatura(tipo) {
    assinaturaManager.abrirModal(tipo);
}

function limparAssinatura(tipo) {
    assinaturaManager.limpar(tipo);
}

function salvarAssinatura(tipo) {
    assinaturaManager.salvar(tipo);
}

function removerAssinatura(tipo) {
    assinaturaManager.remover(tipo);
}
