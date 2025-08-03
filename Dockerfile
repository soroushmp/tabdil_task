FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    build-essential \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install prometheus-client
RUN pip install --no-cache-dir gevent


# Remove build dependencies to reduce image size
RUN apt-get purge -y gcc python3-dev musl-dev build-essential libpq-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
