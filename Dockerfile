FROM rasa/rasa:3.6.21

ENV RASA_TELEMETRY_ENABLED=false
ENV SQLALCHEMY_SILENCE_UBER_WARNING=1

USER root

WORKDIR /app

COPY src/ .
COPY scripts/ .

RUN python /app/scripts/generate_rasa_resources.py

RUN rasa train -d domain

EXPOSE 5005

USER 1001

ENTRYPOINT ["rasa", "run"]
CMD []
