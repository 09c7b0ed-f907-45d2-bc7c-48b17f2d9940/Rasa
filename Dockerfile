FROM rasa/rasa:3.6.21

ENV RASA_TELEMETRY_ENABLED=false
ENV SQLALCHEMY_SILENCE_UBER_WARNING=1
ENV PYTHONPATH=/app

ARG LAYERS
ENV LAYERS=${LAYERS}

USER root

WORKDIR /app

# Preserve directory names so LAYERS like "src/core" resolve inside container
COPY src/ src/
COPY scripts/ scripts/

RUN chmod +x /app/scripts/*.sh

RUN ./scripts/layer_rasa_projects.sh ${LAYERS}

EXPOSE 5005

USER 1001

ENTRYPOINT ["rasa", "run"]
CMD []
