FROM rasa/rasa:3.6.21

ENV RASA_TELEMETRY_ENABLED=false

USER root

WORKDIR /app

COPY src/ .

RUN rasa train -d domain

EXPOSE 5005

USER 1001

ENTRYPOINT ["rasa", "run"]
CMD []