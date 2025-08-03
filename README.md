# Tabdil - B2B Phone Number Credit Service

A comprehensive B2B platform for selling and managing phone number credits, built with Django and modern DevOps practices.

## Features

- 📱 Sell and manage phone number credits
- 🏢 B2B account management
- 📊 Transaction monitoring and reporting
- 🔒 Secure and scalable architecture
- 📈 Performance monitoring with Prometheus and Grafana
- 📝 Comprehensive logging with ELK Stack (Elasticsearch, Logstash, Kibana)
- 🐳 Docker and Docker Compose support
- 🔄 Redis caching for high performance
- 🔍 Audit logging for all operations

## Tech Stack

- **Backend**: Django 5.2
- **Database**: PostgreSQL
- **Cache**: Redis
- **API**: Django REST Framework
- **Authentication**: JWT
- **Monitoring**: Prometheus + Grafana
- **Logging**: Logstash + Elasticsearch
- **Web Server**: Nginx
- **WSGI Server**: Gunicorn

## Prerequisites

- Docker and Docker Compose
- Python 3.9+


## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/soroushmp/tabdil_task.git
   cd tabdil-task
   ```

2. Create a `.env` file from the example and configure it:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the services using Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

4. The service will automatically:
   - Run database migrations
   - Create a default admin user

5. Access the application:
   - Web Interface: http://127.0.0.1
   - API Documentation (Swagger): http://127.0.0.1/swagger/
   - Admin Panel: http://127.0.0.1/admin
     - Username: admin
     - Password: admin
   - Grafana: http://127.0.0.1:3000
     - Username: admin
     - Password: admin
   - Prometheus: http://127.0.0.1:9090
   - Kibana: http://127.0.0.1:5601

## API Documentation

Interactive API documentation is available at http://127.0.0.1/swagger/ when the service is running.

## Development

### Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Running Tests

```bash
python manage.py test
```

## Production Deployment

For production deployment, ensure you:

1. Set `DEBUG=False` in your environment variables
2. Configure proper database credentials
3. Set up proper SSL/TLS
4. Configure proper CORS settings
5. Set up proper logging and monitoring

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Django settings
DEBUG=True
SECRET_KEY=change_this_to_a_secure_random_string_in_production
ALLOWED_HOSTS=*

# Database settings
DB_NAME=tabdil
DB_USER=tabdil_user
DB_PASSWORD=tabdil_password
DB_HOST=pgbouncer
DB_PORT=6432

# Redis settings
REDIS_URL=redis://redis:6379/0
CACHE_URL=redis://redis:6379/1

# Prometheus & Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```


---

Built with ❤️ by the Soroush Moradpour
