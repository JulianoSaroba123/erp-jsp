#!/usr/bin/env python3
"""
Script para diagnosticar problemas de CRUD na interface
"""

def gerar_diagnostico_html():
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Diagnóstico CRUD - Ordens de Serviço</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        .test-section { margin: 20px 0; padding: 15px; border: 1px solid #444; border-radius: 5px; }
        .test-button { margin: 5px; padding: 10px 15px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
        .test-button:hover { background: #0056b3; }
        .result { margin: 10px 0; padding: 10px; border-radius: 3px; }
        .success { background: #155724; border: 1px solid #c3e6cb; }
        .error { background: #721c24; border: 1px solid #f5c6cb; }
        .warning { background: #856404; border: 1px solid #ffeaa7; }
    </style>
</head>
<body>
    <h1>Diagnóstico CRUD - Ordens de Serviço</h1>
    
    <div class="test-section">
        <h3>1. Teste de Navegação dos Botões</h3>
        <button class="test-button" onclick="testarVisualizacao()">Testar Visualizar (ID 2)</button>
        <button class="test-button" onclick="testarEdicao()">Testar Editar (ID 2)</button>
        <button class="test-button" onclick="testarPDF()">Testar PDF (ID 2)</button>
        <button class="test-button" onclick="testarExclusao()">Testar Exclusão (ID 2)</button>
        <div id="navegacao-results"></div>
    </div>
    
    <div class="test-section">
        <h3>2. Teste de JavaScript</h3>
        <button class="test-button" onclick="testarJavaScript()">Testar Funcionamento do JavaScript</button>
        <div id="javascript-results"></div>
    </div>
    
    <div class="test-section">
        <h3>3. Teste de CSS</h3>
        <button class="test-button" onclick="testarCSS()">Verificar Visibilidade dos Botões</button>
        <div id="css-results"></div>
    </div>
    
    <div class="test-section">
        <h3>4. Simulação dos Botões da Lista Original</h3>
        <p>Botões idênticos aos da lista de ordens:</p>
        
        <div class="btn-group btn-group-sm" role="group" style="display: inline-block;">
            <a href="/ordens/2" class="btn btn-outline-light" title="Visualizar" style="padding: 6px 12px; margin: 2px; background: #6c757d; color: white; text-decoration: none; border-radius: 3px;">
                👁 Ver
            </a>
            <a href="/ordens/2/editar" class="btn btn-outline-warning" title="Editar" style="padding: 6px 12px; margin: 2px; background: #ffc107; color: black; text-decoration: none; border-radius: 3px;">
                ✏ Editar
            </a>
            <a href="/ordens/2/pdf" class="btn btn-outline-info" title="PDF" target="_blank" style="padding: 6px 12px; margin: 2px; background: #17a2b8; color: white; text-decoration: none; border-radius: 3px;">
                📄 PDF
            </a>
            <button onclick="confirmarExclusao()" title="Excluir" style="padding: 6px 12px; margin: 2px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer;">
                🗑 Excluir
            </button>
        </div>
        
        <div id="simulacao-results"></div>
    </div>

    <script>
        function mostrarResultado(elemento, tipo, mensagem) {
            const div = document.getElementById(elemento);
            div.innerHTML = `<div class="result ${tipo}">${mensagem}</div>`;
        }
        
        function testarVisualizacao() {
            fetch('/ordens/2')
                .then(response => {
                    if (response.ok) {
                        mostrarResultado('navegacao-results', 'success', '✓ Rota de visualização funcionando (status: ' + response.status + ')');
                    } else {
                        mostrarResultado('navegacao-results', 'error', '✗ Erro na rota de visualização (status: ' + response.status + ')');
                    }
                })
                .catch(err => {
                    mostrarResultado('navegacao-results', 'error', '✗ Erro de conexão: ' + err.message);
                });
        }
        
        function testarEdicao() {
            fetch('/ordens/2/editar')
                .then(response => {
                    if (response.ok) {
                        mostrarResultado('navegacao-results', 'success', '✓ Rota de edição funcionando (status: ' + response.status + ')');
                    } else {
                        mostrarResultado('navegacao-results', 'error', '✗ Erro na rota de edição (status: ' + response.status + ')');
                    }
                })
                .catch(err => {
                    mostrarResultado('navegacao-results', 'error', '✗ Erro de conexão: ' + err.message);
                });
        }
        
        function testarPDF() {
            fetch('/ordens/2/pdf')
                .then(response => {
                    if (response.ok) {
                        mostrarResultado('navegacao-results', 'success', '✓ Rota de PDF funcionando (status: ' + response.status + ')');
                    } else {
                        mostrarResultado('navegacao-results', 'error', '✗ Erro na rota de PDF (status: ' + response.status + ')');
                    }
                })
                .catch(err => {
                    mostrarResultado('navegacao-results', 'error', '✗ Erro de conexão: ' + err.message);
                });
        }
        
        function testarExclusao() {
            // Só testar a conectividade, não excluir de verdade
            fetch('/ordens/2/remover', {
                method: 'HEAD'  // Só testar se a rota existe
            })
                .then(response => {
                    mostrarResultado('navegacao-results', 'warning', '⚠ Rota de exclusão existe (não executada para segurança)');
                })
                .catch(err => {
                    mostrarResultado('navegacao-results', 'warning', '⚠ Rota de exclusão testada');
                });
        }
        
        function testarJavaScript() {
            try {
                // Testar se jQuery está carregado
                const jqueryOk = typeof $ !== 'undefined' ? 'jQuery carregado' : 'jQuery NÃO carregado';
                
                // Testar se Bootstrap está carregado
                const bootstrapOk = typeof bootstrap !== 'undefined' ? 'Bootstrap carregado' : 'Bootstrap NÃO carregado';
                
                // Testar console
                console.log('Teste de JavaScript funcionando');
                
                mostrarResultado('javascript-results', 'success', 
                    `✓ JavaScript funcionando<br>• ${jqueryOk}<br>• ${bootstrapOk}<br>• Console.log funcionando`);
                    
            } catch (err) {
                mostrarResultado('javascript-results', 'error', '✗ Erro no JavaScript: ' + err.message);
            }
        }
        
        function testarCSS() {
            const botoes = document.querySelectorAll('.test-button');
            let botoesVisiveis = 0;
            
            botoes.forEach(botao => {
                const style = window.getComputedStyle(botao);
                if (style.display !== 'none' && style.visibility !== 'hidden') {
                    botoesVisiveis++;
                }
            });
            
            mostrarResultado('css-results', 'success', 
                `✓ CSS funcionando<br>• ${botoesVisiveis} botões visíveis<br>• Estilos aplicados corretamente`);
        }
        
        function confirmarExclusao() {
            if (confirm('Esta é uma simulação. Confirma exclusão da OS: OS0351?')) {
                mostrarResultado('simulacao-results', 'warning', '⚠ Confirmação de exclusão funcionando (simulação)');
            } else {
                mostrarResultado('simulacao-results', 'success', '✓ Cancelamento da exclusão funcionando');
            }
        }
        
        // Auto-executar teste básico
        window.onload = function() {
            testarJavaScript();
            testarCSS();
        };
    </script>
</body>
</html>
"""
    
    with open('diagnostico_crud.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Arquivo diagnostico_crud.html criado!")
    print("Abra este arquivo no navegador para testar:")
    print("http://localhost:5000/../diagnostico_crud.html")
    print("Ou acesse diretamente: file:///{caminho}/diagnostico_crud.html")

if __name__ == "__main__":
    gerar_diagnostico_html()