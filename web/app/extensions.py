from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy() # variable for SQLAlchemy
login_manager = LoginManager() # variable for Login_Manager
login_manager.login_view = "auth_login" #login route name