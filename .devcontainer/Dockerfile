FROM rasa/rasa:3.6.21

USER root

WORKDIR /app

COPY . /app

ENV RASA_TELEMETRY_ENABLED=false

RUN apt-get update && apt-get install -y git

RUN rm -rf /var/lib/apt/lists/*

ENTRYPOINT []
CMD ["sleep", "infinity"]
