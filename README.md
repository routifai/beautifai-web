# Barber Marketplace API

A comprehensive FastAPI backend for a barber marketplace application with authentication, booking management, payment processing, and more.

## Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **User Management**: Customer and barber user types with profile management
- **Barber Operations**: Barber profiles, services, reviews, and availability
- **Booking System**: Appointment scheduling with conflict detection
- **Payment Processing**: Stripe integration for secure payments
- **Search & Discovery**: Location-based barber search with filters
- **Database Migrations**: Alembic for database schema management

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with python-jose
- **Password Hashing**: bcrypt with passlib
- **Payment Processing**: Stripe
- **Caching**: Redis (configured but not implemented)
- **Background Tasks**: Celery (configured but not implemented)
- **API Documentation**: Auto-generated with OpenAPI/Swagger

## Project Structure

```
/backend
├── /app
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── /api
│   │   ├── __init__.py
│   │   ├── /v1
│   │   │   ├── __init__.py
│   │   │   ├── /endpoints
│   │   │   │   ├── auth.py     # Authentication endpoints
│   │   │   │   ├── users.py    # User management
│   │   │   │   ├── barbers.py  # Barber operations
│   │   │   │   ├── bookings.py # Booking system
│   │   │   │   └── payments.py # Payment processing
│   │   │   └── api.py          # API router aggregation
│   ├── /core
│   │   ├── config.py           # Settings and environment
│   │   ├── security.py         # JWT and auth utilities
│   │   └── deps.py             # Dependency injection
│   ├── /models
│   │   ├── __init__.py
│   │   ├── user.py             # SQLAlchemy models
│   │   ├── barber.py
│   │   ├── booking.py
│   │   └── base.py
│   ├── /schemas
│   │   ├── __init__.py
│   │   ├── user.py             # Pydantic models for API
│   │   ├── barber.py
│   │   └── booking.py
│   ├── /services
│   │   ├── __init__.py
│   │   ├── auth_service.py     # Business logic
│   │   ├── booking_service.py
│   │   └── payment_service.py
│   └── /db
│       ├── __init__.py
│       ├── database.py         # Database connection
│       └── session.py          # Database sessions
├── requirements.txt
├── alembic.ini                 # Database migrations
├── /alembic
└── .env
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb barber_marketplace
   
   # Run migrations
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/barber_marketplace
DATABASE_TEST_URL=postgresql://user:password@localhost/barber_marketplace_test

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://yourdomain.com

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# App Configuration
APP_NAME=Barber Marketplace API
DEBUG=True
ENVIRONMENT=development
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `DELETE /api/v1/users/me` - Deactivate current user
- `GET /api/v1/users/{user_id}` - Get user by ID

### Barbers
- `POST /api/v1/barbers/profile` - Create barber profile
- `GET /api/v1/barbers/profile` - Get current barber profile
- `PUT /api/v1/barbers/profile` - Update barber profile
- `GET /api/v1/barbers/search` - Search barbers
- `GET /api/v1/barbers/{barber_id}` - Get barber by ID
- `POST /api/v1/barbers/{barber_id}/reviews` - Create review
- `GET /api/v1/barbers/{barber_id}/reviews` - Get barber reviews

### Bookings
- `POST /api/v1/bookings/` - Create booking
- `GET /api/v1/bookings/` - Get user bookings
- `GET /api/v1/bookings/{booking_id}` - Get booking by ID
- `PUT /api/v1/bookings/{booking_id}/status` - Update booking status
- `DELETE /api/v1/bookings/{booking_id}` - Cancel booking
- `GET /api/v1/bookings/barber/{barber_id}/availability` - Get barber availability
- `GET /api/v1/bookings/barber/{barber_id}/bookings` - Get barber bookings

### Payments
- `POST /api/v1/payments/create-payment-intent` - Create payment intent
- `POST /api/v1/payments/confirm-payment` - Confirm payment
- `POST /api/v1/payments/webhook` - Stripe webhook handler
- `POST /api/v1/payments/{booking_id}/refund` - Refund payment

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current migration status
alembic current
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Formatting
```bash
# Install formatting tools
pip install black isort

# Format code
black .
isort .
```

### Type Checking
```bash
# Install mypy
pip install mypy

# Run type checking
mypy .
```

## Production Deployment

1. **Set production environment variables**
2. **Use a production WSGI server like Gunicorn**
3. **Set up proper CORS origins**
4. **Configure database connection pooling**
5. **Set up monitoring and logging**
6. **Configure SSL/TLS certificates**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License. 