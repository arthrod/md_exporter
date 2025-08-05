FROM python:3.11-slim

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pandoc \
    libreoffice \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    libopenjp2-7 \
    libtiff5 \
    liblcms2-dev \
    libcairo2 \
    libpango-1.0-0 \
    pkg-config \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -rf /var/lib/apt/lists/* /tmp/requirements.txt

COPY --chown=appuser:appuser . /app

RUN chmod +x /app/entrypoint.sh

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]

