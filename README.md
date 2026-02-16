# The Last Dialogue - Infrastructure

## Deployment to Google Cloud Run

### 1. Backend Deployment

```bash
cd backend
# Build and submit the image to Google Container Registry (or Artifact Registry)
gcloud builds submit --tag gcr.io/PROJECT_ID/last-dialogue-backend

# Deploy to Cloud Run
gcloud run deploy last-dialogue-backend \
  --image gcr.io/PROJECT_ID/last-dialogue-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_key,OPENAI_API_KEY=your_key,TAVILY_API_KEY=your_key
```

### 2. Frontend Deployment

```bash
cd frontend
# Build and submit
gcloud builds submit --tag gcr.io/PROJECT_ID/last-dialogue-frontend

# Deploy
# Make sure to set the BACKEND_URL environment variable to point to the deployed backend
gcloud run deploy last-dialogue-frontend \
  --image gcr.io/PROJECT_ID/last-dialogue-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_API_URL=https://last-dialogue-backend-xyz-uc.a.run.app
```

## Local Development

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn server:app --reload
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
