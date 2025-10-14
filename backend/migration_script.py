#!/usr/bin/env python3
"""
Script de migration pour attribuer les données existantes au premier utilisateur créé.
Ce script doit être exécuté après avoir créé le schéma de base de données avec les nouvelles colonnes user_id.
"""

import asyncio
import os
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Ajouter le répertoire backend au path
sys.path.append(os.path.dirname(__file__))

from app.database import Base
from app import models
from app.auth import hash_password


async def migrate_existing_data():
    """Migrer les données existantes vers le nouveau schéma avec utilisateurs"""
    # Configuration de la base de données
    database_url = "sqlite:///./expense.db"

    # Créer le moteur et la session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as session:
        try:
            # Vérifier si les tables existent déjà
            try:
                session.execute(select(models.User).limit(1))
                user_exists = True
            except:
                user_exists = False

            if user_exists:
                print("Les données ont déjà été migrées.")
                return

            # Créer l'utilisateur par défaut
            print("Création de l'utilisateur par défaut...")
            default_user = models.User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),  # À changer !
                is_active=True
            )
            session.add(default_user)
            session.commit()

            # Récupérer l'ID du nouvel utilisateur
            user_id = default_user.id
            print(f"Utilisateur créé avec l'ID: {user_id}")

            # Compter les données existantes
            categories_count = session.query(models.Category).count()
            expenses_count = session.query(models.Expense).count()

            print(f"Nombre de catégories trouvées: {categories_count}")
            print(f"Nombre de dépenses trouvées: {expenses_count}")

            if categories_count > 0:
                print("Attribution des catégories à l'utilisateur...")
                # Attribuer toutes les catégories existantes à cet utilisateur
                session.query(models.Category).update({models.Category.user_id: user_id})
                print(f"{categories_count} catégories attribuées à l'utilisateur {user_id}")

            if expenses_count > 0:
                print("Attribution des dépenses à l'utilisateur...")
                # Attribuer toutes les dépenses existantes à cet utilisateur
                session.query(models.Expense).update({models.Expense.user_id: user_id})
                print(f"{expenses_count} dépenses attribuées à l'utilisateur {user_id}")

            session.commit()
            print("✅ Migration terminée avec succès !")
            print(f"📊 {categories_count} catégories et {expenses_count} dépenses attribuées à l'utilisateur {user_id}")
            print("🔐 Vous pouvez maintenant vous connecter avec:")
            print("   Username: admin")
            print("   Password: admin123")
            print("⚠️  N'oubliez pas de changer le mot de passe par défaut !")

        except Exception as e:
            session.rollback()
            print(f"❌ Erreur lors de la migration: {e}")
            raise


if __name__ == "__main__":
    print("🚀 Démarrage de la migration des données...")
    asyncio.run(migrate_existing_data())
