from .extensions import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Numeric


class User(db.Model, UserMixin):
    """Base user model for authentication"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    professor = db.relationship('Professor', backref='user', uselist=False, cascade='all, delete-orphan')
    
    @property
    def role(self):
        """Determine user role based on relationships"""
        if self.student:
            return 'student'
        elif self.professor:
            return 'professor'
        return 'user'
    
    def __repr__(self):
        return f'<User {self.username}>'


class Student(db.Model):
    """Student profile extending User"""
    __tablename__ = 'student'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    matricule = db.Column(db.String(50), unique=True, nullable=False)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def __repr__(self):
        return f'<Student {self.matricule} - {self.full_name}>'


class Professor(db.Model):
    """Professor profile extending User"""
    __tablename__ = 'professor'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    
    # Relationships
    courses = db.relationship('Course', backref='professor', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def __repr__(self):
        return f'<Professor {self.full_name} - {self.department}>'


class Faculty(db.Model):
    __tablename__ = "faculty"
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(20), unique=True, nullable=False)  # ex: "23"
    name = db.Column(db.String(200), nullable=False)

    courses = db.relationship("Course", backref="faculty", lazy=True)



class StudyPlan(db.Model):
    __tablename__ = "study_plan"
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(50), unique=True, nullable=True)
    label = db.Column(db.String(255), nullable=False)
    courses = db.relationship("CourseStudyPlan", back_populates="study_plan", cascade="all, delete-orphan")


class CourseStudyPlan(db.Model):
    __tablename__ = "course_study_plan"
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), primary_key=True)
    study_plan_id = db.Column(db.Integer, db.ForeignKey("study_plan.id"), primary_key=True)

    # Course Credits in this Study Plan
    plan_credits = db.Column(Numeric(4, 1), nullable=True)

    course = db.relationship("Course", back_populates="study_plans")
    study_plan = db.relationship("StudyPlan", back_populates="courses")


class Course(db.Model):
    """Course model"""
    __tablename__ = 'course'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer, nullable=False, default=3)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Schedule information
    day_of_week = db.Column(db.String(20))  # e.g., "Monday", "Tuesday"
    start_time = db.Column(db.String(10))  # e.g., "10:00"
    end_time = db.Column(db.String(10))  # e.g., "12:00"
    semester = db.Column(db.String(20))  # e.g., "Fall"
    academical_year = db.Column(db.String(10)) # e.g., "2022"
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    
    # Study Plan informations
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=True)
    study_plans = db.relationship("CourseStudyPlan", back_populates="course", cascade="all, delete-orphan")
    
    @property
    def enrolled_count(self):
        return len([e for e in self.enrollments if e.status == 'enrolled'])
    
    @property
    def average_hours(self):
        """Average weekly hours from student feedback"""
        completed = [e for e in self.enrollments if e.status == 'completed' and e.weekly_hours]
        return round(sum(e.weekly_hours for e in completed) / len(completed), 1) if completed else None
    
    @property
    def average_grade(self):
        """Average grade from student feedback"""
        completed = [e for e in self.enrollments if e.status == 'completed' and e.student_grade is not None]
        return round(sum(e.student_grade for e in completed) / len(completed), 1) if completed else None
    
    @property
    def difficulty_rating(self):
        """Difficulty rating based on hours (1-5 scale)"""
        avg_hours = self.average_hours
        if not avg_hours:
            return None
        # 0-5h = 1, 5-10h = 2, 10-15h = 3, 15-20h = 4, 20+h = 5
        if avg_hours < 5:
            return 1
        elif avg_hours < 10:
            return 2
        elif avg_hours < 15:
            return 3
        elif avg_hours < 20:
            return 4
        else:
            return 5
    
    @property
    def feedback_count(self):
        """Number of students who provided feedback"""
        return len([e for e in self.enrollments if e.status == 'completed'])
    
    def __repr__(self):
        return f'<Course {self.code} - {self.name}>'


class Enrollment(db.Model):
    """Enrollment model - many-to-many relationship between Student and Course"""
    __tablename__ = 'enrollment'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Status and feedback fields
    status = db.Column(db.String(20), default='enrolled')  # enrolled, completed, dropped, failed
    weekly_hours = db.Column(db.Integer, nullable=True)  # Student-reported weekly hours
    completion_date = db.Column(db.DateTime, nullable=True)  # When course was completed
    student_grade = db.Column(db.Float, nullable=True)  # Student's self-reported grade (0-20)
    grade = db.Column(db.Float, nullable=True)  # Professor-assigned grade (0-20 scale)
    
    # Ensure a student can only enroll once per course
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='unique_student_course'),
    )
    
    def __repr__(self):
        return f'<Enrollment Student:{self.student_id} Course:{self.course_id} Status:{self.status}>'


class Activity(db.Model):
    __tablename__ = "activity"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)         # ex: "Tennis", "Révisions", "Job"
    description = db.Column(db.Text, nullable=True)

    day_of_week = db.Column(db.String(20), nullable=False)    # "Monday", ...
    start_time = db.Column(db.String(10), nullable=False)     # "18:00"
    end_time = db.Column(db.String(10), nullable=False)       # "19:00"

    semester = db.Column(db.String(20), nullable=True)        # optionnel si tu veux filtrer
    academical_year = db.Column(db.String(10), nullable=True) # optionnel aussi

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("activities", lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Activity {self.title} {self.day_of_week} {self.start_time}-{self.end_time}>"


class Event(db.Model):
    """Social event model - users can create and join events"""
    __tablename__ = 'event'
    
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Basic info
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='other')  # sport, study, social, gaming, food, creative, other
    
    # Schedule
    day_of_week = db.Column(db.String(20), nullable=False)  # e.g., "Lundi"
    start_time = db.Column(db.String(10), nullable=False)  # e.g., "18:00"
    end_time = db.Column(db.String(10), nullable=False)  # e.g., "20:00"
    event_date = db.Column(db.Date, nullable=True)  # For one-time events
    
    # Details
    location = db.Column(db.String(200))
    max_participants = db.Column(db.Integer)  # null = unlimited
    is_public = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_events')
    participants = db.relationship('EventParticipant', back_populates='event', cascade='all, delete-orphan')
    
    @property
    def participant_count(self):
        return len(self.participants)
    
    @property
    def is_full(self):
        if self.max_participants is None:
            return False
        return self.participant_count >= self.max_participants
    
    @property  
    def category_emoji(self):
        emojis = {
            'study': '📚',
            'sport': '⚽',
            'social': '🎉',
            'gaming': '🎮',
            'food': '🍕',
            'creative': '🎨',
            'other': '💼'
        }
        return emojis.get(self.category, '💼')
    
    def __repr__(self):
        return f"<Event {self.title} {self.day_of_week} {self.start_time}-{self.end_time}>"


class EventParticipant(db.Model):
    """Event participation - many-to-many relationship between User and Event"""
    __tablename__ = 'event_participant'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event', back_populates='participants')
    user = db.relationship('User', backref='event_participations')
    
    # Ensure a user can only join an event once
    __table_args__ = (
        db.UniqueConstraint('event_id', 'user_id', name='unique_event_user'),
    )
    
    def __repr__(self):
        return f"<EventParticipant User:{self.user_id} Event:{self.event_id}>"
