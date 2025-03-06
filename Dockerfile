FROM rasa/rasa-sdk:3.6.2

USER root

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY src/ .

EXPOSE 5055

USER 1001

ENTRYPOINT ["python", "-m", "rasa_sdk", "--actions", "actions"]
CMD [""]
