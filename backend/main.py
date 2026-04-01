"""
CalorieAI - FastAPI backend.
Run: uvicorn main:app --reload --port 8000
"""

import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from model.predict import FoodPredictor, MEAL_SUGGESTIONS, NUTRITION_DB

ROOT_PATH = os.getenv("ROOT_PATH", "/api")
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "model" / "food_model.h5"))
CLASS_PATH = os.getenv("CLASS_NAMES_PATH", str(BASE_DIR / "model" / "class_names.json"))

app = FastAPI(
    title="CalorieAI API",
    description="Food recognition and nutrition tracking",
    version="1.0.0",
    root_path=ROOT_PATH,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MealLog(BaseModel):
    food_class: str
    food_name: str
    serving_g: float
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    timestamp: Optional[str] = None


class GoalUpdate(BaseModel):
    goal: str
    daily_target: int


meal_log: List[dict] = []
user_goal: dict = {"goal": "maintenance", "daily_target": 2000}
predictor = None

DEMO_FOODS = [
    "pizza",
    "hamburger",
    "sushi",
    "caesar_salad",
    "grilled_salmon",
    "ramen",
    "tacos",
    "chocolate_cake",
    "eggs_benedict",
    "pad_thai",
]
_demo_idx = 0


@app.on_event("startup")
async def load() -> None:
    global predictor
    try:
        predictor = FoodPredictor(MODEL_PATH, CLASS_PATH)
        print("Food model loaded")
    except Exception as exc:
        print(f"Demo mode: {exc}")


def demo_result(portion_g: float = 150) -> dict:
    global _demo_idx
    key = DEMO_FOODS[_demo_idx % len(DEMO_FOODS)]
    _demo_idx += 1
    nutrition = NUTRITION_DB[key]
    scale = portion_g / 100.0

    return {
        "food_class": key,
        "food_name": nutrition["name"],
        "category": nutrition["category"],
        "confidence": round(85 + random.random() * 12, 1),
        "serving_g": portion_g,
        "per_100g": {
            "calories": nutrition["calories"],
            "protein": nutrition["protein"],
            "carbs": nutrition["carbs"],
            "fat": nutrition["fat"],
            "fiber": nutrition["fiber"],
            "sugar": nutrition["sugar"],
        },
        "totals": {
            "calories": round(nutrition["calories"] * scale, 1),
            "protein": round(nutrition["protein"] * scale, 1),
            "carbs": round(nutrition["carbs"] * scale, 1),
            "fat": round(nutrition["fat"] * scale, 1),
            "fiber": round(nutrition["fiber"] * scale, 1),
            "sugar": round(nutrition["sugar"] * scale, 1),
        },
        "top5": [
            {
                "class": DEMO_FOODS[((_demo_idx - 1) + i) % len(DEMO_FOODS)],
                "confidence": max(0, 0.9 - i * 0.18),
            }
            for i in range(5)
        ],
        "demo_mode": True,
    }


@app.get("/")
def root() -> dict:
    return {"app": "CalorieAI", "status": "running", "model_loaded": predictor is not None}


@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "model_loaded": predictor is not None,
        "mode": "production" if predictor else "demo",
    }


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    portion_g: float = Query(default=None, description="Portion size in grams"),
) -> JSONResponse:
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    data = await file.read()
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(400, "Max file size: 15MB")

    started_at = time.time()
    try:
        if predictor:
            result = predictor.predict(data, portion_g or 150)
        else:
            time.sleep(0.6)
            result = demo_result(portion_g or 150)
        result["processing_ms"] = round((time.time() - started_at) * 1000)
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(500, f"Prediction error: {exc}") from exc


@app.post("/log")
def log_meal(meal: MealLog) -> dict:
    entry = meal.dict()
    entry["id"] = len(meal_log)
    entry["timestamp"] = entry["timestamp"] or datetime.now().isoformat()
    meal_log.append(entry)
    return {"ok": True, "id": entry["id"], "total_entries": len(meal_log)}


