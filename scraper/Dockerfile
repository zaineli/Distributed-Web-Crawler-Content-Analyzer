FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy crawler code
COPY . /app

# Run the crawler
CMD ["python", "crawler.py"]