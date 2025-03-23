from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum as SqlEnum, ForeignKey, Integer, String, Column
from datetime import datetime
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class RolEnum(enum.Enum):
    ADMIN = "ADMIN"
    DOCENTE = "DOCENTE"
    ALUMNO = "ALUMNO"
    INVITADO = "INVITADO"


class Invitado(db.Model, UserMixin):
    id = db.Column(db.String, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    apellido_paterno = db.Column(db.String(150), nullable=False)
    apellido_materno = db.Column(db.String(150), nullable=False)
    foto_perfil = db.Column(String(255), default='static/default_profile_pic.png')
    password_hash = db.Column(db.String(255), nullable=False)  # Campo para almacenar la contraseña encriptada
    email = Column(String(255), unique=True, nullable=False)
    rol = Column(String(255), nullable=False, default=RolEnum.INVITADO.value)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.id    


class Alumno(db.Model, UserMixin):
    id = db.Column(db.String, primary_key=True, unique=True) # Matricula
    nombre = db.Column(db.String(150), nullable=False)
    apellido_paterno = db.Column(db.String(150), nullable=False)
    apellido_materno = db.Column(db.String(150), nullable=False)
    carrera = db.Column(db.String())
    foto_perfil = Column(String(255), default='static/default_profile_pic.png')
    password_hash = db.Column(db.String(255), nullable=False)  # Campo para almacenar la contraseña encriptada
    email = Column(String(255), unique=True, nullable=False)
    rol = Column(String(255), nullable=False, default='ALUMNO')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.id

class Docente(db.Model, UserMixin):
    id = db.Column(db.String, primary_key=True, unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    apellido_paterno = db.Column(db.String(150), nullable=False)
    apellido_materno = db.Column(db.String(150), nullable=False)
    carrera = db.Column(db.String(150))
    foto_perfil = Column(String(255))
    password_hash = db.Column(db.String(255), nullable=False)  # Campo para almacenar la contraseña encriptada
    email = Column(String(255), unique=True, nullable=False)
    rol = Column(String(255), nullable=False, default=RolEnum.DOCENTE.value)
    encoding = db.Column(db.LargeBinary)  # Almacena el encoding facial

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
    encoding = db.Column(db.LargeBinary)  # Almacena el encoding facial

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
    precio = db.Column(db.Float, nullable=False) # Float
    carrera = db.Column(db.String, nullable=False)
    imagen_producto = Column(String(255), default='static/uploads/icon-box.png')
    medida = db.Column(db.String)
    pedidos = relationship('PedidoProducto', back_populates='producto')
    

class Carrito(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    id_producto = db.Column(db.Integer, nullable=False)
    id_usuario = db.Column(db.String, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    notas = db.Column(db.String)
    total = db.Column(db.Float, nullable=False)    

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    id_usuario = db.Column(db.String, nullable=False)
    total = db.Column(db.Float, nullable=False)  # Total de los productos
    estatus = db.Column(db.String, default="abierto")
    fecha_pedido = db.Column(db.DateTime, default=datetime.utcnow)  # Fecha al hacer el pedido
    
    def to_dict(self):
        return {
            'id':self.id,
            'id_usuario':self.id_usuario,
            'id_usuario_cierre':self.id_usuario_cierre,
            'total':self.total,
            'estatus':self.estatus,
            'fecha_pedido':self.fecha_pedido
        }
    # Relación con los productos del pedido
    productos = relationship('PedidoProducto', back_populates='pedido')

class PedidoProducto(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    id_pedido = db.Column(db.Integer, ForeignKey('pedido.id'), nullable=False)
    id_producto = db.Column(db.Integer, ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    carrera = db.Column(db.String)
    estatus = db.Column(db.String)
    ubicacion = db.Column(db.String)  # Ubicación para recoger el producto
    fecha_recibido = db.Column(db.DateTime)  # Fecha cuando el admin recibe el pedido
    fecha_limite = db.Column(db.DateTime)  # Fecha límite para recoger el producto
    id_usuario_cierre = db.Column(db.String)  # Usuario que da cierre al pedido

    pedido = relationship('Pedido', back_populates='productos')
    producto = relationship('Producto')

    def to_dict(self):
        producto = Producto.query.get(self.id_producto)  # Obtener el producto relacionado
        return {
            'id':self.id,
            'id_pedido':self.id_pedido,
            'id_producto':self.id_producto,
            'nombre_producto':producto.nombre_producto,
            'cantidad':self.cantidad,
            'subtotal':self.subtotal,
            'carrera':self.carrera,
            'estatus':self.estatus,
            'ubicacion':self.ubicacion,
            'fecha_recibido':self.fecha_recibido,
            'fecha_limite':self.fecha_limite
        }



class Carrera(db.Model):
    id = db.Column(db.String, primary_key=True, unique=True)
    nombre = db.Column(db.String, nullable=False)