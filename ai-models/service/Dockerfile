FROM python:3.11-slim

WORKDIR /app

COPY service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service/main.py .
COPY models /app/models

ENV MODELS_DIR=/app/models
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
