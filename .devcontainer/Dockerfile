FROM rasa/rasa:3.6.21

USER root

WORKDIR /workspace

ENV RASA_TELEMETRY_ENABLED=false

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

EXPOSE 5005

ENTRYPOINT []
CMD ["sleep", "infinity"]
