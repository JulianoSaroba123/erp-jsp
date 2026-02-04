# 🔧 Módulo de Serviços - Documentação Completa

## ✅ O que foi implementado:

### 1. **Model Servico** (`app/servico/servico_model.py`)
- ✅ Cadastro completo de serviços
- ✅ Código automático (SRV001, SRV002, etc.)
- ✅ Categorias: Instalação, Manutenção, Reparo, Consultoria, Projeto, Vistoria, Treinamento, Outros
- ✅ Tipos de cobrança: Por Hora, Por Dia, Serviço Fechado, Por Km, Por Item
- ✅ Campos de valor: valor_base, valor_minimo
- ✅ Tempo estimado (min, max, médio)
- ✅ Prazo de garantia
- ✅ Materiais necessários
- ✅ Instruções de execução
- ✅ Configurações: disponível_app, requer_agendamento, destaque
- ✅ Properties formatadas: valor_base_formatado, tempo_estimado_formatado, etc.
- ✅ Métodos de busca e estatísticas

### 2. **Routes CRUD** (`app/servico/servico_routes.py`)
- ✅ `/servico/listar` - Lista todos os serviços com filtros
- ✅ `/servico/novo` - Criar novo serviço
- ✅ `/servico/<id>/editar` - Editar serviço
- ✅ `/servico/<id>` - Visualizar serviço
- ✅ `/servico/<id>/excluir` - Excluir (desativar) serviço
- ✅ `/servico/dashboard` - Dashboard com estatísticas

### 3. **APIs REST** (para integração com OS)
- ✅ `/servico/api/buscar?q=termo` - Busca serviços por nome/código
- ✅ `/servico/api/<id>` - Detalhes de um serviço específico
- ✅ `/servico/api/categorias` - Lista todas as categorias

### 4. **Templates**
- ✅ `listar.html` - Lista com filtros e estatísticas
- ✅ `form.html` - Formulário criar/editar
- ⏳ `visualizar.html` - Precisa criar
- ⏳ `confirmar_exclusao.html` - Precisa criar
- ⏳ `dashboard.html` - Atualizar com estatísticas

### 5. **Dados de Teste**
- ✅ Script `criar_servicos_exemplo.py` cria 6 serviços prontos
- ✅ SRV001: Instalação Elétrica Residencial (R$ 1.500)
- ✅ SRV002: Manutenção Preventiva (R$ 150/hora)
- ✅ SRV003: Reparo de Tomadas (R$ 50/item)
- ✅ SRV004: Consultoria Técnica (R$ 200/hora)
- ✅ SRV005: Projeto Elétrico (R$ 2.500)
- ✅ SRV006: Vistoria Elétrica (R$ 800)

---

## 🔗 Próximos Passos - Integração com Ordem de Serviço

### FASE 1: Preparar Ordem de Serviço para receber serviços

1. **Atualizar `ordem_servico_model.py`**:
   - Adicionar relacionamento com `Servico`
   - Ajustar `OrdemServicoItem` para referenciar `Servico`

2. **Atualizar formulário de OS**:
   - Adicionar campo de seleção de serviços
   - Usar API `/servico/api/buscar` para autocomplete
   - Ao selecionar serviço, preencher automaticamente:
     - Descrição
     - Tipo de cobrança
     - Valor unitário
     - Tempo estimado
     - Prazo de garantia

### FASE 2: Implementar seleção de serviços na OS

```javascript
// Exemplo de integração via JavaScript
$('#buscar_servico').autocomplete({
    source: '/servico/api/buscar',
    select: function(event, ui) {
        adicionarServicoNaOS(ui.item);
    }
});

function adicionarServicoNaOS(servico) {
    // Adiciona linha na tabela de itens da OS
    // Preenche com dados do serviço selecionado
}
```

### FASE 3: Backend - Salvar serviços na OS

```python
# Em ordem_servico_routes.py
@ordem_servico_bp.route('/novo', methods=['POST'])
def criar_os():
    # 1. Criar a OS
    os = OrdemServico(...)
    
    # 2. Para cada serviço selecionado:
    servico_id = request.form.get('servico_id')
    servico = Servico.query.get(servico_id)
    
    # 3. Criar item da OS baseado no serviço
    item = OrdemServicoItem(
        servico_id=servico.id,
        descricao=servico.nome,
        tipo_servico=servico.tipo_cobranca,
        valor_unitario=servico.valor_base,
        quantidade=1
    )
    os.servicos.append(item)
```

---

## 📱 Como usar o módulo:

### 1. **Acessar no navegador**:
```
http://localhost:5000/servico/listar
```

### 2. **Criar novo serviço**:
- Clicar em "Novo Serviço"
- Preencher formulário
- Código é gerado automaticamente (ou pode digitar manualmente)
- Escolher categoria e tipo de cobrança
- Definir valor base
- Salvar

### 3. **Usar serviço em Ordem de Serviço**:
- Na tela de criar/editar OS
- Campo "Adicionar Serviço"
- Buscar por código ou nome
- Selecionar da lista
- Dados preenchidos automaticamente
- Ajustar quantidade se necessário

---

## 🎯 Benefícios:

1. **Padronização**: Todos usam os mesmos serviços cadastrados
2. **Agilidade**: Não precisa digitar descrição e valores toda vez
3. **Consistência**: Preços e prazos sempre corretos
4. **Relatórios**: Pode ver quais serviços são mais vendidos
5. **Estimativas**: Tempo estimado ajuda no planejamento
6. **Garantia**: Prazo de garantia já definido

---

## 🚀 Para testar agora:

```bash
# 1. Criar serviços de exemplo
python criar_servicos_exemplo.py

# 2. Iniciar servidor
python run.py

# 3. Acessar
http://localhost:5000/servico/listar
```

---

## 📝 TO-DO:

- [ ] Criar template `visualizar.html`
- [ ] Criar template `confirmar_exclusao.html`
- [ ] Atualizar template `dashboard.html`
- [ ] Adicionar campo `servico_id` em `OrdemServicoItem`
- [ ] Implementar seleção de serviços no formulário de OS
- [ ] Criar JavaScript para autocomplete de serviços
- [ ] Adicionar relatório de serviços mais usados
- [ ] Implementar histórico de alterações de preços

---

**Tudo pronto para a próxima etapa: integrar com Ordem de Serviço!** 🎉
