# Gunakan Python resmi
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Copy requirements
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua source code
COPY . /app

# Expose port untuk Hugging Face
EXPOSE 7860

# Jalankan FastAPI pakai uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
