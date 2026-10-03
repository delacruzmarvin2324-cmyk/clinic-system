import pickle
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


MODEL_PATH = Path(__file__).resolve().parent.parent / "appointment_model.pkl"


def _load_model() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "The trained appointment model was not found. Run python train_appointment_model.py first."
        )

    with open(MODEL_PATH, "rb") as handle:
        payload = pickle.load(handle)

    if isinstance(payload, dict) and "model" in payload and "columns" in payload:
        return payload

    raise ValueError("The saved model file is not in the expected format.")


def predict_no_show_risk_from_profile(
    age: int,
    gender: str,
    neighbourhood: str,
    scholarship: bool,
    hypertension: bool,
    diabetes: bool,
    alcoholism: bool,
    handicap: int,
    sms_received: bool,
    appointment_date: date,
) -> float:
    payload = _load_model()
    model = payload["model"]
    feature_columns = payload["columns"]

    scheduled_date = date.today()
    waiting_days = max(0, (appointment_date - scheduled_date).days)

    gender_value = 0
    if isinstance(gender, str):
        gender_value = {"F": 0, "M": 1}.get(str(gender).strip().upper(), 0)
    elif isinstance(gender, (int, float)):
        gender_value = int(gender)

    row = pd.DataFrame([
        {
            "Age": int(age),
            "Gender": gender_value,
            "Scholarship": bool(scholarship),
            "Hipertension": bool(hypertension),
            "Diabetes": bool(diabetes),
            "Alcoholism": bool(alcoholism),
            "Handcap": int(handicap),
            "SMS_received": bool(sms_received),
            "WaitingDays": waiting_days,
            "Neighbourhood": str(neighbourhood),
        }
    ])

    encoded = pd.get_dummies(row, columns=["Neighbourhood"], drop_first=True)
    for column in feature_columns:
        if column not in encoded.columns:
            encoded[column] = 0

    encoded = encoded[feature_columns]
    probabilities = model.predict_proba(encoded)[0]
    return float(probabilities[1])


def predict_no_show_risk(
    age: int,
    gender: str,
    neighbourhood: str,
    scholarship: bool,
    hypertension: bool,
    diabetes: bool,
    alcoholism: bool,
    handicap: int,
    sms_received: bool,
    appointment_date: date,
) -> float:
    return predict_no_show_risk_from_profile(
        age=age,
        gender=gender,
        neighbourhood=neighbourhood,
        scholarship=scholarship,
        hypertension=hypertension,
        diabetes=diabetes,
        alcoholism=alcoholism,
        handicap=handicap,
        sms_received=sms_received,
        appointment_date=appointment_date,
    )


def get_risk_level(probability: float) -> str:
    if probability >= 0.8:
        return "High risk"
    if probability >= 0.55:
        return "Medium risk"
    return "Low risk"
