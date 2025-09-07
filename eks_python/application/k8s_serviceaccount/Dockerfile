FROM python:3.11-slim

WORKDIR /app
COPY app.py .

RUN pip install boto3

CMD ["python", "app.py"]
