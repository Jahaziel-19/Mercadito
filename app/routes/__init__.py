from flask import Flask
from .invitado import invitado_bp
from .docente import docente_bp
from .alumno import alumno_bp
from .general import general_bp

def register_blueprints(app: Flask):
    app.register_blueprint(general_bp)
    app.register_blueprint(invitado_bp, url_prefix='/invitado')
    app.register_blueprint(docente_bp, url_prefix='/docente')
    app.register_blueprint(alumno_bp, url_prefix='/alumno')
