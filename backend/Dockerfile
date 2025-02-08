FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so

COPY requirements.txt /app/

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate"]