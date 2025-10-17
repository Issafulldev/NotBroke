"""Tests for authentication functionality."""

import pytest
from sqlalchemy import select

from app import models, schemas
from app.auth import hash_password, verify_password


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test that password hashing works."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt format
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword123"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False


class TestAuthAPI:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, client, db_session):
        """Test successful user registration."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }

        response = await client.post("/auth/register", json=user_data)

        assert response.status_code == 201

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "is_active" in data

        # Verify user was created in database
        result = await db_session.execute(
            select(models.User).where(models.User.username == "testuser")
        )
        user = result.scalars().first()
        assert user is not None
        assert user.email == "test@example.com"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, db_session):
        """Test registration with duplicate username fails."""
        # Create first user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        # Try to create user with same username but different email
        duplicate_data = {
            "username": "testuser",
            "email": "test2@example.com",
            "password": "testpassword456"
        }

        response = await client.post("/auth/register", json=duplicate_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, db_session):
        """Test registration with duplicate email fails."""
        # Create first user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        # Try to create user with same email but different username
        duplicate_data = {
            "username": "testuser2",
            "email": "test@example.com",
            "password": "testpassword456"
        }

        response = await client.post("/auth/register", json=duplicate_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client, db_session):
        """Test successful login."""
        # First register a user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        # Now try to login
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }

        response = await client.post("/auth/login", json=login_data)

        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, db_session):
        """Test login with wrong password fails."""
        # First register a user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        # Try to login with wrong password
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        response = await client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user fails."""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }

        response = await client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
