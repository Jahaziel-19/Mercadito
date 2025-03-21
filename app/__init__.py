from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# Extensiones globales
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    with app.app_context():
        from .routes import register_blueprints
        register_blueprints(app)

        db.create_all()  # Crear tablas si no existen

    return app

@login_manager.user_loader
def load_user(user_id):
    from models import Invitado, Alumno, Docente, Admin  # Importar modelos aquí para evitar referencias circulares
    
    for model in [Invitado, Alumno, Docente, Admin]:
        user = model.query.get(user_id)
        if user:
            return user

    return None
