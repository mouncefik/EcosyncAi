# Energy Insight Application

A web application for energy consumption prediction, power generation forecasting, and load optimization with interactive visualizations.

## Features

- User authentication and profiles
- Energy consumption prediction
- Solar power generation forecasting
- Load optimization recommendations
- Interactive dashboard with energy statistics
- Device management
- Historical energy data tracking
- AI assistant for energy-related queries

## Docker Setup

This application can be run using Docker and Docker Compose for easy deployment across different environments.

### Prerequisites

- Docker and Docker Compose installed on your machine
- API keys for weather data and Google Generative AI (optional)

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
WEATHER_API_KEY=your_weather_api_key
GOOGLE_API_KEY=your_google_api_key
```

### Running with Docker Compose

1. Build and start the containers:

```bash
docker-compose up -d
```

2. The application will be available at:
   - Web application: http://localhost:5000
   - pgAdmin (database management): http://localhost:5050
     - Login with email: admin@energy.com
     - Password: admin_password

3. To stop the containers:

```bash
docker-compose down
```

4. To stop the containers and remove volumes (will delete database data):

```bash
docker-compose down -v
```

## Connecting to the Database

- Host: localhost
- Port: 5432
- Database: energy_db
- Username: energy_user
- Password: energy_password

Inside Docker containers, the database host is `db` instead of `localhost`.

## Security Notes

- For production use, replace all default passwords in the docker-compose.yml file with strong, unique passwords
- Store sensitive information in environment variables or a secrets manager, not in the source code
- Consider using Docker secrets for managing sensitive information in production

## Development

To run the application locally without Docker:

1. Install Python 3.11
2. Install dependencies from requirements.txt
3. Set up a PostgreSQL database
4. Run the application with `gunicorn --bind 0.0.0.0:5000 --reload main:app`