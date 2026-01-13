FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

ENV PYTHONUNBUFFERED=1
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000

ENV FLASK_ENV=production
ENV DEV_SMS_BACKEND=console

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2", "--threads", "4"]
