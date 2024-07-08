from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
#from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SqlEnum, ForeignKey, Integer, String, Column
#from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.String, primary_key=True, unique=True) # Matricula
    nombre = db.Column(db.String(150), nullable=False)
    apellido_paterno = db.Column(db.String(150), nullable=False)
    apellido_materno = db.Column(db.String(150), nullable=False)
    carrera = db.Column(db.String())
    foto_perfil = Column(String(255), default='static/default_profile_pic.png')
    password_hash = db.Column(db.String(255), nullable=False)  # Campo para almacenar la contraseña encriptada
    email = Column(String(255), unique=True, nullable=False)
    rol = Column(String(255), nullable=False, default='USER')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.id

class Admin(db.Model, UserMixin):
    id = db.Column(db.String, primary_key=True, unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    carrera = db.Column(db.String())
    foto_perfil = Column(String(255), default='static/default_profile_pic.png')
    password_hash = db.Column(db.String(255), nullable=False)  # Campo para almacenar la contraseña encriptada
    email = Column(String(255), unique=True, nullable=False)
    rol = Column(String(255), nullable=False, default='ADMIN')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.id

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    nombre_producto = db.Column(db.String, nullable=False)
    descripcion = db.Column(db.String)
    #cantidad = db.Column(db.Integer, nullable=False) # Si es que se requiere inventario
    precio = db.Column(db.Integer, nullable=False)
    carrera = db.Column(db.String, nullable=False)
    imagen_producto = Column(String(255), default='static/uploads/icon-box.png')
    
    def get_next_id():
        last_product = Producto.query.order_by(Producto.id.desc()).first()
        if last_product and last_product.id >= 100:
            return last_product.id + 1
        return 100

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    id_producto = db.Column(db.Integer, nullable=False)
    id_user = db.Column(db.String, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    sub_total = db.Column(db.Integer, nullable=False)
    notas = db.Column(db.String)

class Carrera(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    nombre = db.Column(db.String, nullable=False)