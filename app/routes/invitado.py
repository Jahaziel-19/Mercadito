from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, login_required, logout_user
from models import Invitado, db, Pedido, Carrito, Producto, PedidoProducto
from scripts import verificar_correo_existente
from werkzeug.utils import secure_filename
import os
import random
import string
from flask_mail import Message
from flask import current_app

invitado_bp = Blueprint('invitado', __name__, template_folder='../templates/invitado')

@invitado_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        id = request.form['id']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        email = request.form['email']
        foto_perfil = request.files['foto_perfil']

        if verificar_correo_existente(email):
            flash('Este correo ya está registrado en la plataforma. Por favor, usa otro correo.', category='danger')
            return redirect(url_for('invitado.registro_invitado'))

        if foto_perfil and foto_perfil.filename != '':
            filename = secure_filename(foto_perfil.filename)
            foto_perfil.save(os.path.join(current_app.config['UPLOAD_USER'], filename))
            foto_path = os.path.join(current_app.config['UPLOAD_USER'], filename)
        else:
            foto_path = 'static/default_profile_pic.png'

        # Generar una contraseña aleatoria de 10 caracteres
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        nuevo_invitado = Invitado(
            id=id,
            nombre=nombre.upper(),
            apellido_paterno=apellido_paterno.upper(),
            apellido_materno=apellido_materno.upper(),
            email=email,
            foto_perfil=foto_path
        )

        if not Invitado.query.get(nuevo_invitado.id):
            nuevo_invitado.set_password(password)
            db.session.add(nuevo_invitado)
            db.session.commit()
            # Enviar la contraseña y el link de inicio de sesión al correo electrónico
            msg = Message("Registro exitoso", sender=current_app.config['MAIL_USERNAME'], recipients=[nuevo_invitado.email])
            msg.body = f"Hola {nombre},\n\nTu cuenta de invitado ha sido creada exitosamente. Usa este link para iniciar sesión: {url_for('invitado.login_invitado', _external=True)}\nTu contraseña es: {password}\n\n¡Bienvenido!"
            mail = current_app.extensions['mail']
            mail.send(msg)
            flash('Registro exitoso! Revisa tu correo para el link de inicio de sesión y tu contraseña.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Un usuario ya está registrado con la misma CURP, verifique de nuevo', category='danger')
            return redirect(url_for('invitado.registro_invitado'))

    return render_template('invitado/registro_invitado.html')


@invitado_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['correo']
        password = request.form['contraseña']
        invitado = Invitado.query.filter_by(email=email).first()

        if invitado and invitado.check_password(password):
            login_user(invitado)
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('invitado.perfil_invitado'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
            return render_template('invitado/login_invitado.html')
    return render_template('invitado/login_invitado.html')


@invitado_bp.route('/perfil')
@login_required
def perfil():
    # Obtener pedidos del invitado
    pedidos = db.session.query(Pedido).filter(Pedido.id_usuario == current_user.id).all()

    # Obtener productos asociados a los pedidos
    productos_pedidos = []
    for pedido in pedidos:
        productos = PedidoProducto.query.filter_by(id_pedido=pedido.id).all()
        productos_pedidos.append((pedido, productos))

    # Obtener carrito del invitado
    carrito = db.session.query(Carrito, Producto).join(Producto, Carrito.id_producto == Producto.id).filter(
        Carrito.id_usuario == current_user.id).all()

    return render_template('invitado/perfil_invitado.html', carrito=carrito,
                           productos_pedidos=productos_pedidos)

