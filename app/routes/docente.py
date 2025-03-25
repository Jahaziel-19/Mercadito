from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, current_user, login_required
from models import Docente, db, Carrito, Producto, Pedido, PedidoProducto, Carrera
from scripts import verificar_correo_existente
from werkzeug.utils import secure_filename
import os
import random
import string
from flask_mail import Message


docente_bp = Blueprint('docente', __name__, template_folder='../templates/docente')

@docente_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        id = request.form['id']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        carrera = request.form['carrera']
        email = request.form['email']
        foto_perfil = request.files['foto_perfil']

        if verificar_correo_existente(email):
            flash('Este correo ya está registrado en la plataforma. Por favor, usa otro correo.', category='danger')
            return redirect(url_for('docente.registro_docente'))

        if foto_perfil and foto_perfil.filename != '':
            filename = secure_filename(foto_perfil.filename)
            foto_perfil.save(os.path.join(current_app.config['UPLOAD_USER'], filename))
            foto_path = os.path.join(current_app.config['UPLOAD_USER'], filename)
        else:
            foto_path = 'static/default_profile_pic.png'

        # Generar una contraseña aleatoria de 10 caracteres
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        nuevo_docente = Docente(
            id=id,
            nombre=nombre.upper(),
            apellido_paterno=apellido_paterno.upper(),
            apellido_materno=apellido_materno.upper(),
            carrera=carrera.upper(),
            email=email,
            foto_perfil=foto_path
        )

        if not Docente.query.get(nuevo_docente.id):
            nuevo_docente.set_password(password)
            db.session.add(nuevo_docente)
            db.session.commit()
            # Enviar la contraseña y el link de inicio de sesión al correo electrónico
            msg = Message("Registro exitoso", sender=current_app.config['MAIL_USERNAME'], recipients=[nuevo_docente.email])
            msg.body = f"Hola {nombre},\n\nTu cuenta de docente ha sido creada exitosamente. Usa este link para iniciar sesión: {url_for('docente.login_docente', _external=True)}\nTu contraseña es: {password}\n\n¡Bienvenido!"
            mail = current_app.extensions['mail']
            mail.send(msg)
            flash('Registro exitoso! Revisa tu correo para el link de inicio de sesión y tu contraseña.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Un usuario ya está registrado con los mismos datos, verifique de nuevo', category='danger')
            return redirect(url_for('docente.registro_docente'))

    carreras = Carrera.query.all()
    return render_template('registro_docente.html', carreras=carreras)


@docente_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['correo']
        password = request.form['contraseña']
        docente = Docente.query.filter_by(email=email).first()

        if docente and docente.check_password(password):
            login_user(docente)
            flash('Inicio de sesión exitoso.', category='success')
            return redirect(url_for('docente.perfil_docente'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')
            return render_template('login_docente.html')
    return render_template('login_docente.html')


@docente_bp.route('/perfil')
@login_required
def perfil():
    estatus = {
        'abierto': 'bg-warning',
        'recibido': 'bg-success',
        'cancelado': 'bg-danger',
        'cerrado': 'bg-primary'
    }

    pedidos_cerrados = db.session.query(Pedido).options(
        joinedload(Pedido.productos)
    ).filter(Pedido.estatus == 'cerrado').all()

    productos_pedidos_cerrados = []
    for pedido in pedidos_cerrados:
        productos_asociados = PedidoProducto.query.filter_by(
            id_pedido=pedido.id,
            carrera=current_user.carrera
        ).all()

        if productos_asociados:
            usuario = (
                Admin.query.get(pedido.id_usuario) or
                Docente.query.get(pedido.id_usuario) or
                Alumno.query.get(pedido.id_usuario) or
                Invitado.query.get(pedido.id_usuario)
            )
            pedido.nombre_usuario = f"{usuario.nombre} {usuario.apellido_paterno} {usuario.apellido_materno}" if usuario else "Desconocido"
            productos_pedidos_cerrados.append((pedido, productos_asociados))

    return render_template(
        'perfil_docente.html',
        productos_pedidos_cerrados=productos_pedidos_cerrados,
        estatus=estatus
    )