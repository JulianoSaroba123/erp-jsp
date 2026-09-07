# -*- coding: utf-8 -*-
"""Aplica a correção do JavaScript quebrado do formulário de fornecedor.

Uso local na branch fix/fornecedor-autocomplete-cnpj.
Não altera banco de dados.
"""
from pathlib import Path

FORM = Path('app/fornecedor/templates/fornecedor/form.html')


def main():
    texto = FORM.read_text(encoding='utf-8')

    if 'btnConsultarCnpj' not in texto:
        raise SystemExit('ABORTADO: marcador btnConsultarCnpj não encontrado; revise o template antes de aplicar.')

    texto = texto.replace('btnConsultarCnpj', 'btnCnpj')

    duplicado = """btnCnpj.addEventListener('click', function() {
                console.log('🖱️ BOTÃO CLICADO!');
            btnCnpj.addEventListener('click', function() {"""

    if duplicado not in texto:
        raise SystemExit('ABORTADO: listener CNPJ duplicado esperado não foi encontrado.')

    texto = texto.replace(
        duplicado,
        """btnCnpj.addEventListener('click', function() {""",
        1,
    )

    final_quebrado = """            });
        console.log('⚙️ Inicializando interface...');
        atualizarInterface();

        // Foco no tipo primeiro
        tipoSelect.focus();
        console.log('✅ Script de fornecedor carregado com sucesso!'e();

        // Foco no tipo primeiro
        tipoSelect.focus();
    });"""

    final_correto = """            });
        }

        console.log('⚙️ Inicializando interface...');
        atualizarInterface();

        // Foco no tipo primeiro
        tipoSelect.focus();
        console.log('✅ Script de fornecedor carregado com sucesso!');
    });"""

    if final_quebrado not in texto:
        raise SystemExit('ABORTADO: bloco final quebrado esperado não foi encontrado.')

    texto = texto.replace(final_quebrado, final_correto, 1)

    FORM.write_text(texto, encoding='utf-8')
    print('OK - JavaScript do fornecedor corrigido.')


if __name__ == '__main__':
    main()
