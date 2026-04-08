# 🔧 Como Corrigir a Logo no Render

## Problema
A logo não aparece no PDF da Ordem de Serviço no Render.

## Causa
A função `get_logo_base64()` estava retornando formatos inconsistentes (às vezes com prefixo `data:image`, às vezes sem).

## Solução Aplicada

### 1. Código Corrigido
A função `get_logo_base64()` em `app/ordem_servico/ordem_servico_routes.py` foi corrigida para:
- Sempre retornar base64 puro (sem prefixo `data:image`)
- Remover prefixo se houver no banco
- Adicionar logs detalhados para debug

### 2. Como Aplicar no Render

#### Opção 1: Via Git Push (RECOMENDADO)
```bash
# Commite as alterações
git add app/ordem_servico/ordem_servico_routes.py
git commit -m "fix: corrige carregamento da logo no PDF"
git push origin main
```

O Render fará deploy automático e aplicará as correções.

#### Opção 2: Via Render Shell (Se urgente)
1. Acesse o Render Dashboard
2. Vá em "Shell" no seu serviço
3. Execute:
```bash
python fix_logo_render.py
```

Este script vai:
- Verificar se a logo está no banco
- Remover prefixo `data:image` se houver
- Validar o base64
- Tentar carregar JSP.jpg se necessário

### 3. Verificação

Após aplicar, teste gerando um PDF:
1. Acesse uma Ordem de Serviço
2. Clique em "Gerar PDF"
3. Verifique se a logo aparece no cabeçalho

## Logs para Debug

Os logs agora mostram:
```
🔍 DEBUG LOGO: Iniciando busca da logo...
✅ DEBUG LOGO: Logo encontrada no banco (base64) - XXXXX chars
```

Se aparecer:
- `❌ DEBUG LOGO: Arquivo não encontrado` → Logo não está no banco
- `⚠️ DEBUG LOGO: Nenhuma logo encontrada` → Precisa configurar a logo

## Como Configurar a Logo pela Primeira Vez

Se não houver logo configurada:

1. Acesse Configurações do Sistema
2. Faça upload da logo (PNG ou JPG)
3. O sistema converterá e salvará em base64 automaticamente

## Checklist

- [ ] Código atualizado no Git
- [ ] Deploy no Render concluído
- [ ] Script `fix_logo_render.py` executado (se necessário)
- [ ] PDF testado e logo aparecendo

## Arquivos Alterados

- `app/ordem_servico/ordem_servico_routes.py` - Função `get_logo_base64()`
- `fix_logo_render.py` - Script de correção (novo)
- `verificar_e_corrigir_logo_render.py` - Script de diagnóstico (novo)
