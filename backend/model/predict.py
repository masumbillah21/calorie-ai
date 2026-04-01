"""
CalorieAI - Food Prediction Engine + Nutrition Database
Covers all 101 Food-101 classes with macros per 100g serving
"""

import numpy as np
import json
import tensorflow as tf
from tensorflow.keras.preprocessing import image as keras_image
from PIL import Image
import io

# ─────────────────────────────────────────────────────────────────────────────
# NUTRITION DATABASE  (per 100g unless noted)
# Keys match Food-101 class folder names
# ─────────────────────────────────────────────────────────────────────────────
NUTRITION_DB = {
    "apple_pie":           {"name":"Apple Pie",           "calories":237,"protein":2.0,"carbs":34.0,"fat":11.0,"fiber":1.5,"sugar":14.0,"serving_g":125,"category":"Dessert"},
    "baby_back_ribs":      {"name":"Baby Back Ribs",      "calories":292,"protein":24.0,"carbs":2.0,"fat":21.0,"fiber":0.0,"sugar":1.0,"serving_g":200,"category":"Meat"},
    "baklava":             {"name":"Baklava",             "calories":428,"protein":5.6,"carbs":52.0,"fat":23.0,"fiber":1.8,"sugar":28.0,"serving_g":80,"category":"Dessert"},
    "beef_carpaccio":      {"name":"Beef Carpaccio",      "calories":163,"protein":18.0,"carbs":0.5,"fat":9.5,"fiber":0.0,"sugar":0.0,"serving_g":100,"category":"Meat"},
    "beef_tartare":        {"name":"Beef Tartare",        "calories":196,"protein":20.0,"carbs":1.0,"fat":12.0,"fiber":0.0,"sugar":0.0,"serving_g":150,"category":"Meat"},
    "beet_salad":          {"name":"Beet Salad",          "calories":74,"protein":2.5,"carbs":12.0,"fat":2.0,"fiber":3.0,"sugar":8.0,"serving_g":200,"category":"Salad"},
    "beignets":            {"name":"Beignets",            "calories":389,"protein":5.5,"carbs":48.0,"fat":20.0,"fiber":1.2,"sugar":14.0,"serving_g":80,"category":"Dessert"},
    "bibimbap":            {"name":"Bibimbap",            "calories":490,"protein":26.0,"carbs":70.0,"fat":12.0,"fiber":4.0,"sugar":5.0,"serving_g":400,"category":"Asian"},
    "bread_pudding":       {"name":"Bread Pudding",       "calories":244,"protein":6.5,"carbs":35.0,"fat":9.0,"fiber":0.8,"sugar":16.0,"serving_g":150,"category":"Dessert"},
    "breakfast_burrito":   {"name":"Breakfast Burrito",   "calories":309,"protein":14.0,"carbs":30.0,"fat":15.0,"fiber":2.5,"sugar":2.0,"serving_g":250,"category":"Mexican"},
    "bruschetta":          {"name":"Bruschetta",          "calories":196,"protein":5.5,"carbs":27.0,"fat":7.5,"fiber":2.0,"sugar":3.0,"serving_g":100,"category":"Appetizer"},
    "caesar_salad":        {"name":"Caesar Salad",        "calories":184,"protein":7.0,"carbs":8.0,"fat":14.0,"fiber":2.0,"sugar":1.5,"serving_g":200,"category":"Salad"},
    "cannoli":             {"name":"Cannoli",             "calories":327,"protein":8.0,"carbs":32.0,"fat":19.0,"fiber":0.5,"sugar":16.0,"serving_g":100,"category":"Dessert"},
    "caprese_salad":       {"name":"Caprese Salad",       "calories":145,"protein":9.0,"carbs":5.0,"fat":10.0,"fiber":1.0,"sugar":4.0,"serving_g":200,"category":"Salad"},
    "carrot_cake":         {"name":"Carrot Cake",         "calories":415,"protein":4.5,"carbs":55.0,"fat":21.0,"fiber":1.5,"sugar":36.0,"serving_g":100,"category":"Dessert"},
    "ceviche":             {"name":"Ceviche",             "calories":110,"protein":18.0,"carbs":6.0,"fat":2.0,"fiber":1.0,"sugar":3.0,"serving_g":150,"category":"Seafood"},
    "cheesecake":          {"name":"Cheesecake",          "calories":321,"protein":5.5,"carbs":25.0,"fat":22.0,"fiber":0.4,"sugar":20.0,"serving_g":125,"category":"Dessert"},
    "cheese_plate":        {"name":"Cheese Plate",        "calories":386,"protein":22.0,"carbs":2.0,"fat":32.0,"fiber":0.0,"sugar":0.5,"serving_g":80,"category":"Dairy"},
    "chicken_curry":       {"name":"Chicken Curry",       "calories":238,"protein":22.0,"carbs":10.0,"fat":12.0,"fiber":2.5,"sugar":4.0,"serving_g":300,"category":"Asian"},
    "chicken_quesadilla":  {"name":"Chicken Quesadilla",  "calories":340,"protein":22.0,"carbs":30.0,"fat":15.0,"fiber":2.0,"sugar":2.0,"serving_g":200,"category":"Mexican"},
    "chicken_wings":       {"name":"Chicken Wings",       "calories":290,"protein":27.0,"carbs":3.0,"fat":19.0,"fiber":0.0,"sugar":1.0,"serving_g":150,"category":"Meat"},
    "chocolate_cake":      {"name":"Chocolate Cake",      "calories":371,"protein":5.0,"carbs":51.0,"fat":18.0,"fiber":2.5,"sugar":32.0,"serving_g":100,"category":"Dessert"},
    "chocolate_mousse":    {"name":"Chocolate Mousse",    "calories":254,"protein":5.0,"carbs":26.0,"fat":15.0,"fiber":1.5,"sugar":22.0,"serving_g":100,"category":"Dessert"},
    "churros":             {"name":"Churros",             "calories":372,"protein":4.5,"carbs":50.0,"fat":18.0,"fiber":1.5,"sugar":12.0,"serving_g":100,"category":"Dessert"},
    "clam_chowder":        {"name":"Clam Chowder",        "calories":164,"protein":8.0,"carbs":16.0,"fat":8.0,"fiber":1.0,"sugar":3.0,"serving_g":240,"category":"Soup"},
    "club_sandwich":       {"name":"Club Sandwich",       "calories":445,"protein":30.0,"carbs":36.0,"fat":20.0,"fiber":2.5,"sugar":4.0,"serving_g":250,"category":"Sandwich"},
    "crab_cakes":          {"name":"Crab Cakes",          "calories":188,"protein":16.0,"carbs":12.0,"fat":8.0,"fiber":0.5,"sugar":1.5,"serving_g":150,"category":"Seafood"},
    "creme_brulee":        {"name":"Crème Brûlée",        "calories":297,"protein":4.5,"carbs":26.0,"fat":20.0,"fiber":0.0,"sugar":22.0,"serving_g":120,"category":"Dessert"},
    "croque_madame":       {"name":"Croque Madame",       "calories":418,"protein":24.0,"carbs":28.0,"fat":23.0,"fiber":1.5,"sugar":3.0,"serving_g":200,"category":"Sandwich"},
    "cup_cakes":           {"name":"Cupcakes",            "calories":375,"protein":4.0,"carbs":52.0,"fat":17.0,"fiber":0.8,"sugar":35.0,"serving_g":80,"category":"Dessert"},
    "deviled_eggs":        {"name":"Deviled Eggs",        "calories":192,"protein":10.0,"carbs":2.0,"fat":16.0,"fiber":0.0,"sugar":1.0,"serving_g":100,"category":"Appetizer"},
    "donuts":              {"name":"Donuts",              "calories":452,"protein":5.0,"carbs":51.0,"fat":25.0,"fiber":1.5,"sugar":20.0,"serving_g":75,"category":"Dessert"},
    "dumplings":           {"name":"Dumplings",           "calories":332,"protein":12.0,"carbs":40.0,"fat":14.0,"fiber":2.0,"sugar":2.0,"serving_g":150,"category":"Asian"},
    "edamame":             {"name":"Edamame",             "calories":121,"protein":11.0,"carbs":9.0,"fat":5.0,"fiber":5.0,"sugar":2.0,"serving_g":155,"category":"Vegetarian"},
    "eggs_benedict":       {"name":"Eggs Benedict",       "calories":346,"protein":18.0,"carbs":20.0,"fat":22.0,"fiber":1.0,"sugar":2.0,"serving_g":200,"category":"Breakfast"},
    "escargots":           {"name":"Escargots",           "calories":208,"protein":16.0,"carbs":2.0,"fat":15.0,"fiber":0.0,"sugar":0.0,"serving_g":100,"category":"Seafood"},
    "falafel":             {"name":"Falafel",             "calories":333,"protein":13.0,"carbs":32.0,"fat":18.0,"fiber":5.0,"sugar":3.0,"serving_g":100,"category":"Vegetarian"},
    "filet_mignon":        {"name":"Filet Mignon",        "calories":252,"protein":30.0,"carbs":0.0,"fat":14.0,"fiber":0.0,"sugar":0.0,"serving_g":200,"category":"Meat"},
    "fish_and_chips":      {"name":"Fish and Chips",      "calories":376,"protein":18.0,"carbs":38.0,"fat":17.0,"fiber":3.0,"sugar":1.5,"serving_g":350,"category":"Seafood"},
    "foie_gras":           {"name":"Foie Gras",           "calories":462,"protein":11.0,"carbs":4.5,"fat":44.0,"fiber":0.0,"sugar":0.0,"serving_g":80,"category":"Meat"},
    "french_fries":        {"name":"French Fries",        "calories":312,"protein":3.5,"carbs":41.0,"fat":15.0,"fiber":3.5,"sugar":0.5,"serving_g":150,"category":"Snack"},
    "french_onion_soup":   {"name":"French Onion Soup",   "calories":156,"protein":8.5,"carbs":15.0,"fat":7.0,"fiber":1.5,"sugar":6.0,"serving_g":300,"category":"Soup"},
    "french_toast":        {"name":"French Toast",        "calories":229,"protein":8.0,"carbs":28.0,"fat":9.5,"fiber":1.0,"sugar":8.0,"serving_g":150,"category":"Breakfast"},
    "fried_calamari":      {"name":"Fried Calamari",      "calories":175,"protein":18.0,"carbs":8.0,"fat":8.0,"fiber":0.3,"sugar":0.5,"serving_g":150,"category":"Seafood"},
    "fried_rice":          {"name":"Fried Rice",          "calories":163,"protein":4.5,"carbs":25.0,"fat":5.0,"fiber":1.0,"sugar":1.5,"serving_g":250,"category":"Asian"},
    "frozen_yogurt":       {"name":"Frozen Yogurt",       "calories":159,"protein":3.8,"carbs":28.0,"fat":3.5,"fiber":0.0,"sugar":24.0,"serving_g":150,"category":"Dessert"},
    "garlic_bread":        {"name":"Garlic Bread",        "calories":274,"protein":6.5,"carbs":32.0,"fat":14.0,"fiber":1.5,"sugar":1.5,"serving_g":100,"category":"Bread"},
    "gnocchi":             {"name":"Gnocchi",             "calories":155,"protein":4.0,"carbs":27.0,"fat":3.5,"fiber":1.8,"sugar":1.0,"serving_g":200,"category":"Italian"},
    "greek_salad":         {"name":"Greek Salad",         "calories":134,"protein":4.0,"carbs":8.0,"fat":9.5,"fiber":2.5,"sugar":5.0,"serving_g":250,"category":"Salad"},
    "grilled_cheese_sandwich": {"name":"Grilled Cheese", "calories":391,"protein":17.0,"carbs":32.0,"fat":22.0,"fiber":1.5,"sugar":4.0,"serving_g":150,"category":"Sandwich"},
    "grilled_salmon":      {"name":"Grilled Salmon",      "calories":208,"protein":28.0,"carbs":0.0,"fat":10.0,"fiber":0.0,"sugar":0.0,"serving_g":200,"category":"Seafood"},
    "guacamole":           {"name":"Guacamole",           "calories":155,"protein":2.0,"carbs":9.0,"fat":14.0,"fiber":6.5,"sugar":1.0,"serving_g":100,"category":"Mexican"},
    "gyoza":               {"name":"Gyoza",               "calories":255,"protein":11.0,"carbs":30.0,"fat":10.0,"fiber":2.0,"sugar":2.0,"serving_g":150,"category":"Asian"},
    "hamburger":           {"name":"Hamburger",           "calories":540,"protein":34.0,"carbs":42.0,"fat":26.0,"fiber":2.5,"sugar":8.0,"serving_g":280,"category":"Fast Food"},
    "hot_and_sour_soup":   {"name":"Hot & Sour Soup",     "calories":80,"protein":5.0,"carbs":10.0,"fat":2.5,"fiber":1.0,"sugar":3.0,"serving_g":300,"category":"Soup"},
    "hot_dog":             {"name":"Hot Dog",             "calories":346,"protein":14.0,"carbs":26.0,"fat":21.0,"fiber":1.0,"sugar":4.0,"serving_g":150,"category":"Fast Food"},
    "huevos_rancheros":    {"name":"Huevos Rancheros",    "calories":295,"protein":16.0,"carbs":26.0,"fat":14.0,"fiber":4.0,"sugar":4.0,"serving_g":250,"category":"Mexican"},
    "hummus":              {"name":"Hummus",              "calories":177,"protein":8.0,"carbs":20.0,"fat":8.5,"fiber":6.0,"sugar":2.0,"serving_g":100,"category":"Vegetarian"},
    "ice_cream":           {"name":"Ice Cream",           "calories":207,"protein":3.5,"carbs":24.0,"fat":11.0,"fiber":0.6,"sugar":21.0,"serving_g":130,"category":"Dessert"},
    "lasagna":             {"name":"Lasagna",             "calories":166,"protein":11.0,"carbs":16.0,"fat":6.5,"fiber":1.5,"sugar":3.0,"serving_g":250,"category":"Italian"},
    "lobster_bisque":      {"name":"Lobster Bisque",      "calories":215,"protein":9.0,"carbs":12.0,"fat":16.0,"fiber":0.5,"sugar":4.0,"serving_g":240,"category":"Soup"},
    "lobster_roll_sandwich":{"name":"Lobster Roll",       "calories":436,"protein":26.0,"carbs":38.0,"fat":20.0,"fiber":1.5,"sugar":3.0,"serving_g":200,"category":"Seafood"},
    "macaroni_and_cheese": {"name":"Mac and Cheese",      "calories":358,"protein":14.0,"carbs":40.0,"fat":16.0,"fiber":1.5,"sugar":4.0,"serving_g":250,"category":"American"},
    "macarons":            {"name":"Macarons",            "calories":449,"protein":6.0,"carbs":60.0,"fat":21.0,"fiber":1.0,"sugar":50.0,"serving_g":60,"category":"Dessert"},
    "miso_soup":           {"name":"Miso Soup",           "calories":40,"protein":3.0,"carbs":5.0,"fat":1.0,"fiber":1.0,"sugar":1.5,"serving_g":250,"category":"Soup"},
    "mussels":             {"name":"Mussels",             "calories":172,"protein":24.0,"carbs":7.0,"fat":4.5,"fiber":0.0,"sugar":0.0,"serving_g":200,"category":"Seafood"},
    "nachos":              {"name":"Nachos",              "calories":505,"protein":16.0,"carbs":52.0,"fat":28.0,"fiber":5.0,"sugar":3.0,"serving_g":200,"category":"Mexican"},
    "omelette":            {"name":"Omelette",            "calories":187,"protein":14.0,"carbs":1.5,"fat":14.0,"fiber":0.0,"sugar":1.0,"serving_g":150,"category":"Breakfast"},
    "onion_rings":         {"name":"Onion Rings",         "calories":277,"protein":3.7,"carbs":31.0,"fat":16.0,"fiber":1.5,"sugar":3.0,"serving_g":120,"category":"Snack"},
    "oysters":             {"name":"Oysters",             "calories":68,"protein":7.0,"carbs":3.9,"fat":2.5,"fiber":0.0,"sugar":0.0,"serving_g":85,"category":"Seafood"},
    "pad_thai":            {"name":"Pad Thai",            "calories":380,"protein":20.0,"carbs":50.0,"fat":12.0,"fiber":3.0,"sugar":8.0,"serving_g":300,"category":"Asian"},
    "paella":              {"name":"Paella",              "calories":199,"protein":15.0,"carbs":22.0,"fat":6.0,"fiber":1.5,"sugar":2.0,"serving_g":350,"category":"Spanish"},
    "pancakes":            {"name":"Pancakes",            "calories":227,"protein":6.0,"carbs":35.0,"fat":8.0,"fiber":1.0,"sugar":8.0,"serving_g":150,"category":"Breakfast"},
    "panna_cotta":         {"name":"Panna Cotta",         "calories":220,"protein":3.5,"carbs":22.0,"fat":13.0,"fiber":0.0,"sugar":18.0,"serving_g":120,"category":"Dessert"},
    "peking_duck":         {"name":"Peking Duck",         "calories":337,"protein":20.0,"carbs":6.0,"fat":26.0,"fiber":0.0,"sugar":5.0,"serving_g":200,"category":"Asian"},
    "pho":                 {"name":"Pho",                 "calories":215,"protein":17.0,"carbs":25.0,"fat":4.5,"fiber":1.5,"sugar":3.0,"serving_g":450,"category":"Asian"},
    "pizza":               {"name":"Pizza",               "calories":266,"protein":11.0,"carbs":33.0,"fat":10.0,"fiber":2.3,"sugar":4.0,"serving_g":200,"category":"Italian"},
    "pork_chop":           {"name":"Pork Chop",           "calories":231,"protein":28.0,"carbs":0.0,"fat":13.0,"fiber":0.0,"sugar":0.0,"serving_g":200,"category":"Meat"},
    "poutine":             {"name":"Poutine",             "calories":497,"protein":15.0,"carbs":48.0,"fat":28.0,"fiber":3.5,"sugar":2.0,"serving_g":300,"category":"Canadian"},
    "prime_rib":           {"name":"Prime Rib",           "calories":341,"protein":28.0,"carbs":0.0,"fat":25.0,"fiber":0.0,"sugar":0.0,"serving_g":250,"category":"Meat"},
    "pulled_pork_sandwich":{"name":"Pulled Pork Sandwich","calories":521,"protein":32.0,"carbs":44.0,"fat":23.0,"fiber":2.0,"sugar":12.0,"serving_g":280,"category":"Sandwich"},
    "ramen":               {"name":"Ramen",               "calories":436,"protein":22.0,"carbs":52.0,"fat":14.0,"fiber":2.5,"sugar":4.0,"serving_g":480,"category":"Asian"},
    "ravioli":             {"name":"Ravioli",             "calories":220,"protein":10.0,"carbs":30.0,"fat":7.0,"fiber":2.0,"sugar":2.0,"serving_g":250,"category":"Italian"},
    "red_velvet_cake":     {"name":"Red Velvet Cake",     "calories":415,"protein":5.0,"carbs":57.0,"fat":20.0,"fiber":1.0,"sugar":40.0,"serving_g":100,"category":"Dessert"},
    "risotto":             {"name":"Risotto",             "calories":174,"protein":5.5,"carbs":28.0,"fat":4.5,"fiber":1.0,"sugar":1.5,"serving_g":300,"category":"Italian"},
    "samosa":              {"name":"Samosa",              "calories":262,"protein":5.0,"carbs":30.0,"fat":14.0,"fiber":3.0,"sugar":2.0,"serving_g":100,"category":"Indian"},
    "sashimi":             {"name":"Sashimi",             "calories":130,"protein":22.0,"carbs":0.0,"fat":4.5,"fiber":0.0,"sugar":0.0,"serving_g":150,"category":"Japanese"},
    "scallops":            {"name":"Scallops",            "calories":111,"protein":20.0,"carbs":5.0,"fat":1.0,"fiber":0.0,"sugar":0.0,"serving_g":150,"category":"Seafood"},
    "seaweed_salad":       {"name":"Seaweed Salad",       "calories":45,"protein":1.5,"carbs":7.0,"fat":1.0,"fiber":2.5,"sugar":4.0,"serving_g":100,"category":"Japanese"},
    "shrimp_and_grits":    {"name":"Shrimp and Grits",    "calories":350,"protein":22.0,"carbs":38.0,"fat":12.0,"fiber":2.0,"sugar":2.5,"serving_g":300,"category":"American"},
    "spaghetti_bolognese": {"name":"Spaghetti Bolognese", "calories":348,"protein":22.0,"carbs":40.0,"fat":11.0,"fiber":3.0,"sugar":5.0,"serving_g":350,"category":"Italian"},
    "spaghetti_carbonara": {"name":"Spaghetti Carbonara", "calories":421,"protein":20.0,"carbs":43.0,"fat":19.0,"fiber":2.0,"sugar":2.0,"serving_g":300,"category":"Italian"},
    "spring_rolls":        {"name":"Spring Rolls",        "calories":165,"protein":5.5,"carbs":22.0,"fat":7.0,"fiber":2.0,"sugar":2.0,"serving_g":100,"category":"Asian"},
    "steak":               {"name":"Steak",               "calories":271,"protein":26.0,"carbs":0.0,"fat":18.0,"fiber":0.0,"sugar":0.0,"serving_g":200,"category":"Meat"},
    "strawberry_shortcake":{"name":"Strawberry Shortcake","calories":326,"protein":5.0,"carbs":46.0,"fat":14.0,"fiber":1.5,"sugar":22.0,"serving_g":150,"category":"Dessert"},
    "sushi":               {"name":"Sushi",               "calories":200,"protein":10.0,"carbs":30.0,"fat":4.0,"fiber":1.5,"sugar":4.0,"serving_g":150,"category":"Japanese"},
    "tacos":               {"name":"Tacos",               "calories":368,"protein":19.0,"carbs":30.0,"fat":19.0,"fiber":4.0,"sugar":3.0,"serving_g":200,"category":"Mexican"},
    "takoyaki":            {"name":"Takoyaki",            "calories":272,"protein":11.0,"carbs":30.0,"fat":12.0,"fiber":1.0,"sugar":3.0,"serving_g":150,"category":"Japanese"},
    "tiramisu":            {"name":"Tiramisu",            "calories":295,"protein":6.0,"carbs":28.0,"fat":17.0,"fiber":0.5,"sugar":20.0,"serving_g":150,"category":"Dessert"},
    "tuna_tartare":        {"name":"Tuna Tartare",        "calories":135,"protein":22.0,"carbs":2.5,"fat":4.0,"fiber":0.5,"sugar":1.0,"serving_g":150,"category":"Seafood"},
    "waffles":             {"name":"Waffles",             "calories":291,"protein":7.5,"carbs":37.0,"fat":13.0,"fiber":1.5,"sugar":8.0,"serving_g":150,"category":"Breakfast"},
}

