import os
import pickle
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


def find_dataset():
    candidates = [
        Path.cwd() / "healthcare_noshows_appt.csv",
        Path.home() / "Downloads" / "healthcare_noshows_appt.csv",
        Path(r"C:\Users\Meros\Downloads\healthcare_noshows_appt.csv"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Could not find healthcare_noshows_appt.csv. Place it in the project folder or update the path."
    )


csv_path = find_dataset()
print(f"Using dataset: {csv_path}")

df = pd.read_csv(csv_path)

# Clean and prepare columns
if "ScheduledDay" in df.columns:
    df["ScheduledDay"] = pd.to_datetime(df["ScheduledDay"], errors="coerce")
if "AppointmentDay" in df.columns:
    df["AppointmentDay"] = pd.to_datetime(df["AppointmentDay"], errors="coerce")

if "ScheduledDay" in df.columns and "AppointmentDay" in df.columns:
    df["WaitingDays"] = (df["AppointmentDay"] - df["ScheduledDay"]).dt.days.abs()
else:
    df["WaitingDays"] = 0

# Create target: No-show = 1 when patient did not show
if "Showed_up" in df.columns:
    showed_up = df["Showed_up"].astype(str).str.strip().str.lower()
    df["No-show"] = showed_up.map({"true": 0, "false": 1, "yes": 0, "no": 1, "t": 0, "f": 1})
    df["No-show"] = df["No-show"].fillna(1)
else:
    raise KeyError("Column 'Showed_up' was not found in the dataset.")

# Encode gender
if "Gender" in df.columns:
    df["Gender"] = df["Gender"].astype(str).str.upper().map({"F": 0, "M": 1})
    df["Gender"] = df["Gender"].fillna(0)

# Drop unused columns
columns_to_drop = [c for c in ["PatientId", "AppointmentID", "ScheduledDay", "AppointmentDay"] if c in df.columns]
df = df.drop(columns=columns_to_drop)

# Remove rows with missing target values
df = df.dropna(subset=["No-show"])

X = df.drop(columns=["No-show"])
y = df["No-show"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# One-hot encode neighborhood
if "Neighbourhood" in X_train.columns:
    X_train_encoded = pd.get_dummies(X_train, columns=["Neighbourhood"], drop_first=True)
    X_test_encoded = pd.get_dummies(X_test, columns=["Neighbourhood"], drop_first=True)

    # Align columns between train and test sets
    missing_cols = set(X_train_encoded.columns) - set(X_test_encoded.columns)
    for col in missing_cols:
        X_test_encoded[col] = 0
    X_test_encoded = X_test_encoded[X_train_encoded.columns]
else:
    X_train_encoded = X_train
    X_test_encoded = X_test

model = RandomForestClassifier(random_state=42, n_estimators=200)
model.fit(X_train_encoded, y_train)

predictions = model.predict(X_test_encoded)

print("Classification Report:")
print(classification_report(y_test, predictions))
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))

accuracy = accuracy_score(y_test, predictions)
print("Accuracy:", accuracy)

model_path = Path.cwd() / "appointment_model.pkl"
with open(model_path, "wb") as file:
    pickle.dump({"model": model, "columns": X_train_encoded.columns.tolist()}, file)

print(f"Model saved as {model_path}")
