FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update \
  && apt-get install -y libpq-dev gcc \
  && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV HOST 0.0.0.0

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 