# ─────────────────────────────────────────
# MEAL SUGGESTIONS BY GOAL
# ─────────────────────────────────────────
MEAL_SUGGESTIONS = {
    "weight_loss": {
        "goal_label": "Weight Loss",
        "daily_target": 1500,
        "suggestions": [
            {"name":"Greek Salad","calories":134,"reason":"Low calorie, high in vitamins"},
            {"name":"Grilled Salmon","calories":208,"reason":"High protein, omega-3 rich"},
            {"name":"Miso Soup","calories":40,"reason":"Very low calorie, filling"},
            {"name":"Edamame","calories":121,"reason":"High protein plant snack"},
            {"name":"Sashimi","calories":130,"reason":"Lean protein, zero carbs"},
            {"name":"Seaweed Salad","calories":45,"reason":"Nutrient dense, very low cal"},
        ]
    },
    "muscle_gain": {
        "goal_label": "Muscle Gain",
        "daily_target": 2800,
        "suggestions": [
            {"name":"Steak","calories":271,"reason":"Complete protein, iron rich"},
            {"name":"Grilled Salmon","calories":208,"reason":"Protein + healthy fats"},
            {"name":"Eggs Benedict","calories":346,"reason":"High protein breakfast"},
            {"name":"Shrimp and Grits","calories":350,"reason":"Protein + complex carbs"},
            {"name":"Bibimbap","calories":490,"reason":"Balanced macros, high protein"},
            {"name":"Chicken Wings","calories":290,"reason":"High protein snack"},
        ]
    },
    "maintenance": {
        "goal_label": "Maintenance",
        "daily_target": 2000,
        "suggestions": [
            {"name":"Sushi","calories":200,"reason":"Balanced macros"},
            {"name":"Caesar Salad","calories":184,"reason":"Moderate calories, satisfying"},
            {"name":"Pad Thai","calories":380,"reason":"Balanced meal with variety"},
            {"name":"Omelette","calories":187,"reason":"Versatile, protein rich"},
            {"name":"Ramen","calories":436,"reason":"Warming, balanced bowl"},
            {"name":"Pancakes","calories":227,"reason":"Enjoyable, moderate energy"},
        ]
    },
    "keto": {
        "goal_label": "Keto / Low Carb",
        "daily_target": 1800,
        "suggestions": [
            {"name":"Steak","calories":271,"reason":"Zero carb, high fat + protein"},
            {"name":"Sashimi","calories":130,"reason":"Zero carb, pure protein"},
            {"name":"Beef Carpaccio","calories":163,"reason":"Very low carb"},
            {"name":"Omelette","calories":187,"reason":"Zero carb, high fat"},
            {"name":"Cheese Plate","calories":386,"reason":"High fat, very low carb"},
            {"name":"Guacamole","calories":155,"reason":"Healthy fats, low net carb"},
        ]
    }
}


