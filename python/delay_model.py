from pathlib import Path
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import (roc_auc_score,average_precision_score,
    precision_score,recall_score,f1_score,classification_report)

BASE_DIR = Path(r"")
INPUT_FILE = BASE_DIR / "flights_2024_2025_raw.parquet" #Combined Datset Path
PREDICTION_FILE = "delay_predictions_2025.parquet"
IMPORTANCE_FILE = "delay_model_feature_importance.csv"

TRAIN_SAMPLE_SIZE = 1_500_000 #Total 15.28 million records (2024 and 2025 combined dataset)
RANDOM_STATE = 42

REQUIRED_COLUMNS = [
    "FlightDate","Marketing_Airline_Network","DOT_ID_Marketing_Airline","Flight_Number_Marketing_Airline",
    "Tail_Number","Origin","Dest","CRSDepTime","DayOfWeek","Month",
    "Distance","CRSElapsedTime","ArrDel15","Cancelled","Diverted"]

CATEGORICAL_FEATURES = ["Marketing_Airline_Network","Origin","Dest"]
NUMERIC_FEATURES = ["DepartureHour","DayOfWeek","Month","Distance","CRSElapsedTime"]

def load_data() -> pd.DataFrame:
    print("\nLoading required columns from Parquet...")
    df = pd.read_parquet(INPUT_FILE,
        columns=REQUIRED_COLUMNS,)
    print(f"Rows loaded: {len(df):,}")
    print(f"Columns loaded: {len(df.columns)}")

    df["FlightDate"] = pd.to_datetime(
        df["FlightDate"],errors="coerce")
    df = df[df["FlightDate"].notna()].copy() #Remove flights with invalid dates
    print(
        f"Date range: "
        f"{df['FlightDate'].min().date()} → "
        f"{df['FlightDate'].max().date()}")
    return df

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Scheduled departure hour
    # CRSDepTime is HHMM local time
    df["CRSDepTime"] = pd.to_numeric(
        df["CRSDepTime"],errors="coerce")
    df["DepartureHour"] = (df["CRSDepTime"].fillna(0).astype(int).floordiv(100).clip(0, 23))

    for col in ["DayOfWeek","Month","Distance","CRSElapsedTime",]:
        df[col] = pd.to_numeric(df[col],errors="coerce",)
    for col in CATEGORICAL_FEATURES:
        df[col] = (df[col].fillna("UNKNOWN").astype(str).str.strip())
    return df

def stratified_sample(df: pd.DataFrame,target: str,sample_size: int,) -> pd.DataFrame:
    if sample_size is None or len(df) <= sample_size:
        return df
    positive = df[df[target] == 1]
    negative = df[df[target] == 0]
    positive_n = int(sample_size * len(positive) / len(df))
    negative_n = sample_size - positive_n
    positive_sample = positive.sample(
        n=min(positive_n, len(positive)),
        random_state=RANDOM_STATE)
    negative_sample = negative.sample(
        n=min(negative_n, len(negative)),
        random_state=RANDOM_STATE)
    result = pd.concat([positive_sample,negative_sample,],ignore_index=True,)
    return result.sample(
        frac=1,random_state=RANDOM_STATE).reset_index(drop=True)

