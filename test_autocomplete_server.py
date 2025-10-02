from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/test-autocomplete')
def test_autocomplete():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Teste Autocomplete</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; }
        .input-group { position: relative; width: 100%; }
        .form-control { 
            width: 100%; 
            padding: 10px; 
            font-size: 16px; 
            border: 1px solid #ccc; 
            border-radius: 4px; 
        }
        .dropdown-menu {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            border: 1px solid #ccc;
            background: white;
            z-index: 1000;
            border-radius: 0 0 4px 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .dropdown-item {
            display: block;
            padding: 8px 12px;
            text-decoration: none;
            color: #333;
            cursor: pointer;
        }
        .dropdown-item:hover {
            background: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Teste de Autocomplete de Clientes</h1>
        <p>Digite 2 ou mais letras para buscar clientes:</p>
        
        <div class="input-group">
            <input id="cliente_input" class="form-control" placeholder="Digite para buscar..." autocomplete="off">
            <div id="cliente_dropdown" class="dropdown-menu" style="display: none;"></div>
        </div>
        
        <div id="resultado" style="margin-top: 20px; padding: 10px; background: #f8f9fa; border-radius: 4px;"></div>
    </div>
    
    <script>
        console.log('🚀 Script iniciado');
        
        const input = document.getElementById('cliente_input');
        const dropdown = document.getElementById('cliente_dropdown');
        const resultado = document.getElementById('resultado');
        
        console.log('Elementos encontrados:', {input, dropdown, resultado});
        
        if (!input || !dropdown) {
            resultado.innerHTML = '❌ Elementos não encontrados!';
        } else {
            resultado.innerHTML = '✅ Elementos encontrados. Digite para testar...';
        }
        
        let timeout = null;
        
        input.addEventListener('input', function() {
            const query = this.value.trim();
            console.log('📝 Digitando:', query);
            
            resultado.innerHTML = '⌨️ Você digitou: ' + query;
            
            if (timeout) {
                clearTimeout(timeout);
            }
            
            if (query.length < 2) {
                dropdown.style.display = 'none';
                return;
            }
            
            resultado.innerHTML = '🔍 Buscando...';
            
            timeout = setTimeout(function() {
                console.log('🌐 Fazendo requisição para:', '/clientes/api/busca?q=' + query);
                
                fetch('/clientes/api/busca?q=' + encodeURIComponent(query))
                    .then(response => {
                        console.log('📡 Resposta recebida:', response.status);
                        return response.json();
                    })
                    .then(clientes => {
                        console.log('👥 Clientes encontrados:', clientes);
                        
                        resultado.innerHTML = '📊 Encontrados: ' + (clientes.length || 0) + ' clientes';
                        
                        dropdown.innerHTML = '';
                        
                        if (!clientes || clientes.length === 0) {
                            dropdown.style.display = 'none';
                            return;
                        }
                        
                        clientes.forEach(cliente => {
                            const item = document.createElement('a');
                            item.className = 'dropdown-item';
                            item.textContent = cliente.nome + ' (' + (cliente.cpf_cnpj || 'Sem CPF/CNPJ') + ')';
                            
                            item.addEventListener('click', function(e) {
                                e.preventDefault();
                                console.log('✅ Cliente selecionado:', cliente);
                                
                                input.value = item.textContent;
                                dropdown.style.display = 'none';
                                resultado.innerHTML = '🎯 Cliente selecionado: ' + cliente.nome;
                            });
                            
                            dropdown.appendChild(item);
                        });
                        
                        dropdown.style.display = 'block';
                    })
                    .catch(error => {
                        console.error('❌ Erro:', error);
                        resultado.innerHTML = '❌ Erro ao buscar: ' + error.message;
                        dropdown.style.display = 'none';
                    });
            }, 300);
        });
        
        // Fechar dropdown ao clicar fora
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
        
        console.log('✅ Script configurado');
    </script>
</body>
</html>
    ''')

if __name__ == '__main__':
    app.run(debug=True, port=5001)