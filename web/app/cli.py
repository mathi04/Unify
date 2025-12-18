from .extensions import db
from werkzeug.security import generate_password_hash
from datetime import datetime

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
