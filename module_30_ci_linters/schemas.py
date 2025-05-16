from typing import List

from pydantic import BaseModel, ConfigDict, field_validator


class RecipeCreate(BaseModel):
    title: str
    cooking_time: int
    ingredients: str
    description: str

    @field_validator('cooking_time')
    def validate_cooking_time(cls, v):
        if v <= 0:
            raise ValueError("Cooking time must be a positive integer")
        return v


class RecipeOut(BaseModel):
    id: int
    title: str
    views: int
    cooking_time: int
    model_config = ConfigDict(from_attributes=True)


class RecipeDetailsOut(BaseModel):
    id: int
    title: str
    cooking_time: int
    ingredients: str
    description: str
    views: int
    model_config = ConfigDict(from_attributes=True)