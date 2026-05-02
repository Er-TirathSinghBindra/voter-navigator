FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app ./app

# Expose the port that Cloud Run expects
EXPOSE 8080

# Run the web service on container startup
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
