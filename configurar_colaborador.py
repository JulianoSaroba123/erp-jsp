#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar usuário colaborador corretamente
"""

import sqlite3
import os

DB_PATH = 'database/database.db'

if not os.path.exists(DB_PATH):
    print(f"❌ Banco não encontrado: {DB_PATH}")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("🔧 CONFIGURAR USUÁRIO COLABORADOR")
print("=" * 60)

try:
    # 1. Verificar se coluna tipo_usuario existe
    cursor.execute("PRAGMA table_info(usuario)")
    colunas = [row[1] for row in cursor.fetchall()]
    
    if 'tipo_usuario' not in colunas:
        print("\n⚠️  Coluna tipo_usuario não existe. Criando...")
        cursor.execute("ALTER TABLE usuario ADD COLUMN tipo_usuario VARCHAR(20) DEFAULT 'usuario'")
        conn.commit()
        print("✅ Coluna tipo_usuario criada!")
    else:
        print("\n✅ Coluna tipo_usuario já existe")
    
    # 2. Verificar se usuário colaborador existe
    cursor.execute("SELECT id, username, nome, tipo_usuario FROM usuario WHERE username = 'colaborador'")
    usuario = cursor.fetchone()
    
    if usuario:
        id_, username, nome, tipo_atual = usuario
        print(f"\n📌 Usuário encontrado:")
        print(f"   ID: {id_}")
        print(f"   Username: {username}")
        print(f"   Nome: {nome}")
        print(f"   Tipo atual: {tipo_atual if tipo_atual else 'NÃO DEFINIDO'}")
        
        if tipo_atual != 'colaborador':
            print(f"\n🔧 Atualizando tipo_usuario para 'colaborador'...")
            cursor.execute("UPDATE usuario SET tipo_usuario = 'colaborador' WHERE username = 'colaborador'")
            conn.commit()
            print("✅ Tipo atualizado com sucesso!")
        else:
            print("\n✅ Tipo já está correto!")
    else:
        print("\n⚠️  Usuário 'colaborador' não existe!")
        print("\n💡 Criando usuário colaborador...")
        
        # Hash da senha '123456' usando werkzeug
        from werkzeug.security import generate_password_hash
        senha_hash = generate_password_hash('123456')
        
        cursor.execute("""
            INSERT INTO usuario (username, nome, email, senha, tipo_usuario, ativo, data_criacao)
            VALUES ('colaborador', 'Técnico Colaborador', 'colaborador@jsp.com', ?, 'colaborador', 1, datetime('now'))
        """, (senha_hash,))
        conn.commit()
        print("✅ Usuário colaborador criado!")
        print("   Username: colaborador")
        print("   Senha: 123456")
    
    # 3. Verificar resultado final
    print("\n" + "=" * 60)
    print("📊 VERIFICAÇÃO FINAL")
    print("=" * 60)
    
    cursor.execute("SELECT username, nome, tipo_usuario FROM usuario WHERE username = 'colaborador'")
    result = cursor.fetchone()
    
    if result:
        username, nome, tipo = result
        print(f"\n✅ Configuração confirmada:")
        print(f"   Username: {username}")
        print(f"   Nome: {nome}")
        print(f"   Tipo: {tipo}")
        print(f"\n🎯 Pronto para usar!")
        print(f"   1. Faça logout")
        print(f"   2. Login com: colaborador / 123456")
        print(f"   3. As seções financeiras devem estar ocultas")
    
except sqlite3.Error as e:
    print(f"\n❌ Erro SQL: {e}")
    conn.rollback()
finally:
    conn.close()

print("\n" + "=" * 60)
