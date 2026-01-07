from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from . import auth_bp
from ..extensions import db, login_manager
from ..models import User, Student, Professor

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Bienvenue {user.username}!", "success")
            return redirect(url_for("main.menu"))
        else:
            flash("Identifiants invalides", "error")

    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            # Get common fields
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            role = request.form.get("role")  # 'student' or 'professor'
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            
            # Validate common fields
            if not all([username, email, password, role, first_name, last_name]):
                flash("Tous les champs sont requis", "warning")
                return redirect(url_for("auth.register"))
            
            # Check if username or email already exists
            if User.query.filter((User.username == username) | (User.email == email)).first():
                flash("Nom d'utilisateur ou email déjà utilisé", "warning")
                return redirect(url_for("auth.register"))
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.flush()  # Get user.id without committing
            
            # Create role-specific profile
            if role == 'student':
                matricule = request.form.get("matricule")
                if not matricule:
                    flash("Le matricule est requis pour les étudiants", "warning")
                    db.session.rollback()
                    return redirect(url_for("auth.register"))
                
                # Check if matricule already exists
                if Student.query.filter_by(matricule=matricule).first():
                    flash("Ce matricule est déjà utilisé", "warning")
                    db.session.rollback()
                    return redirect(url_for("auth.register"))
                
                student = Student(
                    user_id=user.id,
                    first_name=first_name,
                    last_name=last_name,
                    matricule=matricule
                )
                db.session.add(student)
                
            elif role == 'professor':
                department = request.form.get("department")
                if not department:
                    flash("Le département est requis pour les professeurs", "warning")
                    db.session.rollback()
                    return redirect(url_for("auth.register"))
                
                professor = Professor(
                    user_id=user.id,
                    first_name=first_name,
                    last_name=last_name,
                    department=department
                )
                db.session.add(professor)
            else:
                flash("Rôle invalide", "error")
                db.session.rollback()
                return redirect(url_for("auth.register"))
            
            db.session.commit()
            flash(f"Compte créé avec succès! Bienvenue {first_name}!", "success")
            return redirect(url_for("auth.login"))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création du compte: {str(e)}", "error")
            return redirect(url_for("auth.register"))

    return render_template("auth/register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté", "info")
    return redirect(url_for("main.menu"))
