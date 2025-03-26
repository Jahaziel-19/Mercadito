from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, current_user, login_required
from models import Admin, db, Docente, Alumno, Invitado, RolEnum, Pedido, Producto, PedidoProducto, Carrito, Carrera
from werkzeug.security import generate_password_hash, check_password_hash
from scripts import verificar_correo_existente, roles_required
import math

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

@admin_bp.route('/registro', methods=['GET', 'POST'])
@login_required
def registro():
    carreras = Carrera.query.all()
    if request.method == 'POST':
        id = request.form['id']
        nombre = request.form['nombre']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        #foto_perfil = request.files['foto_perfil']
        #foto_path = 'static/default_profile_pic.png'

        if verificar_correo_existente(email):
            flash('Este correo ya está registrado en la plataforma. Por favor, usa otro correo.', category='danger')
            return redirect(url_for('admin.registro'))

        nuevo_usuario = Admin(
            id=id,
            nombre=nombre.upper(),
            email=email,
            password_hash=password,
            #foto_perfil=foto_path
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return redirect(url_for('admin.login'))

    return render_template('admin/registro_admin.html', carreras=carreras)

@admin_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        usuario = Admin.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password_hash, password):
            login_user(usuario)
            return redirect(url_for('admin.perfil')) # Aquí puedes redirigir al panel de administración
        else:
            flash('Usuario o contraseña incorrectos', category="danger")
            return render_template('login_admin.html')
    return render_template('login_admin.html')

@admin_bp.route('/perfil', methods=['POST', 'GET'])
@login_required
@roles_required(RolEnum.ADMIN.value)
def perfil():
    if current_user.rol != 'ADMIN':
        return redirect(url_for('index'))
    
    estatus = {
        'abierto': 'bg-warning',
        'recibido': 'bg-success',
        'cancelado': 'bg-danger',
        'cerrado': 'bg-primary'
    }

    # Obtener productos disponibles para el admin
    productos = Producto.query.filter_by(carrera=current_user.carrera).all()

    # Obtener pedidos cerrados relacionados con la carrera del admin, incluyendo el nombre del usuario
    pedidos_cerrados = db.session.query(Pedido).options(
        joinedload(Pedido.productos)  # Carga los productos en la consulta
    ).filter(Pedido.estatus == 'cerrado').all()

    productos_pedidos_cerrados = []
    for pedido in pedidos_cerrados:
        productos_asociados = PedidoProducto.query.filter_by(
            id_pedido=pedido.id,
            carrera=current_user.carrera  
        ).all()

        if productos_asociados:
            # Obtener el usuario del pedido
            usuario = (
                Admin.query.get(pedido.id_usuario) or
                Docente.query.get(pedido.id_usuario) or
                Alumno.query.get(pedido.id_usuario) or
                Invitado.query.get(pedido.id_usuario)
            )
            pedido.nombre_usuario = f"{usuario.nombre} {usuario.apellido_paterno} {usuario.apellido_materno}" if usuario else "Desconocido"
            productos_pedidos_cerrados.append((pedido, productos_asociados))

    return render_template(
        'perfil_admin.html',
        productos=productos,
        productos_pedidos_cerrados=productos_pedidos_cerrados,
        estatus=estatus
    )
