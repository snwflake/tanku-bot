FROM python:3.11-slim

EXPOSE 8085

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /tmp/requirements.txt

WORKDIR /tanku-bot
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./app /tanku-bot/app

CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8085"]