import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_PRODUCT = 'static/uploads/productos'
    UPLOAD_USER = 'static/uploads/user'