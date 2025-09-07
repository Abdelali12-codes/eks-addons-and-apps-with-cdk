from flask import Flask, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import random

app = Flask(__name__)

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    "flask_app_request_count",
    "Total HTTP requests",
    ["method", "endpoint"]
)

REQUEST_LATENCY = Histogram(
    "flask_app_request_latency_seconds",
    "Request latency",
    ["endpoint"]
)

@app.route("/")
def hello():
    REQUEST_COUNT.labels(method="GET", endpoint="/").inc()
    with REQUEST_LATENCY.labels(endpoint="/").time():
        time.sleep(random.uniform(0.1, 0.5))  # Simulate latency
        return "Hello, World!"

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

