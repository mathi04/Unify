import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret") #cookie key
    SQLALCHEMY_DATABASE_URI = os.environ.get( 
        "DATABASE_URI",
        "mysql+pymysql://app_user:app_password@db:3306/app_db"
    ) #connection to db information
    SQLALCHEMY_TRACK_MODIFICATIONS = False
