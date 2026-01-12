import click
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from werkzeug.security import generate_password_hash
from .extensions import db
from .models import User, Professor, Course, Faculty, StudyPlan, CourseStudyPlan


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
    
    DAY_MAP = {
        "Monday": "Lundi",
        "Tuesday": "Mardi",
        "Wednesday": "Mercredi",
        "Thursday": "Jeudi",
        "Friday": "Vendredi",
        "Saturday": "Samedi",
        "Sunday": "Dimanche",
    }

    SEMESTER_MAP = {
        "Automne": "Fall",
        "Printemps": "Spring",
        "Annuel": "Annual",
    }

    def _hour_to_str(h):
        if h is None:
            return None
        try:
            return f"{int(h):02d}:00"
        except (ValueError, TypeError):
            return None

    def _credits_to_int(c):
        # Course.credits est int dans ta DB ; JSON est float.
        if c is None:
            return 0
        try:
            return int(round(float(c)))
        except (ValueError, TypeError):
            return 0

    def _plan_credits_decimal(x):
        # listStudyPlan[].planCredits est string/null dans ton JSON
        if x is None:
            return None
        s = str(x).strip()
        if not s:
            return None
        try:
            return Decimal(s)
        except (InvalidOperation, ValueError):
            return None

    def _build_description(obj: dict):
        parts = []
        if obj.get("objective"):
            parts.append(str(obj["objective"]).strip())
        if obj.get("description"):
            parts.append(str(obj["description"]).strip())
        txt = "\n\n".join([p for p in parts if p])
        return txt or None

    def _normalize_day(day):
        if not day:
            return None
        day = str(day).strip()
        return DAY_MAP.get(day, day)  

    def _normalize_semester(periodicity):
        if not periodicity:
            return None
        p = str(periodicity).strip()
        return SEMESTER_MAP.get(p, p)

    @app.cli.command("seed-from-json")
    @click.argument("json_path")
    @click.option("--password", "default_password", default="ChangeMe123!", show_default=True)
    @click.option("--wipe", is_flag=True, help="Supprime courses + liens + study plans + faculties + profs seed (dangereux).")
    def seed_from_json_cmd(json_path, default_password, wipe):
        """
        Seed complet depuis courses.json:
        - Users+Professors (créés à partir de personId)
        - Faculties (facultyId/Label)
        - StudyPlans (listStudyPlan)
        - Courses
        - CourseStudyPlan avec plan_credits
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_courses = data.get("courses", [])
        if not isinstance(raw_courses, list):
            raise click.ClickException("JSON invalide: 'courses' doit être une liste.")

        now = datetime.utcnow()


        if wipe:
            click.echo("Wiping tables: course_study_plan, course, study_plan, faculty, professor, user(profs only)...")
            CourseStudyPlan.query.delete()
            Course.query.delete()
            StudyPlan.query.delete()
            Faculty.query.delete()
            professors = Professor.query.all()
            prof_user_ids = [p.user_id for p in professors]
            Professor.query.delete()
            if prof_user_ids:
                User.query.filter(User.id.in_(prof_user_ids)).delete(synchronize_session=False)
            db.session.commit()


        prof_payload = {}
        for c in raw_courses:
            pid = c.get("personId")
            if pid and str(pid).isdigit():
                pid = int(pid)
                if pid not in prof_payload:
                    prof_payload[pid] = {
                        "first_name": (c.get("displayFirstName") or "Unknown").strip() or "Unknown",
                        "last_name": (c.get("displayLastName") or "Unknown").strip() or "Unknown",
                        "department": (c.get("facultyLabel") or "Unknown").strip() or "Unknown",
                    }

  
        PLACEHOLDER_PID = 0
        prof_payload.setdefault(PLACEHOLDER_PID, {"first_name": "TBD", "last_name": "TBD", "department": "Unknown"})

        created_users = created_profs = 0
        professor_by_pid = {}

        for pid, p in prof_payload.items():
            username = f"prof_{pid}"
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
                # update soft
                prof.first_name = p["first_name"]
                prof.last_name = p["last_name"]
                prof.department = p["department"]

            professor_by_pid[pid] = prof

        db.session.commit()
        placeholder_prof = professor_by_pid[PLACEHOLDER_PID]

        faculty_by_external = {f.external_id: f for f in Faculty.query.all()}

        studyplan_by_external = {sp.external_id: sp for sp in StudyPlan.query.filter(StudyPlan.external_id.isnot(None)).all()}
        studyplan_by_label = {sp.label: sp for sp in StudyPlan.query.all()}

        inserted_courses = updated_courses = 0
        link_inserted = link_updated = 0

        codes = [c.get("code") for c in raw_courses if c.get("code")]
        existing_courses = Course.query.filter(Course.code.in_(codes)).all()
        course_by_code = {cc.code: cc for cc in existing_courses}

        for c in raw_courses:
            code = c.get("code")
            title = c.get("title")
            if not code or not title:
                continue

            # Faculty
            faculty_ext = str(c.get("facultyId") or "").strip()
            faculty_label = (c.get("facultyLabel") or "").strip()
            faculty_id = None
            if faculty_ext and faculty_label:
                fac = faculty_by_external.get(faculty_ext)
                if fac is None:
                    fac = Faculty(external_id=faculty_ext, name=faculty_label)
                    db.session.add(fac)
                    db.session.flush()
                    faculty_by_external[faculty_ext] = fac
                faculty_id = fac.id

            # Professor
            pid = c.get("personId")
            if pid and str(pid).isdigit():
                prof = professor_by_pid.get(int(pid), placeholder_prof)
            else:
                prof = placeholder_prof

            payload = dict(
                code=str(code)[:20],
                name=str(title)[:200],
                description=_build_description(c),
                credits=_credits_to_int(c.get("credits")),
                professor_id=prof.id,
                created_at=now,
                day_of_week=_normalize_day(c.get("day")),
                start_time=_hour_to_str(c.get("startHour")),
                end_time=_hour_to_str(c.get("endHour")),
                semester=_normalize_semester(c.get("periodicity")),
                academical_year=str(c.get("academicalYear") or "").strip() or None,
                faculty_id=faculty_id,
            )

            obj = course_by_code.get(payload["code"])
            if obj is None:
                obj = Course(**payload)
                db.session.add(obj)
                db.session.flush()  # obj.id pour liens
                course_by_code[obj.code] = obj
                inserted_courses += 1
            else:
                for k, v in payload.items():
                    setattr(obj, k, v)
                db.session.flush()
                updated_courses += 1

            # Associations StudyPlan (listStudyPlan)
            list_plans = c.get("listStudyPlan") or []
            for sp in list_plans:
                ext = sp.get("studyPlanGroupId") or sp.get("studyPlanId")
                ext = str(ext).strip() if ext is not None else None
                label = (sp.get("studyPlanLabel") or "Unknown plan").strip()

                study_plan = None
                if ext:
                    study_plan = studyplan_by_external.get(ext)
                if study_plan is None:
                    study_plan = studyplan_by_label.get(label)

                if study_plan is None:
                    study_plan = StudyPlan(external_id=ext, label=label)
                    db.session.add(study_plan)
                    db.session.flush()
                    if ext:
                        studyplan_by_external[ext] = study_plan
                    studyplan_by_label[label] = study_plan

                assoc = CourseStudyPlan.query.filter_by(course_id=obj.id, study_plan_id=study_plan.id).first()
                if assoc is None:
                    assoc = CourseStudyPlan(
                        course_id=obj.id,
                        study_plan_id=study_plan.id,
                        plan_credits=_plan_credits_decimal(sp.get("planCredits")),
                    )
                    db.session.add(assoc)
                    link_inserted += 1
                else:
                    assoc.plan_credits = _plan_credits_decimal(sp.get("planCredits"))
                    link_updated += 1

        db.session.commit()

        click.echo({
            "users_created": created_users,
            "professors_created": created_profs,
            "courses_inserted": inserted_courses,
            "courses_updated": updated_courses,
            "course_plan_links_inserted": link_inserted,
            "course_plan_links_updated": link_updated,
        })
