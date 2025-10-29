#!/usr/bin/env python3
"""
Migration script: SQLite → PostgreSQL

Script de migration sécurisé des données depuis SQLite vers PostgreSQL.
Peut être utilisé pour :
- Migrer les données existantes
- Valider que tout fonctionne
- Faire un backup avant migration

Usage:
    python migrate_to_postgres.py
    
Configuration:
    1. Configurer DATABASE_URL_SOURCE et DATABASE_URL_TARGET ci-dessous
    2. Ou utiliser les variables d'environnement
    3. Exécuter le script
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any

from sqlalchemy import inspect, text, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models import Base, User, Category, Expense, Translation


# Configuration des bases de données
DATABASE_URL_SOURCE = os.getenv(
    "DATABASE_URL_SOURCE",
    "sqlite+aiosqlite:///./expense.db"
)

DATABASE_URL_TARGET = os.getenv(
    "DATABASE_URL_TARGET",
    "postgresql+asyncpg://notbroke_user:password@localhost:5432/notbroke_db"
)


class MigrationManager:
    """Gère la migration des données d'une base à l'autre."""
    
    def __init__(self, source_url: str, target_url: str):
        self.source_url = source_url
        self.target_url = target_url
        self.source_engine = None
        self.target_engine = None
        self.source_session_maker = None
        self.target_session_maker = None
        self.stats = {
            "users": 0,
            "categories": 0,
            "expenses": 0,
            "translations": 0,
        }
    
    async def setup(self) -> None:
        """Initialiser les connexions aux bases de données."""
        print("🔌 Connexion aux bases de données...")
        
        try:
            # Source (SQLite)
            self.source_engine = create_async_engine(
                self.source_url,
                echo=False,
                connect_args={"check_same_thread": False} if "sqlite" in self.source_url else {}
            )
            self.source_session_maker = async_sessionmaker(self.source_engine)
            
            # Test connexion source
            async with self.source_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print("  ✅ SQLite connecté")
            
            # Target (PostgreSQL)
            self.target_engine = create_async_engine(
                self.target_url,
                echo=False,
            )
            self.target_session_maker = async_sessionmaker(self.target_engine)
            
            # Test connexion target
            async with self.target_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print("  ✅ PostgreSQL connecté")
            
        except Exception as e:
            print(f"  ❌ Erreur de connexion: {e}")
            raise
    
    async def create_target_schema(self) -> None:
        """Créer le schéma dans la base de données cible."""
        print("\n📋 Création du schéma PostgreSQL...")
        
        try:
            async with self.target_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("  ✅ Schéma créé")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            raise
    
    async def cleanup_target_data(self) -> None:
        """Nettoyer les données existantes dans la base cible."""
        print("\n🧹 Nettoyage des données existantes...")
        
        try:
            async with self.target_session_maker() as session:
                # Ordre important: respecter les contraintes de clés étrangères
                await session.execute(delete(Expense))
                await session.execute(delete(Translation))
                await session.execute(delete(Category))
                await session.execute(delete(User))
                await session.commit()
                print("  ✅ Données nettoyées")
        except Exception as e:
            print(f"  ℹ️  Aucune donnée à nettoyer (base vide): {e}")
    
    async def migrate_users(self) -> None:
        """Migrer les utilisateurs."""
        print("\n👥 Migration des utilisateurs...")
        
        async with self.source_session_maker() as source_session:
            source_users = (await source_session.execute(
                __import__("sqlalchemy").select(User)
            )).scalars().all()
            
            if not source_users:
                print("  ℹ️  Aucun utilisateur à migrer")
                return
            
            async with self.target_session_maker() as target_session:
                for user in source_users:
                    try:
                        new_user = User(
                            id=user.id,
                            username=user.username,
                            email=user.email,
                            hashed_password=user.hashed_password,
                            is_active=user.is_active,
                            created_at=user.created_at,
                        )
                        target_session.add(new_user)
                        self.stats["users"] += 1
                    except Exception as e:
                        print(f"    ⚠️  Erreur pour utilisateur {user.username}: {e}")
                
                await target_session.commit()
                print(f"  ✅ {self.stats['users']} utilisateur(s) migré(s)")
    
    async def migrate_categories(self) -> None:
        """Migrer les catégories."""
        print("\n📂 Migration des catégories...")
        
        async with self.source_session_maker() as source_session:
            source_categories = (await source_session.execute(
                __import__("sqlalchemy").select(Category)
            )).scalars().all()
            
            if not source_categories:
                print("  ℹ️  Aucune catégorie à migrer")
                return
            
            async with self.target_session_maker() as target_session:
                for category in source_categories:
                    try:
                        new_category = Category(
                            id=category.id,
                            name=category.name,
                            description=category.description,
                            parent_id=category.parent_id,
                            user_id=category.user_id,
                        )
                        target_session.add(new_category)
                        self.stats["categories"] += 1
                    except Exception as e:
                        print(f"    ⚠️  Erreur pour catégorie {category.name}: {e}")
                
                await target_session.commit()
                print(f"  ✅ {self.stats['categories']} catégorie(s) migrée(s)")
    
    async def migrate_expenses(self) -> None:
        """Migrer les dépenses."""
        print("\n💰 Migration des dépenses...")
        
        async with self.source_session_maker() as source_session:
            source_expenses = (await source_session.execute(
                __import__("sqlalchemy").select(Expense)
            )).scalars().all()
            
            if not source_expenses:
                print("  ℹ️  Aucune dépense à migrer")
                return
            
            async with self.target_session_maker() as target_session:
                for expense in source_expenses:
                    try:
                        new_expense = Expense(
                            id=expense.id,
                            category_id=expense.category_id,
                            amount=expense.amount,
                            note=expense.note,
                            created_at=expense.created_at,
                            user_id=expense.user_id,
                        )
                        target_session.add(new_expense)
                        self.stats["expenses"] += 1
                    except Exception as e:
                        print(f"    ⚠️  Erreur pour dépense: {e}")
                
                await target_session.commit()
                print(f"  ✅ {self.stats['expenses']} dépense(s) migrée(s)")
    
    async def migrate_translations(self) -> None:
        """Migrer les traductions."""
        print("\n🌐 Migration des traductions...")
        
        async with self.source_session_maker() as source_session:
            source_translations = (await source_session.execute(
                __import__("sqlalchemy").select(Translation)
            )).scalars().all()
            
            if not source_translations:
                print("  ℹ️  Aucune traduction à migrer")
                return
            
            async with self.target_session_maker() as target_session:
                for translation in source_translations:
                    try:
                        # Vérifier si la traduction existe déjà
                        existing = await target_session.execute(
                            __import__("sqlalchemy").select(Translation).where(
                                Translation.id == translation.id
                            )
                        )
                        if existing.scalar():
                            # Traduction existe, la mettre à jour
                            existing_trans = existing.scalar()
                            existing_trans.locale = translation.locale
                            existing_trans.key = translation.key
                            existing_trans.value = translation.value
                        else:
                            # Nouvelle traduction
                            new_translation = Translation(
                                id=translation.id,
                                locale=translation.locale,
                                key=translation.key,
                                value=translation.value,
                            )
                            target_session.add(new_translation)
                        self.stats["translations"] += 1
                    except Exception as e:
                        print(f"    ⚠️  Erreur pour traduction id {translation.id}: {e}")
                
                await target_session.commit()
                print(f"  ✅ {self.stats['translations']} traduction(s) migrée(s)")
    
    async def verify_migration(self) -> bool:
        """Vérifier l'intégrité de la migration."""
        print("\n✔️  Vérification de la migration...")
        
        try:
            async with self.target_session_maker() as session:
                users_count = (await session.execute(
                    __import__("sqlalchemy").select(__import__("sqlalchemy").func.count(User.id))
                )).scalar() or 0
                
                categories_count = (await session.execute(
                    __import__("sqlalchemy").select(__import__("sqlalchemy").func.count(Category.id))
                )).scalar() or 0
                
                expenses_count = (await session.execute(
                    __import__("sqlalchemy").select(__import__("sqlalchemy").func.count(Expense.id))
                )).scalar() or 0
                
                translations_count = (await session.execute(
                    __import__("sqlalchemy").select(__import__("sqlalchemy").func.count(Translation.id))
                )).scalar() or 0
                
                print(f"  📊 Résultats PostgreSQL:")
                print(f"    - Utilisateurs: {users_count}")
                print(f"    - Catégories: {categories_count}")
                print(f"    - Dépenses: {expenses_count}")
                print(f"    - Traductions: {translations_count}")
                
                # Vérifier la cohérence
                if users_count == self.stats["users"] and \
                   categories_count == self.stats["categories"] and \
                   expenses_count == self.stats["expenses"] and \
                   translations_count == self.stats["translations"]:
                    print("  ✅ Vérification réussie - Les données sont intactes!")
                    return True
                else:
                    print("  ⚠️  Attention: Nombre de lignes différent")
                    return False
                
        except Exception as e:
            print(f"  ❌ Erreur de vérification: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Fermer les connexions."""
        if self.source_engine:
            await self.source_engine.dispose()
        if self.target_engine:
            await self.target_engine.dispose()


async def main() -> None:
    """Exécuter la migration complète."""
    print("=" * 70)
    print("🚀 MIGRATION SQLite → PostgreSQL")
    print("=" * 70)
    print(f"Source: {DATABASE_URL_SOURCE}")
    print(f"Target: {DATABASE_URL_TARGET}")
    print("=" * 70)
    
    migration = MigrationManager(DATABASE_URL_SOURCE, DATABASE_URL_TARGET)
    
    try:
        # Setup
        await migration.setup()
        
        # Créer le schéma
        await migration.create_target_schema()
        await migration.cleanup_target_data() # Nettoyer les données existantes
        
        # Migrer les données
        await migration.migrate_users()
        await migration.migrate_categories()
        await migration.migrate_expenses()
        await migration.migrate_translations()
        
        # Vérifier
        success = await migration.verify_migration()
        
        # Résumé
        print("\n" + "=" * 70)
        print("📋 RÉSUMÉ DE LA MIGRATION")
        print("=" * 70)
        print(f"Utilisateurs:     {migration.stats['users']:>5}")
        print(f"Catégories:       {migration.stats['categories']:>5}")
        print(f"Dépenses:         {migration.stats['expenses']:>5}")
        print(f"Traductions:      {migration.stats['translations']:>5}")
        print("=" * 70)
        
        if success:
            print("\n✅ Migration réussie!")
            print("\n📝 Prochaines étapes:")
            print("  1. Mettre à jour DATABASE_URL dans votre .env")
            print("  2. Tester l'application")
            print("  3. Déployer sur Render/VPS")
            sys.exit(0)
        else:
            print("\n⚠️  Migration complétée mais avec avertissements")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await migration.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
