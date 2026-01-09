import click
import json
from datetime import datetime
from werkzeug.security import generate_password_hash
from .extensions import db
from .models import User, Professor, Course


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        print("✓ Tables created successfully")
    
    @app.cli.command("reset-db")
    def reset_db():
        """Drop all tables and recreate them."""
        db.drop_all()
        db.create_all()
        print("✓ Database reset successfully")
    
    @app.cli.command("seed-db")
    def seed_db():
        """Populate database with sample data for testing."""
        from .models import User, Student, Professor, Course, Enrollment
        
        # Clear existing data
        print("Clearing existing data...")
        Enrollment.query.delete()
        Course.query.delete()
        Student.query.delete()
        Professor.query.delete()
        User.query.delete()
        
        # Create sample users
        print("Creating sample users...")
        
        # Student users
        student1_user = User(
            username='alice',
            email='alice@student.unige.ch',
            password_hash=generate_password_hash('password123')
        )
        student2_user = User(
            username='bob',
            email='bob@student.unige.ch',
            password_hash=generate_password_hash('password123')
        )
        
        # Professor users
        prof1_user = User(
            username='prof_smith',
            email='smith@unige.ch',
            password_hash=generate_password_hash('password123')
        )
        prof2_user = User(
            username='prof_jones',
            email='jones@unige.ch',
            password_hash=generate_password_hash('password123')
        )
        
        db.session.add_all([student1_user, student2_user, prof1_user, prof2_user])
        db.session.commit()
        
        # Create student profiles
        print("Creating student profiles...")
        student1 = Student(
            user_id=student1_user.id,
            first_name='Alice',
            last_name='Johnson',
            matricule='STU001'
        )
        student2 = Student(
            user_id=student2_user.id,
            first_name='Bob',
            last_name='Smith',
            matricule='STU002'
        )
        
        db.session.add_all([student1, student2])
        db.session.commit()
        
        # Create professor profiles
        print("Creating professor profiles...")
        prof1 = Professor(
            user_id=prof1_user.id,
            first_name='John',
            last_name='Smith',
            department='Computer Science'
        )
        prof2 = Professor(
            user_id=prof2_user.id,
            first_name='Jane',
            last_name='Jones',
            department='Mathematics'
        )
        
        db.session.add_all([prof1, prof2])
        db.session.commit()
        
        # Create courses
        print("Creating sample courses...")
        course1 = Course(
            code='CS101',
            name='Introduction to Programming',
            description='Learn the fundamentals of programming using Python',
            credits=6,
            professor_id=prof1.id,
            day_of_week='Monday',
            start_time='10:00',
            end_time='12:00',
            semester='Fall 2025'
        )
        course2 = Course(
            code='CS201',
            name='Data Structures',
            description='Advanced data structures and algorithms',
            credits=6,
            professor_id=prof1.id,
            day_of_week='Wednesday',
            start_time='14:00',
            end_time='16:00',
            semester='Fall 2025'
        )
        course3 = Course(
            code='MATH101',
            name='Calculus I',
            description='Differential and integral calculus',
            credits=6,
            professor_id=prof2.id,
            day_of_week='Tuesday',
            start_time='08:00',
            end_time='10:00',
            semester='Fall 2025'
        )
        course4 = Course(
            code='MATH201',
            name='Linear Algebra',
            description='Vectors, matrices, and linear transformations',
            credits=6,
            professor_id=prof2.id,
            day_of_week='Thursday',
            start_time='10:00',
            end_time='12:00',
            semester='Fall 2025'
        )
        
        db.session.add_all([course1, course2, course3, course4])
        db.session.commit()
        
        # Create enrollments with some completed with feedback
        print("Creating sample enrollments...")
        from datetime import timedelta
        
        # Alice's enrollments
        enrollment1 = Enrollment(
            student_id=student1.id,
            course_id=course1.id,
            status='completed',
            weekly_hours=8,
            student_grade=16.5,
            completion_date=datetime.utcnow() - timedelta(days=30)
        )
        enrollment2 = Enrollment(
            student_id=student1.id,
            course_id=course3.id,
            status='enrolled'
        )
        
        # Bob's enrollments
        enrollment3 = Enrollment(
            student_id=student2.id,
            course_id=course1.id,
            status='completed',
            weekly_hours=12,
            student_grade=14.0,
            completion_date=datetime.utcnow() - timedelta(days=25)
        )
        enrollment4 = Enrollment(
            student_id=student2.id,
            course_id=course2.id,
            status='enrolled'
        )
        
        db.session.add_all([enrollment1, enrollment2, enrollment3, enrollment4])
        db.session.commit()
        
        print("\n✓ Database seeded successfully!")
        print("\nSample credentials:")
        print("  Students: alice/bob (password: password123)")
        print("  Professors: prof_smith/prof_jones (password: password123)")
    def _hour_to_str(h):
        if h is None:
            return None
        try:
            return f"{int(h):02d}:00"
        except (ValueError, TypeError):
            return None

    def _credits_to_int(c):
        if c is None:
            return 0
        try:
            return int(round(float(c)))
        except (ValueError, TypeError):
            return 0

    def _build_description(course_obj: dict):
        parts = []
        if course_obj.get("objective"):
            parts.append(str(course_obj["objective"]).strip())
        if course_obj.get("description"):
            parts.append(str(course_obj["description"]).strip())
        txt = "\n\n".join([p for p in parts if p])
        return txt or None

    @app.cli.command("seed-from-json")
    @click.argument("json_path")
    @click.option("--password", "default_password", default="ChangeMe123!", show_default=True)
    def seed_from_json_cmd(json_path, default_password):
        """Seed Users+Professors puis Courses depuis un courses.json"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_courses = data.get("courses", [])
        if not isinstance(raw_courses, list):
            raise ValueError("JSON invalide: la clé 'courses' doit être une liste.")

        now = datetime.utcnow()

        # 1) Préparer les profs
        prof_payload_by_person_id = {}
        for c in raw_courses:
            person_id = c.get("personId")
            if not person_id or not str(person_id).isdigit():
                continue
            person_id = int(person_id)

            if person_id not in prof_payload_by_person_id:
                prof_payload_by_person_id[person_id] = {
                    "first_name": (c.get("displayFirstName") or "Unknown").strip() or "Unknown",
                    "last_name": (c.get("displayLastName") or "Unknown").strip() or "Unknown",
                    "department": (c.get("facultyLabel") or "Unknown").strip() or "Unknown",
                }

        # Placeholder
        PLACEHOLDER_PERSON_ID = 0
        prof_payload_by_person_id.setdefault(PLACEHOLDER_PERSON_ID, {
            "first_name": "TBD",
            "last_name": "TBD",
            "department": "Unknown",
        })

        # 2) Créer Users + Professors
        created_users = seen_users = 0
        created_profs = updated_profs = 0
        professor_by_person_id = {}

        for person_id, p in prof_payload_by_person_id.items():
            username = f"prof_{person_id}"
            email = f"{username}@unige.local"

            user = User.query.filter((User.username == username) | (User.email == email)).first()
            if user is None:
                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(default_password),
                    created_at=now,
                )
                db.session.add(user)
                db.session.flush()
                created_users += 1
            else:
                seen_users += 1

            prof = Professor.query.filter_by(user_id=user.id).first()
            if prof is None:
                prof = Professor(
                    user_id=user.id,
                    first_name=p["first_name"],
                    last_name=p["last_name"],
                    department=p["department"],
                )
                db.session.add(prof)
                created_profs += 1
            else:
                prof.first_name = p["first_name"]
                prof.last_name = p["last_name"]
                prof.department = p["department"]
                updated_profs += 1

            professor_by_person_id[person_id] = prof

        db.session.commit()

        placeholder_prof = professor_by_person_id[PLACEHOLDER_PERSON_ID]

        # 3) Courses
        inserted_courses = updated_courses = skipped_courses = 0

        codes = [c.get("code") for c in raw_courses if c.get("code")]
        existing_courses = Course.query.filter(Course.code.in_(codes)).all()
        course_by_code = {cc.code: cc for cc in existing_courses}

        for c in raw_courses:
            code = c.get("code")
            title = c.get("title")
            year = c.get("academicalYear")
            if not code or not title or not year:
                skipped_courses += 1
                continue

            person_id = c.get("personId")
            if person_id and str(person_id).isdigit():
                prof = professor_by_person_id.get(int(person_id), placeholder_prof)
            else:
                prof = placeholder_prof

            payload = {
                "code": str(code)[:20],
                "name": str(title)[:200],
                "description": _build_description(c),
                "credits": _credits_to_int(c.get("credits")),
                "professor_id": prof.id,
                "created_at": now,
                "day_of_week": c.get("day"),
                "start_time": _hour_to_str(c.get("startHour")),
                "end_time": _hour_to_str(c.get("endHour")),
                "semester": c.get("periodicity"),
                "academical_year": str(year)[:10],
            }

            obj = course_by_code.get(payload["code"])
            if obj is None:
                db.session.add(Course(**payload))
                inserted_courses += 1
            else:
                for k, v in payload.items():
                    setattr(obj, k, v)
                updated_courses += 1

        db.session.commit()

        click.echo({
            "users_created": created_users,
            "users_seen": seen_users,
            "professors_created": created_profs,
            "professors_updated": updated_profs,
            "courses_inserted": inserted_courses,
            "courses_updated": updated_courses,
            "courses_skipped": skipped_courses,
            "default_password": default_password,
        })
