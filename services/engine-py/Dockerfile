FROM python:3.12-slim
WORKDIR /srv
# Fonts for the creative renderer: DejaVu (Latin) + Noto Sans Arabic.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY evals ./evals
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
