FROM python:3.12-slim

# Install minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Non-root user (HF Spaces requirement)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ ./app/
COPY static/ ./static/

# Switch user
RUN chown -R appuser:appuser /app
USER appuser

# HF Spaces default port
ENV PORT=7860
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 7860

# Run uvicorn — WAJIB bind ke 0.0.0.0
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]