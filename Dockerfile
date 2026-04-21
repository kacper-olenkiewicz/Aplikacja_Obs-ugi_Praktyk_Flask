FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    libcairo2-dev pkg-config python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ZProjekt/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ZProjekt/ .

RUN mkdir -p uploads

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
