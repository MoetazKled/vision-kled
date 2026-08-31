FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src src
COPY templates templates
COPY frontend/dist frontend/dist

ENV DATABASE_URL=sqlite:///visionkled.db
ENV DEMO_BASE_URL=http://127.0.0.1:8000
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
