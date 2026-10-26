# Smart Logistics Risk Platform: Demo Guide

Follow these steps to demonstrate the prototype platform to the college committee in exactly 5 minutes.

## 1. Starting the Backend (Routing Engine)
Open a terminal in the root directory and activate the virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload
```
*Expected: "Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)"*

## 2. Starting the Frontend (UI)
Open a new terminal or simple HTTP server in the frontend directory:
```powershell
cd frontend
python -m http.server 3000
```
Open `http://localhost:3000` in a web browser.

## 3. Interacting with the Dashboard
1. **Selecting Coordinates**: 
   - Origin (Guwahati Base): `26.1445`, `91.7362`
   - Destination: `25.578`, `91.893`
2. **Calculate Shortest Route**: Click the button. Explain that `length_km` (travel cost) operates as the sole metric, rendering a red path traversing mathematically shorter distances.
3. **Calculate Risk-Aware Route**: Click the second button. Explain that the new green path evaluates the Derived Environmental and Logistics Risk formula against highway capacity.
4. **Compare**: Hover over the Route Analytics to show distance vs segment variations. Highlight the "Risk Factors" that prevented the engine from selecting dangerous terrain.

## 4. Explaining Limitations
Transparently mention:
- "The risk categories (CRITICAL, HIGH, MODERATE, LOW) are algorithmically derived indexing heuristics, not Supervised Machine Learning classifications, because there is no verified public hazard target matching OSM lines."
- "ETAs are omitted because assuming unverified speeds over mountain terrains falsifies delivery estimates."
