from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import datetime

from . import courses_bp
from ..extensions import db
from ..models import Course, Faculty, StudyPlan, CourseStudyPlan, Professor, Student, Enrollment, Activity


@courses_bp.route('/')
def catalog():
    q = (request.args.get("q") or "").strip()
    faculty_ext = (request.args.get("faculty") or "").strip()  # ex: "23"
    plan_ext = (request.args.get("plan") or "").strip()        # ex: studyPlanGroupId
    plan_id = request.args.get("plan_id", type=int)            # option alternative
    sort = (request.args.get("sort") or "code").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 25

    query = Course.query

    # Filtre faculté (par external_id)
    if faculty_ext:
        query = query.join(Faculty).filter(Faculty.external_id == faculty_ext)

    # Filtre plan d’étude
    if plan_id:
        query = query.join(CourseStudyPlan).filter(CourseStudyPlan.study_plan_id == plan_id)
    elif plan_ext:
        query = query.join(CourseStudyPlan).join(StudyPlan).filter(StudyPlan.external_id == plan_ext)

    # Recherche code/nom
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Course.code.ilike(like), Course.name.ilike(like)))

    # Tri
    if sort == "name":
        query = query.order_by(Course.name.asc())
    elif sort == "credits":
        query = query.order_by(Course.credits.desc(), Course.code.asc())
    else:
        query = query.order_by(Course.code.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # pour remplir les dropdowns
    faculties = Faculty.query.order_by(Faculty.name.asc()).all()
    plans = StudyPlan.query.order_by(StudyPlan.label.asc()).all()

    return render_template(
        "courses/catalog.html",
        courses=pagination.items,
        pagination=pagination,
        faculties=faculties,
        plans=plans,
        filters={
            "q": q,
            "faculty": faculty_ext,
            "plan": plan_ext,
            "plan_id": plan_id,
            "sort": sort,
        }
    )


@courses_bp.route('/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    is_enrolled = False
    if current_user.is_authenticated and current_user.student:
        is_enrolled = Enrollment.query.filter_by(student_id=current_user.student.id, course_id=course_id).first() is not None
    return render_template('courses/detail.html', course=course, is_enrolled=is_enrolled)


@courses_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_course():
    if not current_user.professor:
        flash('Seuls les professeurs peuvent créer des cours', 'error')
        return redirect(url_for('courses.list_courses'))
    if request.method == 'POST':
        try:
            code = request.form.get('code')
            name = request.form.get('name')
            description = request.form.get('description')
            credits = request.form.get('credits', type=int)
            if not all([code, name, credits]):
                flash('Code, nom et crédits sont requis', 'warning')
                return redirect(url_for('courses.create_course'))
            if Course.query.filter_by(code=code).first():
                flash('Un cours avec ce code existe déjà', 'warning')
                return redirect(url_for('courses.create_course'))
            course = Course(code=code, name=name, description=description, credits=credits, professor_id=current_user.professor.id)
            db.session.add(course)
            db.session.commit()
            flash(f'Cours {name} créé avec succès!', 'success')
            return redirect(url_for('courses.course_detail', course_id=course.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création: {str(e)}', 'error')
            return redirect(url_for('courses.create_course'))
    return render_template('courses/create.html')


@courses_bp.route('/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    if not current_user.student:
        flash('Seuls les étudiants peuvent s inscrire aux cours', 'error')
        return redirect(url_for('courses.course_detail', course_id=course_id))
    course = Course.query.get_or_404(course_id)
    existing = Enrollment.query.filter_by(student_id=current_user.student.id, course_id=course_id).first()
    if existing:
        flash('Vous êtes déjà inscrit à ce cours', 'warning')
        return redirect(url_for('courses.course_detail', course_id=course_id))
    try:
        enrollment = Enrollment(student_id=current_user.student.id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        flash(f'Inscription réussie au cours {course.name}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l inscription: {str(e)}', 'error')
    return redirect(url_for('courses.course_detail', course_id=course_id))


@courses_bp.route('/<int:course_id>/unenroll', methods=['POST'])
@login_required
def unenroll(course_id):
    if not current_user.student:
        flash('Action non autorisée', 'error')
        return redirect(url_for('courses.course_detail', course_id=course_id))
    enrollment = Enrollment.query.filter_by(student_id=current_user.student.id, course_id=course_id).first()
    if not enrollment:
        flash('Vous n êtes pas inscrit à ce cours', 'warning')
        return redirect(url_for('courses.course_detail', course_id=course_id))
    try:
        course_name = enrollment.course.name
        db.session.delete(enrollment)
        db.session.commit()
        flash(f'Désinscription du cours {course_name} réussie', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la désinscription: {str(e)}', 'error')
    return redirect(url_for('courses.list_courses'))


@courses_bp.route('/my-courses')
@login_required
def my_courses():
    if current_user.student:
        enrollments = current_user.student.enrollments
        return render_template('courses/my_enrollments.html', enrollments=enrollments)
    elif current_user.professor:
        courses = current_user.professor.courses
        return render_template('courses/my_courses.html', courses=courses)
    else:
        flash('Profil incomplet', 'warning')
        return redirect(url_for('main.menu'))


@courses_bp.route('/planning')
@login_required
def planning():
    if not current_user.student:
        flash('Cette page est réservée aux étudiants', 'error')
        return redirect(url_for('main.menu'))

    days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi']
    schedule = {day: [] for day in days}

    # 1) Cours de l'étudiant
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.student.id,
        status='enrolled'
    ).all()

    for e in enrollments:
        c = e.course
        if c.day_of_week and c.day_of_week in schedule:
            schedule[c.day_of_week].append({
                "kind": "course",
                "id": c.id,
                "code": c.code,
                "title": c.name,
                "start": c.start_time,
                "end": c.end_time,
            })

    # 2) Activités perso (liées au User)
    activities = Activity.query.filter_by(user_id=current_user.id).all()

    for a in activities:
        if a.day_of_week and a.day_of_week in schedule:
            schedule[a.day_of_week].append({
                "kind": "activity",
                "id": a.id,
                "code": None,
                "title": a.title,
                "start": a.start_time,
                "end": a.end_time,
            })

    # Tri par heure de début
    def _time_key(item):
        return item["start"] or "99:99"

    for day in days:
        schedule[day].sort(key=_time_key)

    return render_template('courses/planning.html', schedule=schedule, days=days)


@courses_bp.route('/<int:course_id>/feedback', methods=['GET', 'POST'])
@login_required
def submit_feedback(course_id):
    if not current_user.student:
        flash('Seuls les étudiants peuvent soumettre des avis', 'error')
        return redirect(url_for('courses.course_detail', course_id=course_id))
    enrollment = Enrollment.query.filter_by(student_id=current_user.student.id, course_id=course_id).first()
    if not enrollment:
        flash('Vous devez être inscrit à ce cours', 'warning')
        return redirect(url_for('courses.course_detail', course_id=course_id))
    if request.method == 'POST':
        try:
            status = request.form.get('status')
            weekly_hours = request.form.get('weekly_hours', type=int)
            student_grade = request.form.get('student_grade', type=float)
            if not status:
                flash('Veuillez sélectionner un statut', 'warning')
                return redirect(url_for('courses.submit_feedback', course_id=course_id))
            enrollment.status = status
            if status == 'completed':
                if weekly_hours and student_grade is not None:
                    enrollment.weekly_hours = min(weekly_hours, 40)
                    enrollment.student_grade = student_grade
                    enrollment.completion_date = datetime.utcnow()
                else:
                    flash('Veuillez renseigner les heures hebdomadaires et votre note', 'warning')
                    return redirect(url_for('courses.submit_feedback', course_id=course_id))
            db.session.commit()
            flash('Merci pour votre retour!', 'success')
            return redirect(url_for('courses.my_courses'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'error')
            return redirect(url_for('courses.submit_feedback', course_id=course_id))
    course = enrollment.course
    return render_template('courses/feedback.html', enrollment=enrollment, course=course)


@courses_bp.route("/activities/new", methods=["GET"])
@login_required
def new_activity():
    return render_template("courses/activity_new.html")

@courses_bp.route("/activities/create", methods=["POST"])
@login_required
def create_activity():
    title = (request.form.get("title") or "").strip()
    day = (request.form.get("day_of_week") or "").strip()
    start = (request.form.get("start_time") or "").strip()
    end = (request.form.get("end_time") or "").strip()

    if not title or not day or not start or not end:
        flash("Merci de remplir tous les champs.", "error")
        return redirect(url_for("courses.new_activity"))

    a = Activity(user_id=current_user.id, title=title, day_of_week=day, start_time=start, end_time=end)
    db.session.add(a)
    db.session.commit()

    flash("Activité ajoutée !", "success")
    return redirect(url_for("courses.planning"))