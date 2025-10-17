"""Tests for category management functionality."""

import pytest
from sqlalchemy import select

from app import models


class TestCategoryAPI:
    """Test category API endpoints."""

    @pytest.mark.asyncio
    async def test_create_category(self, client, db_session):
        """Test creating a new category."""
        # First create and authenticate a user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Create a category
        category_data = {
            "name": "Test Category",
            "description": "A test category"
        }

        response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Category"
        assert data["description"] == "A test category"
        assert "id" in data
        assert "full_path" in data
        assert data["full_path"] == "Test Category"

    @pytest.mark.asyncio
    async def test_get_categories_list(self, client, db_session):
        """Test getting list of categories."""
        # Create and authenticate user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Create categories
        categories_data = [
            {"name": "Food", "description": "Food expenses"},
            {"name": "Transport", "description": "Transport expenses"},
        ]

        for category_data in categories_data:
            await client.post(
                "/categories",
                json=category_data,
                headers={"Authorization": f"Bearer {token}"}
            )

        # Get categories list
        response = await client.get(
            "/categories",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2

        # Check that categories have correct structure
        for category in data:
            assert "id" in category
            assert "name" in category
            assert "full_path" in category
            assert "children" in category
            assert isinstance(category["children"], list)

    @pytest.mark.asyncio
    async def test_get_single_category(self, client, db_session):
        """Test getting a single category."""
        # Create and authenticate user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Create a category
        category_data = {
            "name": "Test Category",
            "description": "A test category"
        }

        create_response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        category_id = create_response.json()["id"]

        # Get the category
        response = await client.get(
            f"/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == category_id
        assert data["name"] == "Test Category"
        assert data["description"] == "A test category"

    @pytest.mark.asyncio
    async def test_update_category(self, client, db_session):
        """Test updating a category."""
        # Create and authenticate user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Create a category
        category_data = {
            "name": "Original Name",
            "description": "Original description"
        }

        create_response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        category_id = create_response.json()["id"]

        # Update the category
        update_data = {
            "name": "Updated Name",
            "description": "Updated description"
        }

        response = await client.patch(
            f"/categories/{category_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == category_id
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_category(self, client, db_session):
        """Test deleting a category."""
        # Create and authenticate user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Create a category
        category_data = {
            "name": "Test Category",
            "description": "A test category"
        }

        create_response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        category_id = create_response.json()["id"]

        # Delete the category
        response = await client.delete(
            f"/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify category is deleted
        get_response = await client.get(
            f"/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_category_hierarchy(self, client, db_session):
        """Test creating hierarchical categories."""
        # Create and authenticate user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Create parent category
        parent_data = {
            "name": "Transport",
            "description": "Transportation expenses"
        }

        parent_response = await client.post(
            "/categories",
            json=parent_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        parent_id = parent_response.json()["id"]

        # Create child category
        child_data = {
            "name": "Car",
            "description": "Car expenses",
            "parent_id": parent_id
        }

        child_response = await client.post(
            "/categories",
            json=child_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert child_response.status_code == 201

        child_data_response = child_response.json()
        assert child_data_response["name"] == "Car"
        assert child_data_response["parent_id"] == parent_id
        assert child_data_response["full_path"] == "Transport / Car"

    @pytest.mark.asyncio
    async def test_duplicate_category_name_error(self, client, db_session):
        """Test that duplicate category names are rejected."""
        # Create and authenticate user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        await client.post("/auth/register", json=user_data)

        login_response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        # Create first category
        category_data = {
            "name": "Test Category",
            "description": "First category"
        }

        await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        # Try to create duplicate
        duplicate_data = {
            "name": "Test Category",
            "description": "Duplicate category"
        }

        response = await client.post(
            "/categories",
            json=duplicate_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
