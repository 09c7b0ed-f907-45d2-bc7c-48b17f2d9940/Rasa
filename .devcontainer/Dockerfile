FROM rasa/rasa-sdk:3.6.2

USER root

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 5055

ENTRYPOINT []
CMD ["sleep", "infinity"]