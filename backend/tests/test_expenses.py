"""Tests for expense management functionality."""

import pytest
from datetime import datetime
from sqlalchemy import select

from app import models


class TestExpenseAPI:
    """Test expense API endpoints."""

    @pytest.mark.asyncio
    async def test_create_expense(self, client, db_session):
        """Test creating a new expense."""
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

        # Create a category first
        category_data = {
            "name": "Food",
            "description": "Food expenses"
        }

        category_response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        category_id = category_response.json()["id"]

        # Create an expense
        expense_data = {
            "category_id": category_id,
            "amount": 25.50,
            "note": "Lunch at restaurant"
        }

        response = await client.post(
            "/expenses",
            json=expense_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201

        data = response.json()
        assert data["amount"] == 25.50
        assert data["note"] == "Lunch at restaurant"
        assert data["category_id"] == category_id
        assert "id" in data
        assert "created_at" in data
        assert "category_path" in data

    @pytest.mark.asyncio
    async def test_get_expenses_list(self, client, db_session):
        """Test getting list of expenses."""
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
            "name": "Food",
            "description": "Food expenses"
        }

        category_response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        category_id = category_response.json()["id"]

        # Create multiple expenses
        expenses_data = [
            {"category_id": category_id, "amount": 15.00, "note": "Coffee"},
            {"category_id": category_id, "amount": 30.00, "note": "Dinner"},
        ]

        for expense_data in expenses_data:
            await client.post(
                "/expenses",
                json=expense_data,
                headers={"Authorization": f"Bearer {token}"}
            )

        # Get expenses list
        response = await client.get(
            "/expenses",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2

        # Check expense structure
        for expense in data:
            assert "id" in expense
            assert "amount" in expense
            assert "category_id" in expense
            assert "created_at" in expense
            assert "category_path" in expense

    @pytest.mark.asyncio
    async def test_update_expense(self, client, db_session):
        """Test updating an expense."""
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
            "name": "Food",
            "description": "Food expenses"
        }

        category_response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        category_id = category_response.json()["id"]

        # Create an expense
        expense_data = {
            "category_id": category_id,
            "amount": 20.00,
            "note": "Original expense"
        }

        create_response = await client.post(
            "/expenses",
            json=expense_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        expense_id = create_response.json()["id"]

        # Update the expense
        update_data = {
            "amount": 25.00,
            "note": "Updated expense"
        }

        response = await client.patch(
            f"/expenses/{expense_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == expense_id
        assert data["amount"] == 25.00
        assert data["note"] == "Updated expense"

    @pytest.mark.asyncio
    async def test_delete_expense(self, client, db_session):
        """Test deleting an expense."""
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
            "name": "Food",
            "description": "Food expenses"
        }

        category_response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        category_id = category_response.json()["id"]

        # Create an expense
        expense_data = {
            "category_id": category_id,
            "amount": 15.00,
            "note": "Test expense"
        }

        create_response = await client.post(
            "/expenses",
            json=expense_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        expense_id = create_response.json()["id"]

        # Delete the expense
        response = await client.delete(
            f"/expenses/{expense_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_expense_validation_negative_amount(self, client, db_session):
        """Test that negative amounts are rejected."""
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
            "name": "Food",
            "description": "Food expenses"
        }

        category_response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        category_id = category_response.json()["id"]

        # Try to create expense with negative amount
        expense_data = {
            "category_id": category_id,
            "amount": -10.00,
            "note": "Invalid expense"
        }

        response = await client.post(
            "/expenses",
            json=expense_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_expense_validation_zero_amount(self, client, db_session):
        """Test that zero amounts are rejected."""
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
            "name": "Food",
            "description": "Food expenses"
        }

        category_response = await client.post(
            "/categories",
            json=category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        category_id = category_response.json()["id"]

        # Try to create expense with zero amount
        expense_data = {
            "category_id": category_id,
            "amount": 0.00,
            "note": "Invalid expense"
        }

        response = await client.post(
            "/expenses",
            json=expense_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_expenses_by_category(self, client, db_session):
        """Test getting expenses filtered by category."""
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

        # Create two categories
        food_category_data = {
            "name": "Food",
            "description": "Food expenses"
        }

        transport_category_data = {
            "name": "Transport",
            "description": "Transport expenses"
        }

        food_response = await client.post(
            "/categories",
            json=food_category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        food_category_id = food_response.json()["id"]

        transport_response = await client.post(
            "/categories",
            json=transport_category_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        transport_category_id = transport_response.json()["id"]

        # Create expenses in different categories
        expenses_data = [
            {"category_id": food_category_id, "amount": 15.00, "note": "Lunch"},
            {"category_id": food_category_id, "amount": 8.00, "note": "Coffee"},
            {"category_id": transport_category_id, "amount": 25.00, "note": "Bus ticket"},
        ]

        for expense_data in expenses_data:
            await client.post(
                "/expenses",
                json=expense_data,
                headers={"Authorization": f"Bearer {token}"}
            )

        # Get expenses for food category only
        response = await client.get(
            f"/categories/{food_category_id}/expenses",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2

        # Verify all expenses are for the food category
        for expense in data:
            assert expense["category_id"] == food_category_id
