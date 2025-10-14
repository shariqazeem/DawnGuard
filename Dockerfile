FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

RUN mkdir -p /app/logs
RUN mkdir -p /app/staticfiles
RUN mkdir -p /app/mediafiles

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "cyphervault.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]