# -*- coding: utf-8 -*-
"""
Script para inserir dados padrão na tabela configuracao
"""

import sqlite3
import os
from datetime import datetime

def inserir_dados_configuracao():
    """Insere dados padrão na tabela configuracao"""
    
    # Caminho para o banco de dados SQLite
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "erp.db")
    
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado: {db_path}")
        return False
        
    try:
        # Conectar diretamente ao SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se já existem dados
        cursor.execute("SELECT COUNT(*) FROM configuracao")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Já existem {count} registro(s) na tabela configuracao.")
            return True
        
        # Inserir dados padrão da JSP
        dados = {
            'nome_fantasia': 'JSP ELÉTRICA INDUSTRIAL & SOLAR',
            'razao_social': 'JSP ELÉTRICA INDUSTRIAL & SOLAR LTDA',
            'cnpj': '41.280.764/0001-65',
            'inscricao_estadual': '',
            'telefone': '(15) 99670-2036',
            'email': 'atendimento@eletricasaroba.com',
            'site': '',
            'logo': '',
            'cep': '18532-122',
            'logradouro': 'Rua Indalécio Costa',
            'numero': '890',
            'bairro': 'Barra Funda',
            'cidade': 'Tietê',
            'uf': 'SP',
            'banco': '403 – CORA SCFI',
            'agencia': '0001',
            'conta': '4633457-0',
            'pix': '41.280.764/0001-65',
            'missao': 'Prover soluções elétricas industriais e solares de qualidade.',
            'visao': 'Ser referência em soluções elétricas sustentáveis.',
            'valores': 'Qualidade, Inovação, Sustentabilidade.',
            'frase_assinatura': 'JSP Elétrica - Energia que move o futuro',
            'tema': 'dark',
            'cor_principal': '#002755',
            'exibir_logo_em_pdfs': True,
            'exibir_rodape_padrao': True,
            'criado_em': datetime.now().isoformat(),
            'atualizado_em': datetime.now().isoformat(),
            'ativo': True
        }
        
        # Preparar SQL de inserção
        colunas = ', '.join(dados.keys())
        placeholders = ', '.join(['?' for _ in dados])
        sql = f"INSERT INTO configuracao ({colunas}) VALUES ({placeholders})"
        
        # Executar inserção
        cursor.execute(sql, list(dados.values()))
        conn.commit()
        
        print("✓ Dados padrão inseridos com sucesso na tabela configuracao!")
        print(f"✓ Empresa: {dados['nome_fantasia']}")
        print(f"✓ CNPJ: {dados['cnpj']}")
        print(f"✓ Endereço: {dados['logradouro']}, {dados['numero']} - {dados['bairro']} - {dados['cidade']}/{dados['uf']}")
        
    except Exception as e:
        print(f"Erro ao inserir dados: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == '__main__':
    print("=== Inserção de Dados Padrão na Configuração ===")
    if inserir_dados_configuracao():
        print("\n🎉 Dados inseridos com sucesso! A aba Configuração deve funcionar agora.")
    else:
        print("\n❌ Falha na inserção dos dados.")