import os
import pickle
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import uvicorn

from database import SessionLocal, User, Prediction, get_db
from auth import hash_password, verify_password, create_access_token
from schemas import UserCreate, UserLogin, PredictionInput, Token

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to Maize Yield Prediction API"}


# Load trained model
with open("final_model.pkl", "rb") as f:
    model = pickle.load(f)


@app.post("/signup/")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pw = hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "✅ Signup successful! You can now log in."}

@app.post("/login/", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if not existing_user or not verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# Dependency to extract current user from JWT token
def get_current_username(authorization: str = Header(...)) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth schema")
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY", "your_secret_key_here"), algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token missing subject")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.post("/predict/")
def predict_yield(data: PredictionInput, username: str = Depends(get_current_username)):
    df = pd.DataFrame([data.dict()])
    df = pd.get_dummies(df)

    for col in model.feature_names_in_:
        if col not in df.columns:
            df[col] = 0

    df = df[model.feature_names_in_]
    pred = model.predict(df)[0]

    return {
        "predicted_yield": round(pred, 2),
        "input_summary": data.dict()
    }
