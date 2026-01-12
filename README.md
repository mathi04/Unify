Clone the repo
Start the project with docker compose up
create the db with docker compose exec web flask create-db or reset it with docker compose exec web flask reset-db
seed the db with unige course with docker compose exec web flask seed-from-json /app/app/ressources/courses.json
connect to 127.0.0.1:5000
