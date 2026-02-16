FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for some python packages)
# RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port
EXPOSE 8080

# Command to run the application
# Cloud Run expects the port to be defined by $PORT env var, but 8080 is default.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
