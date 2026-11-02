# CineMind AI — Movie Genre Classification

A premium cinematic web app for the AI Applications Lab (26ECP-102). It predicts a movie's primary genre from a plot summary using **TF-IDF + Multinomial Naive Bayes**.

**Student:** Vaibhav Kumar · **UID:** 26BCS13517 · **Section:** 10B · **Project:** Group project

## Architecture

- `docs/` — static frontend (HTML, CSS, JavaScript), suitable for GitHub Pages.
- `backend/app.py` — Flask API, trains the text-classification pipeline and exposes `/api/predict`, `/api/stats`, `/api/health`.
- `data/movie_genre_demo_dataset.csv` — small, curated educational dataset to make the project runnable immediately.
- `render.yaml` — one-click Render backend configuration.

GitHub Pages cannot run Python/Flask. The recommended free/low-friction deployment is:
1. Host the static frontend on GitHub Pages.
2. Host the Flask API on Render.
3. Set the deployed API URL in `docs/app.js`.

## Run locally

Python 3.10 or 3.11 recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python backend/app.py
```

Open http://127.0.0.1:5000. Flask serves the frontend and API locally.

## API endpoints

### `GET /api/health`
Returns whether the model loaded successfully.

### `GET /api/stats`
Returns dataset size, number of genres, test accuracy, genre counts, confusion matrix and classification report.

### `POST /api/predict`
JSON body:
```json
{"overview":"A young astronaut receives a mysterious signal from a distant planet..."}
```
Returns predicted genre, model probability and the top three alternatives.

## Deploy backend to Render

1. Push this repository to GitHub.
2. Sign in to Render and choose **New → Blueprint**.
3. Connect the repository; Render reads `render.yaml`.
4. Wait for deployment. Copy the service URL, e.g. `https://cinemind-ai-api.onrender.com`.
5. Test `https://YOUR-API-URL/api/health`.

Render free services may sleep when inactive and the first request can take some time to wake up.

## Deploy frontend to GitHub Pages

1. In GitHub, open the repository → **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Select branch `main`, folder `/docs`, then **Save**.
4. Wait for the published Pages URL.

Then edit `docs/app.js`:
```js
const API_BASE = "https://YOUR-RENDER-SERVICE.onrender.com";
```
Commit and push the change. The frontend will now call the hosted Flask API.

If you prefer a single-host deployment, Render can also serve the frontend and backend together: deploy the repository as a Web Service using the included `render.yaml`, then visit the Render service URL. In that setup leave `API_BASE = ""`.

## Use the official Kaggle dataset

The included CSV is a 72-row **educational demo dataset**, not the original Kaggle data. The accuracy shown in the interface is calculated on this small sample and must not be described as full-dataset performance.

For a stronger final evaluation:
1. Download `tmdb_5000_movies.csv` from https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata.
2. Put it in `data/` and set `DATA_PATH` to that file in the Render environment, or replace the demo CSV with the downloaded file.
3. Redeploy/restart the backend and check `/api/stats`.

TMDB movies can have multiple genres. This starter project simplifies the task by using the first genre as the primary label. For the final academic submission, mention this limitation or extend the project to multi-label classification.

## Group submission checklist

- Add all group members' names, UIDs and contributions to the README/report.
- Run the model on the official Kaggle dataset before claiming final performance.
- Capture genuine screenshots of the running website and prediction output.
- Be ready to explain TF-IDF, Naive Bayes, train/test split, accuracy and confusion matrix.
