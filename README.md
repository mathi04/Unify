# Unify - University Course Management System

A Flask-based web application for managing university courses, student enrollments, and academic planning.

## Features

- **User Authentication**: Separate login for students and professors
- **Course Management**: Create, view, and manage courses
- **Student Enrollment**: Enroll in courses and track progress
- **Planning Calendar**: View weekly schedules with course times
- **Grade Tracking**: Track student grades and completion status
- **Responsive UI**: Modern interface with HTML/CSS templates

## Tech Stack

- **Backend**: Flask (Python web framework)
- **Database**: MySQL/MariaDB with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Environment**: Docker & Docker Compose

## Prerequisites

- Docker & Docker Compose installed on your system
- Git (for cloning the repository)

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Unify
```

### 2. Set Up Environment Variables

Copy the example environment file and update it with your values:

```bash
cp .env.example .env
```

Edit `.env` and update the `SECRET_KEY` to a secure random string:

```
SECRET_KEY=your-secure-random-secret-key
DATABASE_URI=mysql+pymysql://admin_db:unify_admin@db:3306/unify_db
FLASK_APP=app
FLASK_ENV=development
```

### 3. Start the Application with Docker

```bash
docker-compose up -d
```

This will:
- Start a MariaDB database container
- Build and start the Flask web application
- Expose the website on `http://localhost:5000`

### 4. Initialize the Database

Initialize the database tables and seed with sample data:

```bash
# Access the web container
docker-compose exec web flask init-db
docker-compose exec web flask seed-db
```

### 5. Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## Sample Login Credentials

After seeding the database, you can log in with:

**Students:**
- Username: `alice` / Password: `password123`
- Username: `bob` / Password: `password123`

**Professors:**
- Username: `prof_smith` / Password: `password123`
- Username: `prof_jones` / Password: `password123`

## Development

### Running Locally Without Docker

If you prefer to run without Docker:

1. **Install Dependencies:**
```bash
cd web
pip install -r requirements.txt
```

2. **Set Up Local Database:**
   - Install MySQL/MariaDB locally
   - Update `DATABASE_URI` in `.env` to point to your local database

3. **Run the Application:**
```bash
cd web
python run.py
```

Or using Flask CLI:
```bash
export FLASK_APP=app
export FLASK_ENV=development
flask run
```

### Database Commands

```bash
# Initialize database tables
flask init-db

# Reset database (drops and recreates all tables)
flask reset-db

# Seed database with sample data
flask seed-db
```

## Project Structure

```
Unify/
├── docker-compose.yml       # Docker orchestration
├── .env.example            # Environment variables template
├── web/
│   ├── Dockerfile          # Web app Docker config
│   ├── requirements.txt    # Python dependencies
│   ├── run.py             # Application entry point
│   └── app/
│       ├── __init__.py    # Flask app factory
│       ├── config.py      # Configuration
│       ├── models.py      # Database models
│       ├── cli.py         # CLI commands
│       ├── extensions.py  # Flask extensions
│       ├── auth/          # Authentication blueprint
│       ├── courses/       # Courses blueprint
│       ├── main/          # Main blueprint
│       └── templates/     # HTML templates
```

## Database Models

- **User**: Base user model (authentication)
- **Student**: Student profile and details
- **Professor**: Professor profile and department
- **Course**: Course information and schedule
- **Enrollment**: Student course enrollments and grades

## Troubleshooting

### Port Already in Use

If port 5000 or 3306 is already in use, edit `docker-compose.yml` to change the port mappings:

```yaml
ports:
  - "5001:5000"  # Change 5001 to any available port
```

### Database Connection Issues

Make sure the database container is running:
```bash
docker-compose ps
```

Check logs:
```bash
docker-compose logs db
docker-compose logs web
```

### Reset Everything

To completely reset the application:
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec web flask init-db
docker-compose exec web flask seed-db
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is for educational purposes.

## Support

For issues or questions, please open an issue on GitHub.