@app.get("/log")
def get_log(date: Optional[str] = None) -> dict:
    entries = [e for e in meal_log if e.get("timestamp", "").startswith(date)] if date else meal_log
    totals = {
        key: round(sum(entry.get(key, 0) for entry in entries), 1)
        for key in ["calories", "protein", "carbs", "fat", "fiber"]
    }
    return {"entries": entries, "totals": totals, "count": len(entries)}


@app.delete("/log/{meal_id}")
def delete_log(meal_id: int) -> dict:
    global meal_log
    meal_log = [entry for entry in meal_log if entry.get("id") != meal_id]
    return {"ok": True}


@app.get("/nutrition/{food_class}")
def get_nutrition(food_class: str, portion_g: float = 100) -> dict:
    nutrition = NUTRITION_DB.get(food_class)
    if not nutrition:
        raise HTTPException(404, f"Food '{food_class}' not in database")

    scale = portion_g / 100
    return {
        "food_class": food_class,
        "food_name": nutrition["name"],
        "category": nutrition["category"],
        "serving_g": portion_g,
        "per_100g": nutrition,
        "totals": {
            key: round(nutrition[key] * scale, 1)
            for key in ["calories", "protein", "carbs", "fat", "fiber", "sugar"]
        },
    }


@app.get("/foods")
def list_foods(category: Optional[str] = None, search: Optional[str] = None) -> dict:
    foods = [
        {
            "key": key,
            **{field: value[field] for field in ["name", "category", "calories", "protein", "carbs", "fat"]},
        }
        for key, value in NUTRITION_DB.items()
    ]

    if category:
        foods = [food for food in foods if food["category"].lower() == category.lower()]
    if search:
        foods = [food for food in foods if search.lower() in food["name"].lower()]

    return {"count": len(foods), "foods": sorted(foods, key=lambda item: item["name"])}


@app.get("/categories")
def get_categories() -> dict:
    categories = sorted(set(value["category"] for value in NUTRITION_DB.values()))
    return {"categories": categories}


@app.get("/goal")
def get_goal() -> dict:
    goal_key = user_goal["goal"]
    suggestion = MEAL_SUGGESTIONS.get(goal_key, MEAL_SUGGESTIONS["maintenance"])
    return {
        **user_goal,
        "meal_suggestions": suggestion["suggestions"],
        "goal_label": suggestion["goal_label"],
    }


@app.put("/goal")
def update_goal(goal_update: GoalUpdate) -> dict:
    user_goal["goal"] = goal_update.goal
    user_goal["daily_target"] = goal_update.daily_target
    return {"ok": True, **user_goal}


@app.get("/suggestions")
def get_suggestions(goal: str = "maintenance") -> dict:
    suggestion = MEAL_SUGGESTIONS.get(goal, MEAL_SUGGESTIONS["maintenance"])
    return {
        "goal": goal,
        "goal_label": suggestion["goal_label"],
        "daily_target": suggestion["daily_target"],
        "suggestions": suggestion["suggestions"],
    }


@app.get("/dashboard")
def get_dashboard() -> dict:
    today_calories = sum(entry.get("calories", 0) for entry in meal_log)
    return {
        "today": {
            "calories": round(today_calories, 1),
            "target": user_goal["daily_target"],
            "protein": round(sum(entry.get("protein", 0) for entry in meal_log), 1),
            "carbs": round(sum(entry.get("carbs", 0) for entry in meal_log), 1),
            "fat": round(sum(entry.get("fat", 0) for entry in meal_log), 1),
            "meals": len(meal_log),
        },
        "weekly": [
            {"day": "Mon", "calories": 1820, "target": 2000},
            {"day": "Tue", "calories": 2150, "target": 2000},
            {"day": "Wed", "calories": 1760, "target": 2000},
            {"day": "Thu", "calories": 2340, "target": 2000},
            {"day": "Fri", "calories": 1980, "target": 2000},
            {"day": "Sat", "calories": 2600, "target": 2000},
            {"day": "Sun", "calories": today_calories or 1540, "target": 2000},
        ],
        "macro_split": [
            {"name": "Protein", "value": 25, "color": "#4ade80"},
            {"name": "Carbs", "value": 50, "color": "#60a5fa"},
            {"name": "Fat", "value": 25, "color": "#f59e0b"},
        ],
        "streak_days": 7,
        "total_scans": len(meal_log) + 42,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
