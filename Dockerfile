FROM python:3.10-slim

# Install system dependencies untuk GeoDjango (GDAL & GEOS)
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Set direktori kerja
WORKDIR /app

# Install pustaka Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode proyek
COPY . .

# Kumpulkan file statis
RUN python manage.py collectstatic --noinput

# Jalankan server produksi
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:10000"]