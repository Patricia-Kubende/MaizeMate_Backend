import os
from fastapi import FastAPI, Depends
import pickle
import pandas as pd
import uvicorn
from sqlalchemy.orm import Session
from database import SessionLocal, Prediction, User, get_db
from schemas import UserCreate, UserLogin, Token
from auth import hash_password, verify_password, create_access_token
app = FastAPI()

# Load the trained model once at startup
with open("final_model.pkl", "rb") as file:
    model = pickle.load(file)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "Welcome to the Maize Yield Prediction API!"}

@app.post("/predict/")
def predict_yield(data: dict, db: Session = Depends(get_db)):
    try:
        # Convert input data to DataFrame
        df = pd.DataFrame([data])
        df = pd.get_dummies(df)

        # Ensure all missing features are added with value 0
        for feature in model.feature_names_in_:
            if feature not in df.columns:
                df[feature] = 0

        # Reorder columns to match the model
        df = df[model.feature_names_in_]

        # Make prediction
        predicted_yield = model.predict(df)[0]

        # Confidence range (±10%)
        lower_bound = round(predicted_yield * 0.9, 2)
        upper_bound = round(predicted_yield * 1.1, 2)

        # Yield category
        if predicted_yield > 30:
            category = "High Yield"
            recommendation = "✅ Maintain current farming practices."
        elif predicted_yield > 20:
            category = "Moderate Yield"
            recommendation = "⚠️ Consider improving soil quality and irrigation."
        else:
            category = "Low Yield"
            recommendation = "❌ Apply more fertilizer and optimize planting date."
         # **🔍 Dynamic Recommendations Based on Input**
        if data.get("Soil_Type") in ["Sandy", "Silt"]:
            recommendation += " 🌱 Sandy/Silt soil may require more organic matter for better water retention."

        if data.get("pH", 7.0) < 5.5:  # Default to neutral pH if missing
            recommendation += " 🔬 The soil is too acidic! Consider adding lime to increase pH."

        if data.get("Rainfall_mm", 0) < 400:
            recommendation += " ☔️ Rainfall is low! Implement irrigation techniques for better results."

        if data.get("Humidity_%", 100) < 40:
            recommendation += " 💦 Low humidity detected! Monitor moisture levels to prevent crop stress."

        if data.get("Fertilizer_Type") == "Organic":
            recommendation += " 🌿 Organic fertilizer is good for sustainability but may take longer to release nutrients."

        if data.get("Planting_Date") == "March":
            recommendation += " 📅 Early planting may expose crops to dry conditions. Monitor weather patterns."
        # Store prediction in the database
        db_prediction = Prediction(
            Soil_Type=data["Soil_Type"],
            pH=data["pH"],
            Seed_Variety=data["Seed_Variety"],
            Rainfall_mm=data["Rainfall_mm"],
            Temperature_C=data["Temperature_C"],
            Humidity_percent=data["Humidity_%"],
            Planting_Date=data["Planting_Date"],
            Fertilizer_Type=data["Fertilizer_Type"],
            Predicted_Yield=predicted_yield,
            Confidence_Range=f"{lower_bound} - {upper_bound} bags per acre",
            Category=category,
            Recommendation=recommendation
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)

        return {
            "predicted_yield": round(predicted_yield, 2),
            "confidence_range": f"{lower_bound} - {upper_bound} bags per acre",
            "category": category,
            "recommendation": recommendation,
            "input_summary": data
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
