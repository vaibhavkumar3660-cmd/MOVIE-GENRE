/*
 * Set API_BASE to your deployed Render backend URL after deploying it.
 * Example: const API_BASE = "https://cinemind-ai-api.onrender.com";
 * For local development leave it empty; Flask serves both frontend and API.
 */
const API_BASE = "";

const apiUrl = (path) => `${API_BASE}${path}`;
const $ = (id) => document.getElementById(id);
const plotInput = $("plot-input");
const predictBtn = $("predict-btn");
const resultPanel = $("result-panel");
const errorMessage = $("error-message");

const samplePlots = [
  "A young astronaut receives a mysterious signal from a distant planet. As the crew investigates, they discover a secret that could change humanity forever.",
  "Two strangers accidentally exchange their luggage at an airport and spend a hilarious weekend trying to find the owners while becoming friends.",
  "A family moves into an old house where strange voices echo from a locked room every night, revealing a terrifying secret from the past."
];
let sampleIndex = 0;

plotInput.addEventListener("input", () => {
  $("char-count").textContent = `${plotInput.value.length} / 3000 characters`;
  errorMessage.textContent = "";
});

$("sample-btn").addEventListener("click", () => {
  plotInput.value = samplePlots[sampleIndex % samplePlots.length];
  sampleIndex++;
  plotInput.dispatchEvent(new Event("input"));
  plotInput.focus();
});

async function getJSON(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

async function loadStats() {
  try {
    const data = await getJSON("/api/stats");
    $("movie-count").textContent = data.total_movies.toLocaleString();
    $("genre-count").textContent = data.genre_count;
    $("accuracy").textContent = `${data.accuracy}%`;
    $("api-dot").style.background = "#67dba2";
    $("api-dot").style.boxShadow = "0 0 10px #67dba2";
    $("api-status").textContent = "AI model online";
    $("split-value").textContent = `${Math.round(data.train_size/(data.train_size+data.test_size)*100)}% / ${Math.round(data.test_size/(data.train_size+data.test_size)*100)}%`;
    const entries = Object.entries(data.genres).sort((a,b) => b[1]-a[1]);
    const max = Math.max(...entries.map(([,v]) => v), 1);
    $("genre-bars").innerHTML = entries.map(([name,count]) => `
      <div class="genre-row">
        <span>${escapeHTML(name)}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${(count/max)*100}%"></div></div>
        <b class="genre-value">${count}</b>
      </div>`).join("");
    if (data.dataset_note === "Demo dataset") {
      $("accuracy").title = "Accuracy on the included small educational demo dataset only.";
    }
  } catch (error) {
    $("api-status").textContent = "Backend not connected";
    $("api-dot").style.background = "#ff7c91";
    $("api-dot").style.boxShadow = "0 0 10px #ff7c91";
    $("genre-bars").innerHTML = `<p class="muted">Connect the backend to load live model statistics.</p>`;
    $("error-message").textContent = "Backend connection unavailable. Check the API_BASE setting and backend deployment.";
  }
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  })[char]);
}

async function predictGenre() {
  const overview = plotInput.value.trim();
  errorMessage.textContent = "";
  resultPanel.hidden = true;
  if (overview.length < 20) {
    errorMessage.textContent = "Please enter a plot summary with at least 20 characters.";
    plotInput.focus();
    return;
  }
  predictBtn.disabled = true;
  $("button-label").textContent = "Analysing your story…";
  $("button-arrow").textContent = "◌";
  try {
    const data = await getJSON("/api/predict", {
      method: "POST",
      body: JSON.stringify({ overview })
    });
    $("result-genre").textContent = data.predicted_genre;
    $("confidence-value").textContent = `${data.confidence.toFixed(1)}%`;
    $("confidence-bar").style.width = `${Math.min(data.confidence,100)}%`;
    $("result-note").textContent = "Top predicted genre";
    $("alternatives").innerHTML = data.alternatives.map((item,index) =>
      `<span class="alt-pill">${index === 0 ? "Top match · " : ""}${escapeHTML(item.genre)} <b>${item.confidence.toFixed(1)}%</b></span>`
    ).join("");
    $("result-disclaimer").textContent = data.note;
    resultPanel.hidden = false;
    resultPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (error) {
    errorMessage.textContent = error.message;
  } finally {
    predictBtn.disabled = false;
    $("button-label").textContent = "Predict movie genre";
    $("button-arrow").textContent = "→";
  }
}

predictBtn.addEventListener("click", predictGenre);
loadStats();
