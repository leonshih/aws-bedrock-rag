FROM python:3.11-slim

WORKDIR /app

# Install Flask for Hello World
RUN pip install --no-cache-dir flask==3.0.0

# Copy application
COPY main.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
