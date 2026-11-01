# Indian FMCG Sales Intelligence & Forecasting Platform

A sales forecasting and analytics platform that uses XGBoost to predict future sales and analyze retail trends.  
Built using React, FastAPI, Python, XGBoost, and LangGraph.

## How to Run

### 1. Install Backend Dependencies

From the project root:

```bash
python -m pip install -r backend/requirements.txt
```

### 2. Train the Model

```bash
python -m src.train
```

### 3. Start the Backend

```bash
python -m uvicorn backend.app.main:app --reload --app-dir .
```

### 4. Start the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

### 5. Open Application

Visit: http://localhost:5173

API documentation: http://127.0.0.1:8000/docs

### Optional

Set `OPENAI_API_KEY` to enable LLM-based insights.
