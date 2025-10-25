# Gerenciamento de Cache - Sistema ERP JSP

## Problema Identificado
O Flask estava mantendo templates em cache na memória, impedindo que mudanças nos arquivos de template aparecessem nos PDFs gerados sem reiniciar o servidor manualmente.

## Solução Implementada

### 1. Configuração Flask (app/config.py)
```python
class DevelopmentConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    JINJA2_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
```

### 2. Configuração Jinja2 (app/app.py)
```python
if app.config['DEBUG']:
    app.jinja_env.auto_reload = True
```

### 3. Headers HTTP Anti-Cache (proposta_routes.py)
```python
response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
response.headers['Pragma'] = 'no-cache'
response.headers['Expires'] = '0'
```

### 4. Meta Tags no Template (pdf_proposta.html)
```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

### 5. Scripts de Restart Automático

#### Windows Batch (restart_server.bat)
```batch
@echo off
echo Parando servidor Flask...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
echo Limpando cache...
rmdir /s /q __pycache__ 2>nul
echo Reiniciando servidor...
start cmd /k "python run.py"
```

#### PowerShell (restart_server.ps1)
```powershell
Write-Host "🛑 Parando servidor Flask..." -ForegroundColor Red
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "🗑️ Limpando cache..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Directory -Name __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "🚀 Reiniciando servidor..." -ForegroundColor Green
Start-Process -FilePath "python" -ArgumentList "run.py"
```

## Como Usar

### Durante o Desenvolvimento
1. **Modo Automático**: As configurações garantem que mudanças em templates sejam refletidas automaticamente
2. **Modo Manual**: Use os scripts de restart se necessário:
   - `.\restart_server.bat` (Windows Batch)
   - `.\restart_server.ps1` (PowerShell)

### Testes Realizados
✅ Modificação no título do template
✅ Geração imediata de PDF com mudanças
✅ Sem necessidade de restart manual do servidor

## Benefícios
- **Desenvolvimento Ágil**: Mudanças aparecem imediatamente
- **Menos Frustração**: Elimina necessidade de restart manual
- **Produtividade**: Workflow mais fluido para ajustes de layout
- **Confiabilidade**: Múltiplas camadas de prevenção de cache

## Notas Técnicas
- As configurações são específicas para desenvolvimento (`DEBUG=True`)
- Em produção, o cache pode ser reabilitado para performance
- Os headers HTTP garantem que browsers não cacheem as respostas
- O auto-reload do Jinja2 monitora mudanças nos arquivos de template