# 📝 Guia de Gerenciamento de Logo - ERP JSP

Este guia explica como gerenciar a logo do sistema usando os scripts disponíveis.

## 🎯 Problema Resolvido

**Antes:** A logo não aparecia ou voltava para a antiga após reiniciar o sistema.

**Agora:** Sistema salva logo em dois formatos para máxima compatibilidade:
- `logo` - caminho do arquivo físico
- `logo_base64` - imagem em base64 (usado em PDFs e cloud)

## 🛠️ Scripts Disponíveis

### 1. `inicializar_logo_padrao.py`
**Quando usar:** Primeira configuração ou resetar para logo JSP padrão

```powershell
python inicializar_logo_padrao.py
```

**O que faz:**
- ✅ Adiciona logo JSP padrão no banco de dados
- ✅ Inicializa nome fantasia como "JSP Elétrica Industrial & Solar"
- ✅ Pergunta antes de sobrescrever logo existente
- ✅ Pronto para usar imediatamente

### 2. `converter_logo_existente.py`
**Quando usar:** Tem uma logo em arquivo mas não aparece no sistema

```powershell
python converter_logo_existente.py
```

**O que faz:**
- ✅ Procura arquivo de logo em múltiplos caminhos
- ✅ Converte para base64 automaticamente
- ✅ Redimensiona se muito grande (máx 800px)
- ✅ Salva ambos os campos no banco
- ✅ Mostra tamanho e formato

### 3. `testar_upload_logo.py`
**Quando usar:** Verificar estado atual da logo

```powershell
python testar_upload_logo.py
```

**O que faz:**
- ✅ Mostra campos `logo` e `logo_base64`
- ✅ Verifica se arquivo físico existe
- ✅ Exibe tamanho dos dados
- ✅ Útil para debug

## 📋 Fluxo de Uso

### Configuração Inicial (Sistema Novo)

1. **Inicialize a logo padrão:**
   ```powershell
   python inicializar_logo_padrao.py
   ```

2. **Acesse as configurações:**
   - Vá para: http://localhost:5000/configuracao/
   - Agora você já vê a logo JSP padrão

3. **Faça upload de sua logo (opcional):**
   - Clique em "Escolher arquivo"
   - Selecione uma imagem (PNG, JPG, JPEG, GIF)
   - Clique em "Salvar Configurações"
   - ✅ Sistema converte automaticamente para base64

### Migração de Sistema Antigo

Se você tem uma logo antiga que não aparece:

1. **Execute o conversor:**
   ```powershell
   python converter_logo_existente.py
   ```

2. **Verifique o resultado:**
   ```powershell
   python testar_upload_logo.py
   ```

3. **Acesse as configurações:**
   - http://localhost:5000/configuracao/
   - Logo agora aparece corretamente

## ✅ Status da Logo no Template

O template mostra diferentes status:

### ✅ Logo Configurada (Base64)
```
[Imagem da logo]
✓ Logo configurada
```

### ℹ️ Logo em Arquivo
```
[Imagem da logo]
ℹ Arquivo: nome_da_logo.png
```

### ⚠️ Arquivo Não Encontrado
```
[X]
⚠ Arquivo não encontrado - faça novo upload
```

### 📷 Nenhuma Logo
```
[Ícone de imagem]
Nenhuma logo configurada
Faça upload de uma imagem
```

## 🔧 Troubleshooting

### Logo não aparece após upload

**Solução:**
```powershell
# Verifique o estado
python testar_upload_logo.py

# Se logo_base64 estiver vazio, converta:
python converter_logo_existente.py
```

### Logo volta para a antiga

**Causa:** O campo `logo_base64` não foi atualizado.

**Solução:** Faça um novo upload pela interface web. O sistema agora converte automaticamente.

### Arquivo muito grande

O sistema redimensiona automaticamente para máx 800px. Mas você pode otimizar antes:

**Tamanhos recomendados:**
- Largura/Altura: 200-800px
- Tamanho arquivo: < 500KB
- Formato: PNG (com transparência) ou JPG

### Logo no Render (Cloud)

O Render usa o campo `logo_base64`. Certifique-se de que está preenchido:

```powershell
python testar_upload_logo.py
```

Se estiver vazio, faça upload novamente pela interface.

## 📝 Notas Técnicas

### Formatos Aceitos
- PNG (recomendado - suporta transparência)
- JPEG / JPG
- GIF

### Armazenamento
- **Local**: arquivo em `uploads/configuracao/`
- **Banco**: base64 em `configuracao.logo_base64`
- **PDFs**: usa base64
- **Cloud (Render)**: usa base64

### Conversão Automática
Quando você faz upload:
1. ✅ Arquivo salvo em `uploads/configuracao/`
2. ✅ Campo `logo` atualizado com caminho
3. ✅ **Imagem convertida para base64**
4. ✅ **Campo `logo_base64` atualizado**
5. ✅ Redimensionamento se > 800px
6. ✅ Commit no banco de dados

## 🚀 Próximos Passos

Após configurar a logo:

1. ✅ Complete dados da empresa (CNPJ, endereço, etc.)
2. ✅ Configure dados bancários
3. ✅ Adicione textos institucionais (missão, visão, valores)
4. ✅ Escolha tema e cor principal
5. ✅ Teste geração de PDFs para ver a logo

---

**Desenvolvido para ERP JSP v3.0**  
*Sistema de gerenciamento empresarial*
