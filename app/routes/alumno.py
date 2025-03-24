from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, current_user, login_required
from models import Alumno, db, Carrito, Producto, Pedido, PedidoProducto, Carrera
from werkzeug.security import generate_password_hash, check_password_hash
from scripts import verificar_correo_existente
from werkzeug.utils import secure_filename
import os

alumno_bp = Blueprint('alumno', __name__, template_folder='../templates/alumno')

@alumno_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        id = request.form['id']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        carrera = request.form['carrera']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        foto_perfil = request.files['foto_perfil']

        if verificar_correo_existente(email):
            flash('Este correo ya está registrado en la plataforma. Por favor, usa otro correo.', category='danger')
            return redirect(url_for('alumno.registro_alumno'))

        if foto_perfil and foto_perfil.filename != '':
            filename = secure_filename(foto_perfil.filename)
            foto_perfil.save(os.path.join(current_app.config['UPLOAD_USER'], filename))
            foto_path = os.path.join(current_app.config['UPLOAD_USER'], filename)
        else:
            foto_path = 'static/default_profile_pic.png'

        nuevo_usuario = Alumno(
            id=id,
            nombre=nombre.upper(),
            apellido_paterno=apellido_paterno.upper(),
            apellido_materno=apellido_materno.upper(),
            carrera=carrera.upper(),
            email=email,
            password_hash=password,
            foto_perfil=foto_path
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return redirect(url_for('alumno.login'))

    carreras = Carrera.query.all()
    return render_template('registro_alumno.html', carreras=carreras)

@alumno_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        usuario = Alumno.query.filter_by(email=correo).first()

        if usuario and check_password_hash(usuario.password_hash, contraseña):
            login_user(usuario)
            return redirect(url_for('productos.productos_servicios'))
        else:
            flash('Usuario o contraseña incorrectos')
            return render_template('login.html')
    return render_template('login.html')

@alumno_bp.route('/perfil', methods=['POST', 'GET'])
@login_required
def perfil():
    if current_user.rol != 'ALUMNO':
        flash('No tienes permiso para acceder a este perfil', category='danger')
        return redirect(url_for('index'))

    # Obtener pedidos del alumno
    pedidos = db.session.query(Pedido).filter(Pedido.id_usuario == current_user.id).all()

    # Obtener productos asociados al alumno
    productos_pedidos = []
    for pedido in pedidos:
        productos = PedidoProducto.query.filter_by(id_pedido=pedido.id).all()
        productos_pedidos.append((pedido, productos))

    # Obtener carrito del alumno
    carrito = db.session.query(Carrito, Producto).join(Producto, Carrito.id_producto == Producto.id).filter(
        Carrito.id_usuario == current_user.id).all()

    return render_template('perfil_alumno.html', carrito=carrito, productos_pedidos=productos_pedidos)
