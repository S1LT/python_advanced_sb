from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator, List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import async_session, init_db
from models import Recipe
from schemas import RecipeCreate, RecipeDetailsOut, RecipeOut


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@app.post("/recipes", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
async def create_recipe(recipe: RecipeCreate, db: DatabaseSession) -> RecipeOut:
    db_recipe = Recipe(**recipe.model_dump())
    db.add(db_recipe)
    await db.commit()
    await db.refresh(db_recipe)
    return db_recipe


@app.get("/recipes", response_model=List[RecipeOut])
async def get_recipes(db: DatabaseSession) -> List[RecipeOut]:
    result = await db.execute(
        select(Recipe).order_by(Recipe.views.desc(), Recipe.cooking_time.asc())
    )
    recipes: List[RecipeOut] = result.scalars().all()
    return recipes


@app.get("/recipes/{recipe_id}", response_model=RecipeDetailsOut)
async def get_recipe_by_id(recipe_id: int, db: DatabaseSession) -> RecipeDetailsOut:
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe: RecipeDetailsOut = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    recipe.views += 1
    await db.commit()
    await db.refresh(recipe)
    return recipe
