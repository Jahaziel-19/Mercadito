from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, current_user, login_required
from models import Admin, db, RolEnum, Pedido, Producto, PedidoProducto, Carrito
from werkzeug.security import generate_password_hash, check_password_hash
from scripts import verificar_correo_existente, roles_required
import math

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

@admin_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        id = request.form['id']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
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
            apellido_paterno=apellido_paterno.upper(),
            apellido_materno=apellido_materno.upper(),
            email=email,
            password_hash=password,
            #foto_perfil=foto_path
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return redirect(url_for('admin.login'))

    return render_template('admin/registro.html')

@admin_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        usuario = Admin.query.filter_by(email=correo).first()

        if usuario and check_password_hash(usuario.password_hash, contraseña):
            login_user(usuario)
            return redirect(url_for('index')) # Aquí puedes redirigir al panel de administración
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

    # Paginación
    page_abiertos = request.args.get('page_abiertos', 1, type=int)
    page_cerrados = request.args.get('page_cerrados', 1, type=int)
    per_page = 10  # Elementos por página

    # Obtener productos disponibles para el admin
    productos = Producto.query.filter_by(carrera=current_user.carrera).all()

    # Pedidos Abiertos
    pedidos_abiertos_query = db.session.query(Pedido).filter(Pedido.estatus != 'cerrado')
    pedidos_abiertos = pedidos_abiertos_query.paginate(page=page_abiertos, per_page=per_page)
    productos_pedidos = []
    for pedido in pedidos_abiertos.items:
        productos_asociados = PedidoProducto.query.filter_by(
            id_pedido=pedido.id,
            carrera=current_user.carrera  # Asegurar que los productos sean de la misma carrera
        ).all()

        if productos_asociados:  # Solo incluir pedidos con productos de la misma carrera
            productos_pedidos.append((pedido, productos_asociados))

    total_pages_abiertos = math.ceil(pedidos_abiertos_query.count() / per_page)

    # Pedidos Cerrados
    pedidos_cerrados_query = db.session.query(Pedido).filter(Pedido.estatus == 'cerrado')
    pedidos_cerrados = pedidos_cerrados_query.paginate(page=page_cerrados, per_page=per_page)
    productos_pedidos_cerrados = []
    for pedido in pedidos_cerrados.items:
        productos_asociados = PedidoProducto.query.filter(
            PedidoProducto.id_pedido == pedido.id,
            PedidoProducto.carrera == current_user.carrera  # Filtrar también por carrera
        ).all()

        # Si hay productos asociados, agregar el pedido y sus productos
        if productos_asociados:
            productos_pedidos_cerrados.append((pedido, productos_asociados))

    total_pages_cerrados = math.ceil(pedidos_cerrados_query.count() / per_page)

    # Obtener carrito del admin (si aplica)
    carrito = db.session.query(Carrito, Producto).join(
        Producto, Carrito.id_producto == Producto.id
    ).filter(
        Carrito.id_usuario == current_user.id
    ).all()

    return render_template(
        'perfil_admin.html',  # Asegúrate de que la ruta sea correcta
        productos=productos,
        productos_pedidos=productos_pedidos,
        productos_pedidos_cerrados=productos_pedidos_cerrados,
        carrito=carrito,
        estatus=estatus,
        current_page_abiertos=page_abiertos,
        total_pages_abiertos=total_pages_abiertos,
        current_page_cerrados=page_cerrados,
        total_pages_cerrados=total_pages_cerrados
    )