# 🎯 Busca Automática CEP e CNPJ - Guia de Uso

## 📋 Funcionalidades Implementadas

### 🏠 **Busca por CEP**
- **API**: `/fornecedores/api/buscar_cep/{cep}`
- **Funcionalidade**: Preenchimento automático de endereço e cidade
- **Serviço**: ViaCEP (API pública gratuita)

**Como usar:**
1. Digite um CEP no campo correspondente (formato: 00000-000)
2. Ao sair do campo (blur), o endereço será preenchido automaticamente
3. Validação em tempo real de CEP

### 🏢 **Busca por CNPJ** 
- **API**: `/fornecedores/api/buscar_cnpj/{cnpj}`
- **Funcionalidade**: Preenchimento automático de dados da empresa
- **Serviço**: ReceitaWS (API pública gratuita)

**Como usar:**
1. Digite um CNPJ no campo correspondente (formato: 00.000.000/0000-00)
2. Ao sair do campo (blur), os dados da empresa serão preenchidos
3. Validação em tempo real de CNPJ com dígito verificador

## 🧪 **Testes de CEP**
```
CEPs para testar:
- 01310-100 (Av. Paulista, SP) ✅
- 20040-020 (Centro, Rio de Janeiro) ✅
- 30112-000 (Centro, Belo Horizonte) ✅
```

## 🧪 **Testes de CNPJ**
```
CNPJs válidos para testar:
- 11.222.333/0001-81 ✅
- 34.028.316/0001-50 ✅ 
```

## ⚡ **Recursos Implementados**

### 🎨 **Interface**
- ✅ Máscaras automáticas (CEP, CNPJ, telefone)
- ✅ Validação em tempo real
- ✅ Feedback visual de erro
- ✅ Loading states ("Buscando...")

### 🔧 **Backend** 
- ✅ APIs RESTful para CEP e CNPJ
- ✅ Tratamento de erros completo
- ✅ Timeout e error handling
- ✅ Validação de formato

### 📱 **Frontend**
- ✅ JavaScript automático com jQuery
- ✅ AJAX calls para APIs
- ✅ Preenchimento inteligente (só preenche campos vazios)
- ✅ Validação de CNPJ com dígito verificador

## 🚀 **Como Acessar**
1. Execute o servidor: `python executar.py`
2. Acesse: `http://127.0.0.1:5000/fornecedores/cadastrar`
3. Teste preenchendo CEP ou CNPJ nos campos

## 📊 **Status dos Testes**
- ✅ API de CEP funcional
- ✅ API de CNPJ funcional  
- ✅ JavaScript integrado
- ✅ Validações implementadas
- ✅ Interface responsiva

---
**Desenvolvido com Flask + jQuery + ViaCEP + ReceitaWS** 🎉