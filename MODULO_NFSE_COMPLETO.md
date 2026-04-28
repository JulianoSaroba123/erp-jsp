# 📄 Módulo NFS-e (Nota Fiscal de Serviços Eletrônica)
## ERP JSP v3.0

---

## ✅ Implementação Completa

### Arquivos Criados

1. **`app/financeiro/nfse_model.py`** - Modelo de dados
   - 40+ campos para NFS-e completa
   - Cálculos automáticos de ISS e retenções
   - Relacionamentos com Cliente, OrdemServico e LancamentoFinanceiro

2. **`app/financeiro/nfse_routes.py`** - Rotas e lógica
   - CRUD completo (Create, Read, Update, Delete)
   - Geração de PDF
   - Duplicação de notas
   - Cancelamento

3. **Templates HTML:**
   - `listar.html` - Lista todas as NFS-e com filtros
   - `form.html` - Formulário de criação/edição
   - `visualizar.html` - Visualização detalhada

4. **`migrations/criar_tabela_nfse.py`** - Script de migração para criar tabela no banco

5. **Menu atualizado** em `app/templates/base.html`

---

## 🚀 Como Usar

### 1. Acessar o Módulo
- No menu lateral, vá em: **Financeiro > NFS-e (Serviços)**
- Ou acesse diretamente: `http://localhost:5000/financeiro/nfse/`

### 2. Criar Nova NFS-e

#### Passo 1: Dados da Nota
- **Número**: Número sequencial da NFS-e
- **Número RPS**: Número do Recibo Provisório de Serviços (gerado automaticamente)
- **Série RPS**: Série do RPS (padrão: 1)
- **Data de Emissão**: Data de emissão da nota
- **Competência**: Mês/ano de competência (opcional)

#### Passo 2: Prestador
Os dados do prestador são preenchidos **automaticamente** a partir das configurações do sistema.
- Configure em: **Configurações > Dados da Empresa**

#### Passo 3: Tomador dos Serviços
- **Opção 1**: Selecione um cliente cadastrado (preenche automaticamente)
- **Opção 2**: Preencha manualmente os dados do tomador
- Campos: Nome, CPF/CNPJ, Inscrição Municipal, Endereço, Telefone, E-mail
- Pode vincular a uma Ordem de Serviço existente

#### Passo 4: Discriminação dos Serviços
- **Descrição**: Descreva detalhadamente os serviços prestados
- **Código do Serviço**: Código conforme LC 116/2003 (ex: 7.02 para engenharia)
- **Código CNAE**: Código da atividade econômica
- **Local de Prestação**: Onde os serviços foram prestados

#### Passo 5: Valores
- **Valor dos Serviços**: Valor bruto dos serviços (R$)
- **Deduções**: Valores a serem deduzidos (opcional)
- **Alíquota ISS**: Percentual do ISS (padrão: 2%)
- **ISS Retido**: Marque se o ISS foi retido na fonte

#### Passo 6: Retenções Federais
- PIS, COFINS, INSS, IRRF, CSLL (se houver)
- O sistema calcula automaticamente o valor líquido

#### Passo 7: Outras Informações
- **Natureza da Operação**: Tributação no município, fora do município, isenção ou imune
- **Optante Simples**: Marque se a empresa é optante do Simples Nacional
- **Incentivador Cultural**: Marque se participa de programas de incentivo
- **Gerar Lançamento Financeiro**: Cria automaticamente um lançamento a receber

### 3. Visualizar NFS-e
- Lista todas as notas com resumo financeiro
- Filtros por: Cliente, Status, Data, Busca textual
- Cards de resumo: Total Bruto, Total ISS, Total Líquido, Quantidade

### 4. Ações Disponíveis
- **👁️ Visualizar**: Ver todos os detalhes da nota
- **📄 Gerar PDF**: Baixar/imprimir a NFS-e em PDF
- **✏️ Editar**: Modificar observações (apenas notas não canceladas)
- **📋 Duplicar**: Criar nova nota baseada em uma existente
- **🚫 Cancelar**: Cancelar NFS-e (irreversível)

---

## 📊 Modelo de Dados

### Campos Principais

#### Dados da Nota
- `numero` - Número da NFS-e
- `numero_rps` - Número do RPS
- `serie_rps` - Série do RPS
- `data_emissao` - Data de emissão
- `competencia` - Competência (mês/ano de referência)
- `tipo_nfse` - Tipo (PRESTADOR ou TOMADOR)
- `status` - EMITIDA ou CANCELADA

#### Prestador (Quem Presta o Serviço)
- `prestador_nome`
- `prestador_cnpj`
- `prestador_im` - Inscrição Municipal
- `prestador_endereco`
- `prestador_telefone`
- `prestador_email`

#### Tomador (Quem Recebe o Serviço)
- `tomador_nome`
- `tomador_cnpj_cpf`
- `tomador_im`
- `tomador_endereco`
- `tomador_telefone`
- `tomador_email`

#### Serviços
- `descricao_servico` - Descrição detalhada
- `codigo_servico` - Código LC 116/2003
- `codigo_cnae` - CNAE da atividade
- `local_prestacao` - Cidade onde prestou o serviço

#### Valores
- `valor_servicos` - Valor bruto (R$)
- `valor_deducoes` - Deduções (R$)
- `valor_base_calculo` - Base de cálculo (calculado)
- `aliquota_iss` - Alíquota do ISS (%)
- `valor_iss` - Valor do ISS (calculado)
- `iss_retido` - Se ISS foi retido (boolean)

#### Retenções Federais
- `valor_pis`
- `valor_cofins`
- `valor_inss`
- `valor_ir` - IRRF
- `valor_csll`
- `valor_outras_retencoes`

