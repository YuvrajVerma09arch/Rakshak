FROM python:3.12-slim

WORKDIR /srv/rakshak/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The offline path reads rule packs from the package and corpora/blocklist from ../data
COPY backend/app ./app
COPY data ../data

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
