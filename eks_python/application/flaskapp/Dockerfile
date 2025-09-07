# Use an official lightweight Python image
FROM python:3.12-slim

# Set a working directory inside the container
WORKDIR /app

# Copy the application files into the container
COPY app.py /app

# Install Flask
RUN pip install --no-cache-dir flask

# Expose the port Flask will run on
EXPOSE 5000

# Command to run the Flask app
CMD ["python", "app.py"]