def main():
    print("FLIGHT DELAY PREDICTION MODEL")
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find:\n{INPUT_FILE}")
    df = load_data()
    df = prepare_features(df)
    train = df[
        df["FlightDate"].dt.year == 2024].copy() #2024 year used for training
    test = df[
        df["FlightDate"].dt.year == 2025].copy() #2025 year used for testing
    print("\nInitial split:")
    print(f"2024: {len(train):,}")
    print(f"2025: {len(test):,}")

    train = train[ #Target only for non-canceled and non-diverted flights
        (train["Cancelled"] == 0)
        & (train["Diverted"] == 0)
        & train["ArrDel15"].notna()].copy()

    test = test[
        (test["Cancelled"] == 0)
        & (test["Diverted"] == 0)
        & test["ArrDel15"].notna()].copy()

    print("\nAfter removing cancelled/diverted flights:")
    print(f"Training: {len(train):,}")
    print(f"Testing:  {len(test):,}")

    train = stratified_sample(train,
        "ArrDel15",
        TRAIN_SAMPLE_SIZE)
    print(f"\nTraining rows used: {len(train):,}")

    y_train = train["ArrDel15"].astype(int)
    y_test = test["ArrDel15"].astype(int)
    feature_columns = (
        CATEGORICAL_FEATURES
        + NUMERIC_FEATURES)
    X_train = train[feature_columns].copy()
    X_test = test[feature_columns].copy()

    for col in NUMERIC_FEATURES:
        median = X_train[col].median()
        X_train[col] = X_train[col].fillna(median)
        X_test[col] = X_test[col].fillna(median)

    for col in CATEGORICAL_FEATURES:
        X_train[col] = (X_train[col].fillna("UNKNOWN").astype(str))
        X_test[col] = (X_test[col].fillna("UNKNOWN").astype(str))
    cat_indices = [
        feature_columns.index(col)
        for col in CATEGORICAL_FEATURES]

    print("\nTraining CatBoost...")
    model = CatBoostClassifier(
        iterations=700,
        depth=8,
        learning_rate=0.08,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=RANDOM_STATE,
        cat_features=cat_indices,
        verbose=100,
        allow_writing_files=False,)

    model.fit(
        X_train,
        y_train,
        eval_set=(X_test, y_test),
        use_best_model=True,
        early_stopping_rounds=75)

    print("\nGenerating 2025 predictions...")
    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.50).astype(int)

    roc_auc = roc_auc_score(y_test,probabilities,)
    pr_auc = average_precision_score(y_test,probabilities,)
    precision = precision_score(y_test,predictions,zero_division=0)
    recall = recall_score(y_test,predictions,zero_division=0)
    f1 = f1_score(y_test,predictions,zero_division=0)

    print("MODEL PERFORMANCE")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"PR-AUC:    {pr_auc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1:        {f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test,predictions,digits=4,zero_division=0))

    importance = model.get_feature_importance()
    importance_df = (pd.DataFrame({"Feature": feature_columns,"Importance": importance})
        .sort_values("Importance",ascending=False))
    print("\nFeature Importance:")
    print(importance_df.to_string(index=False))
    importance_df.to_csv(
        IMPORTANCE_FILE,
        index=False)

    prediction_output = pd.DataFrame(
        {"FlightDate": test["FlightDate"].values,
        "DOT_ID_Marketing_Airline": test["DOT_ID_Marketing_Airline"].values,
            "Marketing_Airline_Network": test["Marketing_Airline_Network"].values,
            "Flight_Number_Marketing_Airline":test["Flight_Number_Marketing_Airline"].values,
            "Tail_Number":test["Tail_Number"].values,
            "Origin":test["Origin"].values,
            "Dest":test["Dest"].values,
            "DepartureHour":test["DepartureHour"].values,
            "Predicted_Delay_Probability":probabilities,
            "Predicted_Delayed_15":predictions,
            "Actual_Delayed_15":y_test.values,
        })

    prediction_output["Risk_Category"] = np.select(
        [prediction_output["Predicted_Delay_Probability"] < 0.30,
                prediction_output["Predicted_Delay_Probability"] < 0.60],
        ["Low","Medium"],default="High")

    prediction_output.to_parquet(PREDICTION_FILE,
        engine="pyarrow",compression="snappy",index=False)

    print("OUTPUT")
    print(f"Prediction rows: "
        f"{len(prediction_output):,}")
    print(f"Prediction file:\n"
          f"{PREDICTION_FILE}")
    print(
        f"Prediction file size: "
        f"{PREDICTION_FILE.stat().st_size / (1024**2):.1f} MB")
    print("\nDone.")

if __name__ == "__main__":
    main()