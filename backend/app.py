import os
import json
import ast
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = Path(os.getenv("DATA_PATH", BASE_DIR / "data" / "movie_genre_demo_dataset.csv"))
FRONTEND_DIR = BASE_DIR / "docs"

app = Flask(__name__, static_folder=None)
CORS(app)

def parse_genres(value):
    """Extract the first genre from the TMDB JSON genre field."""
    if pd.isna(value):
        return None
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except Exception:
        try:
            parsed = ast.literal_eval(value)
        except Exception:
            return None
    if isinstance(parsed, list) and parsed:
        first = parsed[0]
        return first.get("name") if isinstance(first, dict) else str(first)
    return None

def load_data(path):
    data = pd.read_csv(path)
    if not {"overview", "genres"}.issubset(data.columns):
        raise ValueError("Dataset must contain 'overview' and 'genres' columns.")
    data = data.copy()
    # TMDB Kaggle file stores genres as JSON strings; demo CSV stores plain labels.
    if data["genres"].astype(str).str.startswith(("[", "{")).any():
        data["genres"] = data["genres"].apply(parse_genres)
    if "title" not in data.columns:
        data["title"] = [f"Movie {i+1}" for i in range(len(data))]
    data = data.dropna(subset=["overview", "genres"])
    data["overview"] = data["overview"].astype(str).str.strip()
    data["genres"] = data["genres"].astype(str).str.strip()
    data = data[(data["overview"] != "") & (data["genres"] != "")]
    counts = data["genres"].value_counts()
    # Keep labels with enough samples for a stratified split.
    data = data[data["genres"].isin(counts[counts >= 5].index)]
    return data.reset_index(drop=True)

def build_model():
    data = load_data(DATA_PATH)
    if data["genres"].nunique() < 2:
        raise RuntimeError("Need at least two genres with five examples each.")
    X_train, X_test, y_train, y_test = train_test_split(
        data["overview"], data["genres"], test_size=0.25,
        random_state=42, stratify=data["genres"]
    )
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)),
        ("classifier", MultinomialNB(alpha=0.5))
    ])
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    labels = sorted(data["genres"].unique())
    matrix = confusion_matrix(y_test, predictions, labels=labels)
    report = classification_report(y_test, predictions, labels=labels, output_dict=True, zero_division=0)
    return {
        "model": pipeline,
        "data": data,
        "accuracy": accuracy,
        "labels": labels,
        "confusion_matrix": matrix.tolist(),
        "report": report,
        "test_size": len(y_test),
        "train_size": len(y_train),
    }

try:
    MODEL_BUNDLE = build_model()
    MODEL_ERROR = None
except Exception as exc:
    MODEL_BUNDLE = None
    MODEL_ERROR = str(exc)

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok" if MODEL_BUNDLE else "error",
        "model_loaded": MODEL_BUNDLE is not None,
        "error": MODEL_ERROR
    }), (200 if MODEL_BUNDLE else 503)

@app.get("/api/stats")
def stats():
    if not MODEL_BUNDLE:
        return jsonify({"error": MODEL_ERROR or "Model not available"}), 503
    data = MODEL_BUNDLE["data"]
    counts = data["genres"].value_counts().sort_index().to_dict()
    return jsonify({
        "accuracy": round(MODEL_BUNDLE["accuracy"] * 100, 2),
        "total_movies": int(len(data)),
        "genre_count": int(data["genres"].nunique()),
        "train_size": MODEL_BUNDLE["train_size"],
        "test_size": MODEL_BUNDLE["test_size"],
        "genres": counts,
        "labels": MODEL_BUNDLE["labels"],
        "confusion_matrix": MODEL_BUNDLE["confusion_matrix"],
        "classification_report": MODEL_BUNDLE["report"],
        "dataset_note": "Demo dataset" if len(data) <= 100 else "External dataset"
    })

@app.post("/api/predict")
def predict():
    if not MODEL_BUNDLE:
        return jsonify({"error": MODEL_ERROR or "Model not available"}), 503
    payload = request.get_json(silent=True) or {}
    overview = str(payload.get("overview", "")).strip()
    if len(overview) < 20:
        return jsonify({"error": "Please enter a plot summary of at least 20 characters."}), 400
    if len(overview) > 3000:
        return jsonify({"error": "Please keep the plot summary under 3,000 characters."}), 400
    model = MODEL_BUNDLE["model"]
    genre = str(model.predict([overview])[0])
    probabilities = model.predict_proba([overview])[0]
    classes = model.named_steps["classifier"].classes_
    ranking = sorted(
        [{"genre": str(label), "confidence": round(float(prob) * 100, 2)}
         for label, prob in zip(classes, probabilities)],
        key=lambda item: item["confidence"], reverse=True
    )
    return jsonify({
        "predicted_genre": genre,
        "confidence": ranking[0]["confidence"],
        "alternatives": ranking[:3],
        "note": "Confidence is the model's estimated class probability, not a guarantee."
    })

@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/<path:path>")
def frontend_files(path):
    return send_from_directory(FRONTEND_DIR, path)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
