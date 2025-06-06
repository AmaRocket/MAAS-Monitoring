FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    pip install --upgrade pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY main.py /app/
COPY requirements.txt /app/

RUN pip install -r requirements.txt

EXPOSE 9200

CMD ["python", "main.py"]