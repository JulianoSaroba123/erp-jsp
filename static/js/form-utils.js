// Utilities shared across client/fornecedor forms
(function(window, $){
  'use strict';

  function aplicarMascaras() {
    if ($('#telefone').length) $('#telefone').mask('(00) 00000-0000');
    if ($('#cep').length) $('#cep').mask('00000-000');
  }

  function atualizarMascaraCpfCnpj() {
    const $cpf = $('#cpf_cnpj');
    if (!$cpf.length) return;
    const tipoPessoa = $('input[name="tipo_pessoa"]:checked').val();
    const currentValue = $cpf.val().replace(/\D/g, '');
    if (tipoPessoa === 'PF') {
      $cpf.unmask();
      if (currentValue) $cpf.mask('000.000.000-00');
      $('#label_cpf_cnpj').text('CPF *');
      $('#label_nome').text('Nome *');
      $('#hint_cpf_cnpj').text('Digite apenas números do CPF');
      $('#inscricao_estadual_group, #inscricao_municipal_group').hide();
    } else {
      $cpf.unmask();
      if (currentValue) $cpf.mask('00.000.000/0000-00');
      $('#label_cpf_cnpj').text('CNPJ *');
      $('#label_nome').text('Razão Social *');
      $('#hint_cpf_cnpj').text('Digite apenas números do CNPJ');
      $('#inscricao_estadual_group, #inscricao_municipal_group').show();
    }
  }

  function buscarCep(cep){
    if (!cep || cep.length !== 8) return;
    $('#cep').addClass('loading'); $('#hint_cep').remove();
    return fetch(`https://viacep.com.br/ws/${cep}/json/`).then(function(res){ if (!res.ok) throw new Error('Erro na rede'); return res.json(); })
      .then(function(d){
        if (d.erro){ $('#cep').after('<small id="hint_cep" class="text-muted">CEP não encontrado</small>'); return null; }
        $('#logradouro').val(d.logradouro || '');
        $('#bairro').val(d.bairro || '');
        $('#cidade').val(d.localidade || '');
        $('#uf').val(d.uf || '');
        $('#numero').focus();
        return d;
      }).catch(function(err){ console.warn('Erro ViaCEP', err); $('#cep').after('<small id="hint_cep" class="text-muted">Erro ao buscar CEP</small>'); return null; })
      .finally(function(){ $('#cep').removeClass('loading'); });
  }

  function initFormUtils(){
    aplicarMascaras();

    // Atualiza máscara ao mudar tipo de pessoa
    $(document).on('change', 'input[name="tipo_pessoa"]', function(){
      const $cpf = $('#cpf_cnpj');
      if ($cpf.length && $cpf.val()){
        const digits = $cpf.val().replace(/\D/g,'');
        $cpf.val(digits);
      }
      atualizarMascaraCpfCnpj();
    });

    // Buscar CEP
    $(document).on('blur', '#cep', function(){ const cep = $(this).val().replace(/\D/g,''); buscarCep(cep); });
    $(document).on('click', '#btn_buscar_cep', function(){ const cep = $('#cep').val().replace(/\D/g,''); buscarCep(cep); });

    // Ao perder foco no CPF/CNPJ, disparar lookup para CNPJ se PJ
    $(document).on('blur', '#cpf_cnpj', function(){ const digits = $(this).val().replace(/\D/g,''); const tipoPessoa = $('input[name="tipo_pessoa"]:checked').val(); if (tipoPessoa === 'PJ' && digits.length === 14) { $(this).unmask().mask('00.000.000/0000-00'); consultarCnpj(digits); } });

    // Trigger init after short delay for edit pages
    setTimeout(function(){ try{ atualizarMascaraCpfCnpj(); const tipoPessoa = $('input[name="tipo_pessoa"]:checked').val(); const digits = $('#cpf_cnpj').val().replace(/\D/g,''); if (tipoPessoa === 'PJ' && digits.length === 14) $('#cpf_cnpj').trigger('blur'); } catch(e){ console.warn('init fail', e); } }, 300);
  }

  function consultarCnpj(digits){
    if (!digits) return;
    $('#hint_cpf_cnpj').html('<i class="fas fa-spinner fa-spin"></i> Buscando dados do CNPJ...');
    return $.ajax({ url: `https://brasilapi.com.br/api/cnpj/v1/${digits}`, method: 'GET', dataType: 'json', timeout:10000 })
      .done(function(data){
        if (data && !data.message){
          if (!$('#nome').val()) $('#nome').val(data.razao_social || '');
          if (!$('#apelido').val()) $('#apelido').val(data.nome_fantasia || '');
          if (!$('#telefone').val() && data.ddd_telefone_1){ const tel = data.ddd_telefone_1.replace(/\D/g,''); if (tel.length >= 10) { $('#telefone').unmask().mask('(00) 00000-0000').val(tel); } }
          if (data.cep){ const cep = data.cep.replace(/\D/g,''); $('#cep').val(cep).trigger('blur'); }
          else { if (data.logradouro) $('#logradouro').val(data.logradouro); if (data.bairro) $('#bairro').val(data.bairro); if (data.municipio) $('#cidade').val(data.municipio); if (data.uf) $('#uf').val(data.uf); }
          $('#hint_cpf_cnpj').html('<i class="fas fa-check-circle text-success"></i> Dados do CNPJ carregados!');
        } else {
          $('#hint_cpf_cnpj').html('<i class="fas fa-exclamation-circle text-warning"></i> CNPJ não encontrado na base de dados');
        }
      }).fail(function(xhr, status, error){ $('#hint_cpf_cnpj').html('<i class="fas fa-times-circle text-danger"></i> Erro ao consultar CNPJ'); console.error('Erro na consulta do CNPJ:', error); });
  }

  // Expose to global
  window.formUtils = { init: initFormUtils, buscarCep: buscarCep, atualizarMascaraCpfCnpj: atualizarMascaraCpfCnpj };

  // Initialize on DOM ready
  $(document).ready(function(){ initFormUtils(); });

})(window, jQuery);
