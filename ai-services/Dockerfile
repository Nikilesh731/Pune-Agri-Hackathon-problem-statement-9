FROM python:3.11-slim

# Install system dependencies for OCR, imaging, and document processing
# CRITICAL: These MUST be installed for Railway production
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    tesseract-ocr-mar \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies FIRST (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Tesseract data directory for OCR (CRITICAL)
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Set production defaults
ENV PORT=8080
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check (Railway requires this)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Run application - Railway will pass PORT via environment
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

