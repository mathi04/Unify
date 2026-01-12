
# Unify Project Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:mathi04/Unify.git
   ```

2. Start the project with Docker Compose:
   ```bash
   docker-compose up
   ```

3. Create the database:
   ```bash
   docker-compose exec web flask create-db
   ```

4. Or reset the database:
   ```bash
   docker-compose exec web flask reset-db
   ```

5. Seed the database with UNIGE courses:
   ```bash
   docker-compose exec web flask seed-from-json /app/app/ressources/courses.json
   ```

6. Connect to the application at:
   ```bash
   http://127.0.0.1:5000
   ```
