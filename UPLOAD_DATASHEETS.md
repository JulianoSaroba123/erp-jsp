# 📄 Sistema de Upload de Datasheets

## 🎯 Funcionalidade Implementada

Sistema completo para upload e gerenciamento de **datasheets** (PDFs e imagens) para placas e inversores solares.

## ✨ Recursos

### 1. Upload de Arquivos
- **Formatos aceitos**: PDF, JPG, JPEG, PNG, WEBP
- **Tamanho máximo**: 5 MB
- **Validação automática** de tipo e tamanho
- **Preview em tempo real** para imagens
- **Timestamp automático** para evitar conflitos de nome

### 2. Link Externo
- Opção de usar **URL externa** ao invés de upload
- Útil para datasheets hospedados em sites dos fabricantes
- Economiza espaço em disco

### 3. Visualização
- **Cards de produtos** mostram botão para ver datasheet
- Diferenciação visual: PDF (vermelho) vs Imagem (azul)
- Abre em nova aba para visualização completa

### 4. Edição
- Possibilidade de **substituir arquivo** existente
- **Exclusão automática** do arquivo antigo ao fazer upload de novo
- Manter arquivo atual ou adicionar link externo

## 📁 Estrutura de Arquivos

```
app/
├── static/
│   └── uploads/
│       └── datasheets/          # Pasta de upload
│           ├── .gitkeep         # Mantém pasta no Git
│           └── 20260105_143025_datasheet.pdf  # Formato: timestamp_nomeoriginal.ext
└── energia_solar/
    ├── energia_solar_routes.py  # Rotas com lógica de upload
    └── templates/
        └── energia_solar/
            ├── _form_placa.html      # Formulário com abas Upload/Link
            ├── _form_inversor.html   # Idem para inversores
            └── placas_crud.html      # Cards com botão de datasheet
```

## 🔧 Configuração Técnica

### Rotas Modificadas

**Placas:**
- `POST /energia-solar/placas/criar` - Aceita upload de arquivo
- `POST /energia-solar/placas/editar/<id>` - Atualiza arquivo ou link

**Inversores:**
- `POST /energia-solar/inversores/criar` - Aceita upload de arquivo
- `POST /energia-solar/inversores/editar/<id>` - Atualiza arquivo ou link

### Parâmetros de Upload

```python
UPLOAD_FOLDER = 'app/static/uploads/datasheets'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
```

### Função de Validação

```python
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

## 📝 Uso no Formulário

### Campos do Formulário

**Upload de Arquivo:**
```html
<input type="file" name="datasheet_file" accept=".pdf,.jpg,.jpeg,.png,.webp">
```

**Link Externo:**
```html
<input type="url" name="datasheet_url" placeholder="https://...">
```

### Lógica de Prioridade

1. Se houver **arquivo enviado** → salva arquivo e usa caminho local
2. Se não houver arquivo, mas houver **URL** → salva URL
3. Se nenhum dos dois → `datasheet = None`

### Exclusão Automática

Ao fazer upload de novo arquivo na edição:
```python
if placa.datasheet and placa.datasheet.startswith('/static/uploads/'):
    old_file = os.path.join(app_root, placa.datasheet.lstrip('/'))
    if os.path.exists(old_file):
        os.remove(old_file)  # Remove arquivo antigo
```

## 🎨 Interface do Usuário

### Abas no Formulário
```
┌─────────────────────────────────┐
│ [Upload Arquivo] [Link Externo] │
├─────────────────────────────────┤
│ Aba Upload:                     │
│ [Escolher arquivo...]           │
│ Formatos: PDF, JPG, PNG (5MB)   │
│                                 │
│ [Preview da imagem]             │
└─────────────────────────────────┘
```

### Preview de Imagem
- Exibido automaticamente ao selecionar arquivo
- Thumbnail com max-height: 200px
- Mostra nome e tamanho do arquivo

### Botões nos Cards
```html
<!-- PDF -->
<a href="/static/uploads/datasheets/arquivo.pdf" target="_blank">
    <i class="fas fa-file-pdf"></i> Ver Datasheet PDF