# ─────────────────────────────────────────
# PREDICTOR CLASS
# ─────────────────────────────────────────
class FoodPredictor:
    def __init__(self, model_path: str, class_names_path: str):
        print("🔄 Loading food recognition model...")
        self.model = tf.keras.models.load_model(model_path)
        with open(class_names_path, 'r') as f:
            self.class_names = json.load(f)
        print(f"✅ Model loaded | {len(self.class_names)} food classes")

    def predict(self, img_bytes: bytes, portion_g: float = None):
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((224, 224))
        arr = np.array(img, dtype=np.float32) / 255.0
        arr = np.expand_dims(arr, 0)

        preds = self.model.predict(arr, verbose=0)[0]
        top5_idx = np.argsort(preds)[-5:][::-1]
        top5 = [{"class": self.class_names[str(i)], "confidence": float(preds[i])} for i in top5_idx]

        best_class = top5[0]["class"]
        confidence = float(preds[top5_idx[0]])
        nutrition = NUTRITION_DB.get(best_class)

        if nutrition is None:
            nutrition = {"name": best_class.replace("_", " ").title(),
                        "calories":250,"protein":10,"carbs":30,"fat":10,
                        "fiber":2,"sugar":5,"serving_g":150,"category":"Other"}

        serving = portion_g if portion_g else nutrition["serving_g"]
        scale = serving / 100.0

        return {
            "food_class": best_class,
            "food_name": nutrition["name"],
            "category": nutrition["category"],
            "confidence": round(confidence * 100, 1),
            "serving_g": serving,
            "per_100g": {
                "calories": nutrition["calories"],
                "protein":  nutrition["protein"],
                "carbs":    nutrition["carbs"],
                "fat":      nutrition["fat"],
                "fiber":    nutrition["fiber"],
                "sugar":    nutrition["sugar"],
            },
            "totals": {
                "calories": round(nutrition["calories"] * scale, 1),
                "protein":  round(nutrition["protein"]  * scale, 1),
                "carbs":    round(nutrition["carbs"]    * scale, 1),
                "fat":      round(nutrition["fat"]      * scale, 1),
                "fiber":    round(nutrition["fiber"]    * scale, 1),
                "sugar":    round(nutrition["sugar"]    * scale, 1),
            },
            "top5": top5
        }
