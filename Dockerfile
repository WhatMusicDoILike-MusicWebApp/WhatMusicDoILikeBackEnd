FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy and install dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/models /app/routes

# Copy application files
COPY models /app/models
COPY routes /app/routes
COPY run.py /app/

# Run the application
CMD ["python", "run.py"]

EXPOSE 5000