FROM rasa/rasa-sdk:3.6.2

USER root

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENTRYPOINT []
CMD ["sleep", "infinity"]