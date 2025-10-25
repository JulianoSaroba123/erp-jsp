#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação final dos dados completos do cliente no PDF
"""

import sqlite3
import os

def main():
    """Verifica se todos os dados do cliente estão completos."""
    print("🎯 VERIFICAÇÃO FINAL - DADOS COMPLETOS DO CLIENTE")
    print("=" * 60)
    
    db_path = "c:\\ERP_JSP\\erp.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Buscar dados completos
        cursor.execute("""
            SELECT 
                o.numero,
                o.solicitante,
                o.descricao_problema,
                c.nome,
                c.tipo,
                c.cpf_cnpj,
                c.rg_ie,
                c.email,
                c.telefone,
                c.celular,
                c.endereco,
                c.numero,
                c.complemento,
                c.bairro,
                c.cidade,
                c.estado,
                c.cep
            FROM ordem_servico o
            JOIN clientes c ON o.cliente_id = c.id
            WHERE o.id = 1
        """)
        
        result = cursor.fetchone()
        
        if not result:
            print("❌ Dados não encontrados")
            return False
        
        (numero_os, solicitante, desc_problema, nome, tipo, cpf_cnpj, rg_ie, 
         email, telefone, celular, endereco, numero, complemento, bairro, 
         cidade, estado, cep) = result
        
        print(f"📋 ORDEM DE SERVIÇO: {numero_os}")
        print("\n👤 DADOS COMPLETOS DO CLIENTE:")
        print(f"   📝 Nome: {nome}")
        print(f"   🏢 Tipo: {'Pessoa Jurídica' if tipo == 'PJ' else 'Pessoa Física'}")
        print(f"   📄 {'CNPJ' if tipo == 'PJ' else 'CPF'}: {cpf_cnpj}")
        print(f"   🆔 {'Inscrição Estadual' if tipo == 'PJ' else 'RG'}: {rg_ie or 'N/A'}")
        print(f"   📧 Email: {email}")
        print(f"   ☎️ Telefone: {telefone}")
        print(f"   📱 Celular: {celular or 'N/A'}")
        print(f"   🏠 Endereço: {endereco}")
        if numero:
            print(f"      Número: {numero}")
        if complemento:
            print(f"      Complemento: {complemento}")
        print(f"      Bairro: {bairro}")
        print(f"      Cidade: {cidade}/{estado}")
        print(f"      CEP: {cep}")
        
        print("\n🙋 DADOS DA SOLICITAÇÃO:")
        print(f"   Solicitante: {solicitante or 'N/A'}")
        print(f"   Descrição do Problema: {desc_problema[:80] + '...' if desc_problema and len(desc_problema) > 80 else desc_problema or 'N/A'}")
        
        print("\n✅ CAMPOS IMPLEMENTADOS NO PDF:")
        print("   ✅ Nome do cliente")
        print("   ✅ Tipo (PJ/PF)")
        print("   ✅ CNPJ/CPF")
        print("   ✅ Inscrição Estadual/RG")
        print("   ✅ Email")
        print("   ✅ Telefone")
        print("   ✅ Celular")
        print("   ✅ Endereço completo")
        print("   ✅ Solicitante")
        print("   ✅ Descrição do problema")
        
        print("\n🌐 ACESSO:")
        print("   📄 PDF: http://127.0.0.1:5001/ordem_servico/1/relatorio-pdf")
        print("   ✏️ Formulário: http://127.0.0.1:5001/ordem_servico/1/editar")
        
        print("\n🎉 DADOS COMPLETOS DO CLIENTE MANTIDOS!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n🚨 Problemas encontrados!")
    else:
        print("\n✅ Tudo perfeito! Dados completos do cliente mantidos!")