#### Valor Final
- `valor_liquido` - Valor líquido a receber (calculado automaticamente)

#### Outras Informações
- `natureza_operacao` - 1=Mun, 2=Fora Mun, 3=Isenção, 4=Imune
- `optante_simples` - Se é optante do Simples Nacional
- `incentivo_fiscal` - Se tem incentivo cultural/fiscal
- `observacoes` - Observações gerais
- `informacoes_complementares` - Informações adicionais

#### Relacionamentos
- `cliente_id` - Vínculo com cliente (opcional)
- `ordem_servico_id` - Vínculo com OS (opcional)
- `lancamento_id` - Vínculo com lançamento financeiro (criado automaticamente)

---

## 💡 Funções Automáticas

### Cálculo de Valores
O método `calcular_valores()` calcula automaticamente:
1. **Base de Cálculo**: Valor Serviços - Deduções
2. **Valor ISS**: Base × Alíquota ISS
3. **Valor Líquido**: Valor Serviços - ISS - Retenções

### Geração de Lançamento Financeiro
O método `gerar_lancamento_financeiro()` cria automaticamente:
- Tipo: **Receita** / **Conta a Receber**
- Descrição: "NFS-e #[número] - [Tomador]"
- Valor: Valor líquido da nota
- Status: Pendente
- Vincular à NFS-e

---

## 📑 Geração de PDF

O PDF gerado inclui:
- ✅ Cabeçalho com título e número da NFS-e
- ✅ Dados completos do Prestador
- ✅ Dados completos do Tomador  
- ✅ Discriminação dos serviços
- ✅ Tabela de valores com todos os cálculos
- ✅ Valor líquido destacado
- ✅ Data de emissão
- ✅ Código de verificação (se houver)

---

## 🔐 Regras de Negócio

1. **Não é possível editar notas canceladas**
2. **Não é possível cancelar duas vezes**
3. **O cancelamento gera registro no campo de observações**
4. **Ao cancelar, o lançamento financeiro vinculado também é cancelado**
5. **Duplicar cria nova nota com número sequencial automático**
6. **Deduções não podem ser maiores que o valor dos serviços**

---

## 🎨 Interface

### Cores e Ícones
- **Verde** 🟢 - NFS-e, Serviços, PDF
- **Azul** 🔵 - Dados da Nota, Valores
- **Amarelo** 🟡 - Descrição dos Serviços
- **Vermelho** 🔴 - Cancelar, ISS
- **Cinza** ⚪ - Status Cancelada

### Status Visual
- ✅ **Emitida** - Badge verde
- ❌ **Cancelada** - Badge vermelho

---

## 🔧 Endpoints (Rotas)

```
GET  /financeiro/nfse/                    - Listar todas as NFS-e
GET  /financeiro/nfse/nova                - Formulário de nova NFS-e
POST /financeiro/nfse/nova                - Criar NFS-e
GET  /financeiro/nfse/<id>                - Visualizar NFS-e
GET  /financeiro/nfse/<id>/editar         - Formulário de edição
POST /financeiro/nfse/<id>/editar         - Atualizar NFS-e
POST /financeiro/nfse/<id>/cancelar       - Cancelar NFS-e
GET  /financeiro/nfse/<id>/pdf            - Gerar PDF
POST /financeiro/nfse/<id>/duplicar       - Duplicar NFS-e
```

---

## 📦 Integração com Outros Módulos

### Com Clientes
- Ao selecionar cliente, preenche automaticamente dados do tomador
- Link direto para o cadastro do cliente na visualização

### Com Ordens de Serviço
- Pode vincular NFS-e a uma OS específica
- Link direto para a OS na visualização

### Com Financeiro
- Gera lançamento financeiro automaticamente (opcional)
- Sincroniza cancelamento entre NFS-e e lançamento
- Integração com contas a receber

### Com Configurações
- Busca automaticamente dados da empresa para preencher Prestador
- Usar CNPJ, Inscrição Municipal, Endereço configurados

---

## 📋 Filtros Disponíveis

Na listagem de NFS-e, você pode filtrar por:
- **Cliente**: Selecione um cliente específico
- **Status**: Emitida ou Cancelada
- **Data Início**: A partir de qual data
- **Data Fim**: Até qual data
- **Busca livre**: Busca em número, nome do cliente ou descrição do serviço

---

## 💾 Banco de Dados

### Tabela: `notas_fiscais_servico`
- **45+ colunas** com todos os dados de NFS-e
- **Foreign Keys** para: clientes, ordem_servico, lancamentos_financeiros
- **Índices** em: numero, data_emissao, cliente_id, status
- **Soft delete** com campo `ativo`

---

## 🛠️ Manutenção

### Recriar Tabela
```bash
python migrations/criar_tabela_nfse.py
```
⚠️ **Atenção**: Isso apaga todos os dados existentes!

### Backup
Faça backup regular da tabela `notas_fiscais_servico` antes de atualizações.

---

## ✨ Próximas Melhorias (Sugestões)

- [ ] Exportação para XML conforme padrão ABRASF
- [ ] Envio automático para prefeituras via API
- [ ] Consulta de código de verificação
- [ ] Relatório consolidado de NFS-e
- [ ] Envio por e-mail para o tomador
- [ ] Assinatura digital
- [ ] Numeração automática sequencial
- [ ] Integração com sistema de contabilidade

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do sistema
2. Consulte a documentação do módulo Financeiro
3. Entre em contato com o suporte JSP

---

**Desenvolvido por JSP Soluções - 2026**
**Versão: 3.0**
