FROM python:3.12-slim

# Create non-root user
RUN addgroup --system appgrp && adduser --system --ingroup appgrp appuser

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY controller.py /app/controller.py

# make sure files are owned by non-root
RUN chown -R appuser:appgrp /app
USER appuser

ENV PYTHONUNBUFFERED=1
EXPOSE 8000 8080

# Run kopf operator (kopf runs the python module)
CMD ["kopf", "run", "--standalone", "/app/controller.py"]
