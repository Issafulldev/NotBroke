#!/usr/bin/env python3
"""Script de migration manuelle pour Render - Ajoute la colonne currency aux expenses"""

import asyncio
import sys
import os
from pathlib import Path

# Ajouter le répertoire backend au path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from alembic import command
from alembic.config import Config
from app.config import config as app_config
from app.database import engine
from sqlalchemy import text

async def check_currency_column():
    """Vérifier si la colonne currency existe."""
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='expenses' AND column_name='currency'
            """)
        )
        row = result.first()
        return row is not None

async def run_migration():
    """Exécuter la migration Alembic."""
    print("🔄 Vérification de l'état de la base de données...")
    
    # Vérifier si la colonne existe déjà
    column_exists = await check_currency_column()
    
    if column_exists:
        print("✅ La colonne 'currency' existe déjà dans la table 'expenses'")
        return 0
    
    print("⚠️  La colonne 'currency' n'existe pas. Exécution de la migration...")
    
    # Configurer Alembic
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    
    # Vérifier la version actuelle
    print("\n📋 Version actuelle des migrations:")
    try:
        command.current(alembic_cfg)
    except Exception as e:
        print(f"⚠️  Impossible de récupérer la version actuelle: {e}")
    
    # Exécuter la migration
    print("\n🚀 Exécution de la migration 'add_currency_to_expenses'...")
    try:
        command.upgrade(alembic_cfg, "head")
        print("✅ Migration appliquée avec succès!")
        
        # Vérifier que la colonne existe maintenant
        column_exists = await check_currency_column()
        if column_exists:
            print("✅ Vérification: La colonne 'currency' existe maintenant")
            return 0
        else:
            print("❌ Erreur: La colonne 'currency' n'existe toujours pas après la migration")
            return 1
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return 1

async def main():
    """Point d'entrée principal."""
    print("=" * 70)
    print("🔧 SCRIPT DE MIGRATION - Ajout de la colonne currency")
    print("=" * 70)
    print(f"Base de données: {app_config.get('DATABASE_URL', 'Non configurée').split('@')[1] if '@' in app_config.get('DATABASE_URL', '') else 'Non configurée'}")
    print("=" * 70)
    
    exit_code = await run_migration()
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ Migration terminée avec succès!")
    else:
        print("❌ Migration échouée. Vérifiez les logs ci-dessus.")
    print("=" * 70)
    
    return exit_code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

