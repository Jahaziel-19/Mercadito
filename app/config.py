import os
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Files
    UPLOAD_PRODUCT = 'static/uploads/productos'
    UPLOAD_USER = 'static/uploads/user'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    CARROUSEL = 'static/carrusel'
        
    # Mail config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS= True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Colors
    COLOR1 = "004454"
    COLOR2 = "027373"
    COLOR3 = "F2A71B"
    COLOR4 = "FFFFFF"