</a>

<!-- Imagem -->
<a href="/static/uploads/datasheets/foto.jpg" target="_blank">
    <i class="fas fa-image"></i> Ver Imagem Técnica
</a>
```

## 🧪 Como Testar

### Teste Local

1. Execute o script de verificação:
```bash
python testar_upload_datasheet.py
```

2. Inicie o servidor:
```bash
python run.py
```

3. Acesse: `http://localhost:5000/energia-solar/placas`

4. **Cadastrar nova placa:**
   - Clique em "Nova Placa"
   - Preencha os dados obrigatórios
   - Na seção Datasheet:
     - Aba "Upload Arquivo": escolha um PDF ou imagem
     - OU Aba "Link Externo": cole um link
   - Salve

5. **Verificar resultado:**
   - Card da placa deve mostrar botão "Ver Datasheet"
   - Clicar abre em nova aba

6. **Testar edição:**
   - Clique em "Editar" no card
   - Altere o datasheet (novo arquivo ou link)
   - Salve e verifique atualização

### Teste no Render

**IMPORTANTE**: No Render, o sistema de arquivos é **efêmero**. Arquivos enviados são perdidos a cada deploy.

**Soluções para produção:**
1. Usar **AWS S3** / **Cloudinary** para armazenamento persistente
2. Preferir **links externos** para datasheets
3. Configurar **volume persistente** (se disponível no plano)

Para implementar S3:
```python
import boto3

s3 = boto3.client('s3', 
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
)

s3.upload_fileobj(file, 'bucket-name', filename)
datasheet = f"https://bucket-name.s3.amazonaws.com/{filename}"
```

## 🔒 Segurança

### Validações Implementadas

✅ Extensão de arquivo validada
✅ Tamanho máximo verificado (5MB)
✅ Filename sanitizado com `secure_filename()`
✅ Timestamp adicionado para evitar sobrescrita
✅ Pasta de upload criada automaticamente
✅ Permissões de escrita verificadas

### Validações Faltantes (TODO)

⚠️ Verificar conteúdo real do arquivo (mime-type)
⚠️ Scan de malware em produção
⚠️ Rate limiting para uploads
⚠️ Autenticação/autorização por usuário

## 📊 Banco de Dados

Campo existente no modelo:
```python
datasheet = db.Column(db.String(500))  # Caminho ou URL
```

**Valores possíveis:**
- `/static/uploads/datasheets/20260105_143025_ficha.pdf` (upload local)
- `https://example.com/datasheet.pdf` (link externo)
- `NULL` (sem datasheet)

## 🚀 Melhorias Futuras

1. **Armazenamento em Nuvem**
   - Integrar AWS S3 / Cloudinary
   - Manter upload persistente no Render

2. **Multi-arquivos**
   - Permitir múltiplos datasheets por produto
   - Galeria de imagens do produto

3. **Thumbnails Automáticos**
   - Gerar preview de PDFs
   - Otimizar imagens automaticamente

4. **Organização**
   - Subpastas por fabricante
   - Tags e categorias

5. **Compartilhamento**
   - Links públicos para datasheets
   - QR Code para acesso rápido

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs do servidor
2. Testar permissões da pasta uploads
3. Validar tamanho e formato do arquivo
4. Conferir configuração de `enctype="multipart/form-data"`

## ✅ Checklist de Implementação

- [x] Adicionar imports (werkzeug, os, send_from_directory)
- [x] Criar pasta de uploads com .gitkeep
- [x] Implementar função `allowed_file()`
- [x] Modificar rotas de criar/editar placas
- [x] Modificar rotas de criar/editar inversores
- [x] Atualizar formulários com abas Upload/Link
- [x] Adicionar `enctype="multipart/form-data"` nos forms
- [x] Implementar preview de imagem em JavaScript
- [x] Adicionar botões de datasheet nos cards
- [x] Testar upload local
- [ ] Testar no Render (pendente deploy)
- [ ] Implementar S3 para produção (opcional)
