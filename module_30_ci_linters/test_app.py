from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from database import async_session, init_db
from main import app
from models import Recipe

# Создаем транспорт для запуска FastAPI приложения в тестах
transport = ASGITransport(app=app)


@pytest.fixture(autouse=True, scope="module")
async def initialize_db() -> None:
    """Инициализирует базу данных перед запуском тестов"""
    await init_db()


@pytest.fixture(autouse=True)
async def cleanup_db() -> AsyncGenerator[None, None]:
    """Очищает таблицу перед каждым тестом"""
    async with async_session() as session:
        await session.execute(text("DELETE FROM recipes"))
        await session.commit()
        yield


@pytest.mark.asyncio
async def test_create_recipe() -> None:
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/recipes",
            json={
                "title": "Test Cake",
                "cooking_time": 60,
                "ingredients": "flour, eggs, sugar",
                "description": "Mix ingredients and bake.",
            },
        )
    assert response.status_code == 201  # ← Изменили с 200 на 201
    data = response.json()
    assert data["title"] == "Test Cake"
    assert data["views"] == 0
    assert data["cooking_time"] == 60


@pytest.mark.asyncio
async def test_get_recipes_sorted() -> None:
    # Сначала создаем тестовые данные
    async with async_session() as session:
        session.add_all(
            [
                Recipe(
                    title="Cake",
                    views=5,
                    cooking_time=45,
                    ingredients="flour, eggs",
                    description="Delicious cake",
                ),
                Recipe(
                    title="Pie",
                    views=5,
                    cooking_time=30,
                    ingredients="apples, flour",
                    description="Sweet pie",
                ),
                Recipe(
                    title="Soup",
                    views=3,
                    cooking_time=20,
                    ingredients="carrot, potato",
                    description="Healthy soup",
                ),
            ]
        )
        await session.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/recipes")

    assert response.status_code == 200
    recipes = response.json()

    # Оставляем только те рецепты, которые мы создали в этом тесте
    test_recipes = [r for r in recipes if r["title"] in ["Cake", "Pie", "Soup"]]
    assert [r["title"] for r in test_recipes] == ["Pie", "Cake", "Soup"]


@pytest.mark.asyncio
async def test_get_recipe_details_and_views_increment() -> None:
    # Сначала создаем тестовый рецепт
    async with async_session() as session:
        recipe = Recipe(
            title="Delicious Soup",
            cooking_time=20,
            ingredients="water, salt, vegetables",
            description="Boil everything together.",
        )
        session.add(recipe)
        await session.commit()
        recipe_id = recipe.id

    # Первый запрос - счетчик должен стать 1
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["views"] == 1

    # Второй запрос - счетчик должен стать 2
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["views"] == 2


@pytest.mark.asyncio
async def test_recipe_not_found() -> None:
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/recipes/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Recipe not found"}
