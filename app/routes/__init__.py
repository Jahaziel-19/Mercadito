from flask import Flask

from .invitado import invitado_bp
from .docente import docente_bp
from .alumno import alumno_bp
from .admin import admin_bp
from .productos import productos_bp
from .carrito import carrito_bp
from .pedidos import pedidos_bp

def register_blueprints(app: Flask):
    app.register_blueprint(invitado_bp, url_prefix='/invitado')
    app.register_blueprint(docente_bp, url_prefix='/docente')
    app.register_blueprint(alumno_bp, url_prefix='/alumno')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(productos_bp, url_prefix='/productos')
    app.register_blueprint(carrito_bp, url_prefix='/carrito')
    app.register_blueprint(pedidos_bp, url_prefix='/pedidos')
