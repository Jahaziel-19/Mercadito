# Módulos de python
import os
import random
import string
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
# Reportlab para la generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas

import qrcode
from datetime import datetime

# Módulos de flask
from flask import Flask, render_template, request, session, Response, redirect, url_for, flash , current_app, jsonify
from flask_login import LoginManager, current_user, login_required, login_user, logout_user # Registro e inicio de sesión de usuarios
from flask_migrate import Migrate # Realizar migraciones en la base de datos
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

# Módulos personalizados
from config import Config # Importar configuraciones
from models import db, RolEnum, Invitado, Alumno, Docente, Carrera, Producto, Pedido, PedidoProducto, Admin, Carrito # Importación de modelos
from scripts import random_int, verificar_correo_existente #, enviar_correo
#from app.recognition import registrar_docente, reconocer_usuario
#import face_recognition
import numpy as np
app = Flask(__name__) # Declaración de la app
app.config.from_object(Config) # Declaración de las configuraciones

app.app_context().push()
db.init_app(app)
migrate = Migrate(app, db, render_as_batch=True)

# Mail 
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
#login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    invitado = Invitado.query.get(user_id)
    alumno = Alumno.query.get(user_id)
    docente = Docente.query.get(user_id)
    admin = Admin.query.get(user_id)

    if invitado:
        return invitado
    elif alumno:
        return alumno
    elif docente:
        return docente
    elif admin:
        return admin
    else:
        return None




# Permisos
def roles_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.rol in roles:
                return func(*args, **kwargs)
            else:
                flash('No tienes permiso para acceder a esta página', 'danger')
                return redirect(url_for('index'))
        return wrapper
    return decorator

# Generar token para reestablecimiento de contraseña
def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

# Verifica validez de token para reestablecimiento de contraseña
def verify_reset_token(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=300)  # 5 minutos
    except Exception:
        return None
    return email

# Envio de correos
def enviar_correo(destinatarios, asunto, mensaje, archivos=None, cc=None, action_text=None, action_url=None):
    # Crear un mensaje
    msg = Message(sender=app.config['MAIL_USERNAME'], subject=asunto, recipients=destinatarios)

    # Renderizar la plantilla del correo
    msg.html = render_template('email/email_template.html', subject=asunto, message=mensaje, action_text=action_text, action_url=action_url)

    # Adjuntar archivos si se proporcionan
    if archivos:
        for archivo in archivos:
            msg.attach(archivo.filename, archivo.content_type, archivo.read())

    # Añadir destinatarios en copia (CC) si se proporcionan
    if cc:
        msg.cc = cc

    # Enviar el correo
    with mail.connect() as conn:
        conn.send(msg)


# *******************************  RUTAS  *******************************
@app.route('/', methods=['POST', 'GET'])
def index():
    folder_carrusel = app.config['CARROUSEL']
    imagenes_carrusel = [f for f in os.listdir(folder_carrusel) if os.path.isfile(os.path.join(folder_carrusel, f))]
    print([f for f in os.listdir(folder_carrusel) if os.path.isfile(os.path.join(folder_carrusel, f))])
    return render_template('index.html', imagenes_carrusel=imagenes_carrusel)

# --------------- INVITADO -----------------
@app.route('/registro_invitado', methods=['GET', 'POST'])
def registro_invitado():
    if request.method == 'POST':
        id = request.form['id']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        email = request.form['email']
        foto_perfil = request.files['foto_perfil']
        
        if verificar_correo_existente(email):
            flash('Este correo ya está registrado en la plataforma. Por favor, usa otro correo.', category='danger')
            return redirect(url_for('registro_invitado'))


        if foto_perfil and foto_perfil.filename != '':
            filename = secure_filename(foto_perfil.filename)
            foto_perfil.save(os.path.join(app.config['UPLOAD_USER'], filename))
            foto_path = os.path.join(app.config['UPLOAD_USER'], filename)
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
            foto_perfil=foto_path  # Maneja la carga de archivos según tus necesidades
        )

        if not Invitado.query.get(nuevo_invitado.id):            
            nuevo_invitado.set_password(password)

            db.session.add(nuevo_invitado)
            db.session.commit()

            # Enviar la contraseña y el link de inicio de sesión al correo electrónico
            msg = Message("Registro exitoso", sender=app.config['MAIL_USERNAME'], recipients=[nuevo_invitado.email])
            msg.body = f"Hola {nombre},\n\nTu cuenta de invitado ha sido creada exitosamente. Usa este link para iniciar sesión: {url_for('login_invitado', _external=True)}\nTu contraseña es: {password}\n\n¡Bienvenido!"
            mail.send(msg)

            flash('Registro exitoso! Revisa tu correo para el link de inicio de sesión y tu contraseña.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Un usuario ya está registrado con la misma CURP, verifique de nuevo', category='danger')
            return redirect(url_for('registro_invitado'))

    return render_template('invitado_templates/registro_invitado.html')

@app.route('/login_invitado', methods=['GET', 'POST'])
def login_invitado():
    if request.method == 'POST':
        email = request.form['correo']
        password = request.form['contraseña']

        invitado = Invitado.query.filter_by(email=email).first()
        if invitado and invitado.check_password(password):
            login_user(invitado)
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('perfil_invitado'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('invitado_templates/login_invitado.html')

@app.route('/perfil_invitado')
@login_required
def perfil_invitado():
    # Obtener pedidos del invitado
    pedidos = db.session.query(Pedido).filter(Pedido.id_usuario == current_user.id).all()

    # Obtener productos asociados a los pedidos
    productos_pedidos = []
    for pedido in pedidos:
        productos = PedidoProducto.query.filter_by(id_pedido=pedido.id).all()
        productos_pedidos.append((pedido, productos))

    # Obtener carrito del invitado
    carrito = db.session.query(Carrito, Producto).join(Producto, Carrito.id_producto == Producto.id).filter(Carrito.id_usuario == current_user.id).all()

    return render_template('invitado_templates/perfil_invitado.html', carrito=carrito, productos_pedidos=productos_pedidos)


# --------------- DOCENTE -----------------
@app.route('/registro_docente', methods=['GET', 'POST'])
def registro_docente():
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
            return redirect(url_for('registro_docente'))


        if foto_perfil and foto_perfil.filename != '':
            filename = secure_filename(foto_perfil.filename)
            foto_perfil.save(os.path.join(app.config['UPLOAD_USER'], filename))
            foto_path = os.path.join(app.config['UPLOAD_USER'], filename)
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
            foto_perfil=foto_path  # Maneja la carga de archivos según tus necesidades
        )

        if not Docente.query.get(nuevo_docente.id):
            nuevo_docente.set_password(password)

            db.session.add(nuevo_docente)
            db.session.commit()

            # Enviar la contraseña y el link de inicio de sesión al correo electrónico
            msg = Message("Registro exitoso", sender=app.config['MAIL_USERNAME'], recipients=[nuevo_docente.email])
            msg.body = f"Hola {nombre},\n\nTu cuenta de invitado ha sido creada exitosamente. Usa este link para iniciar sesión: {url_for('login_docente', _external=True)}\nTu contraseña es: {password}\n\n¡Bienvenido!"
            mail.send(msg)

            flash('Registro exitoso! Revisa tu correo para el link de inicio de sesión y tu contraseña.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Un usuario ya está registrado con los mismos datos, verifique de nuevo', category='danger')
            return redirect(url_for('registro_docente'))
    carreras = Carrera.query.all()
    return render_template('docente_templates/registro_docente.html', carreras=carreras)

@app.route('/login_docente', methods=['GET', 'POST'])
def login_docente():
    if request.method == 'POST':
        email = request.form['correo']
        password = request.form['contraseña']

        docente = Docente.query.filter_by(email=email).first()
        if docente and docente.check_password(password):
            login_user(docente)
            flash('Inicio de sesión exitoso.', category='success')
            return redirect(url_for('perfil_docente'))
        else:
            flash('Correo o contraseña incorrectos.', 'danger')

    return render_template('docente_templates/login_docente.html')

@app.route('/perfil_docente')
@login_required
def perfil_docente():  
    estatus = {
        'abierto':'bg-warning',
        'recibido':'bg-success',
        'cancelado':'bg-danger',
        'cerrado':'bg-primary'
    }
    # Obtener pedidos del docente
    pedidos = db.session.query(Pedido).filter(Pedido.id_usuario == current_user.id).all()
    # Obtener pedidos cerrados por el docente
    pedidos_cerrados = db.session.query(Pedido).filter(
        #Pedido.id_usuario_cierre == f'{current_user.nombre} {current_user.apellido_paterno} {current_user.apellido_materno}',
        Pedido.estatus == 'cerrado'
    ).all()

    # Obtener productos asociados a los pedidos cerrados
    productos_pedidos_cerrados = []
    for pedido in pedidos_cerrados:
        productos = PedidoProducto.query.filter_by(id_pedido=pedido.id).all()
        productos_pedidos_cerrados.append((pedido, productos))
    # Obtener carrito del docente
    carrito = db.session.query(Carrito, Producto).join(Producto, Carrito.id_producto == Producto.id).filter(Carrito.id_usuario == current_user.id).all()
    return render_template('docente_templates/perfil_docente.html', carrito=carrito, pedidos=pedidos, pedidos_cerrados=pedidos_cerrados, estatus=estatus)


# --------------- ALUMNO -----------------
@app.route('/registro_alumno', methods=['GET', 'POST'])
def registro_alumno():
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
            return redirect(url_for('registro_alumno'))


        if foto_perfil and foto_perfil.filename != '':
            filename = secure_filename(foto_perfil.filename)
            foto_perfil.save(os.path.join(app.config['UPLOAD_USER'], filename))
            foto_path = os.path.join(app.config['UPLOAD_USER'], filename)
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

        return redirect(url_for('login'))

    carreras = Carrera.query.all()
    return render_template('registro_alumno.html', carreras=carreras)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        usuario = Alumno.query.filter_by(email=correo).first()
        if usuario and check_password_hash(usuario.password_hash, contraseña):
            login_user(usuario)
            return redirect(url_for('productos_servicios'))
        else:
            flash('Usuario o contraseña incorrectos')    
    return render_template('login.html')

@app.route('/perfil_alumno', methods=['POST', 'GET'])
@login_required
def perfil_alumno():
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
    carrito = db.session.query(Carrito, Producto).join(Producto, Carrito.id_producto == Producto.id).filter(Carrito.id_usuario == current_user.id).all()

    return render_template('perfil_alumno.html', carrito=carrito, productos_pedidos=productos_pedidos)

# Previsualizacion del producto
@app.route('/previsualizar_producto/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def previsualizar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if request.method == 'POST':
        id_user = current_user.id
        cantidad = int(request.form['cantidad'])
        sub_total = cantidad * producto.precio
        notas = request.form.get('notas', '')
    return render_template('previsualizar_producto.html', producto=producto)

@app.route('/pedido/<int:producto_id>', methods=['POST'])
@login_required
def pedido(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    id_pedido = random_int(28)

    if request.method == 'POST':
        id_user = current_user.id  
        cantidad = int(request.form.get('cantidad', 1))
        notas = request.form.get('notas', '')

        # Calcular el total
        total = cantidad * producto.precio

        nuevo_pedido = Pedido(
            id=id_pedido,
            id_producto=producto.id,
            id_usuario=id_user,
            cantidad=cantidad,
            total=total,
            notas=notas
        )

        # Asegurar que el ID de pedido es único
        if Pedido.query.filter_by(id=id_pedido).first():
            nuevo_pedido.id = random_int(8)

        db.session.add(nuevo_pedido)
        db.session.commit()

    flash('Pedido generado', category='success')
    return redirect(url_for(f'perfil_{(current_user.rol).lower()}'))

@app.route('/agregar_carrito/<int:producto_id>', methods=['POST'])
@login_required
def agregar_carrito(producto_id):
    rol = str(current_user.rol).lower()
    producto = Producto.query.get_or_404(producto_id)
    id_carrito = random_int(4)
    if request.method == 'POST':
        id_user = current_user.id  
        cantidad = int(request.form.get('cantidad', 1))
        notas = request.form.get('notas', '')
        if cantidad == '':
            return url_for('agregar_carrito', producto_id=producto_id)
        # Calcular el total
        total = cantidad * producto.precio

        nuevo_carrito_item = Carrito(
            id=id_carrito,
            id_producto=producto.id,
            id_usuario=id_user,
            cantidad=cantidad,
            notas=notas, 
            total=total
        )
        # Asegurar que el ID de carrito es único
        if Carrito.query.filter_by(id=id_carrito).first():
            nuevo_carrito_item.id = random_int(8)

        db.session.add(nuevo_carrito_item)
        db.session.commit()

    flash('Producto agregado al carrito', category='success')
    return redirect(url_for(f'perfil_{rol}'))

# Ruta para editar un item del carrito
@app.route('/editar_carrito/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_carrito(id):
    rol = (current_user.rol).lower()
    item = Carrito.query.get_or_404(id)
    producto = Producto.query.get_or_404(item.id_producto)

    if request.method == 'POST':
        item.cantidad = int(request.form.get('cantidad', 1))
        print(f"Cantidad: {item.cantidad}")
        item.notas = request.form.get('notas', '')
        print(f"Notas: {item.notas}")
        item.total = item.cantidad * producto.precio
        print(f"Total: {item.total}")
        
        db.session.commit()
        flash('Carrito actualizado', 'success')
        return redirect(url_for(f'perfil_{rol}'))

    return render_template('editar_carrito.html', item=item, producto=producto)

# Pedir items de carrito
@app.route('/pedir_carrito', methods=['POST'])
@login_required
def pedir_carrito():
    rol = str(current_user.rol).lower()
    carrito_items = Carrito.query.filter(Carrito.id_usuario == current_user.id).all()

    if not carrito_items:
        flash('Tu carrito está vacío', 'warning')
        return redirect(url_for(f'perfil_{rol}'))
        
    total_pedido = sum(item.total for item in carrito_items)
    notas_pedido = request.form.get('notas', '')

    # Crear un nuevo pedido
    nuevo_pedido = Pedido(
        id=random_int(8),
        id_usuario=current_user.id,
        total=total_pedido,
        estatus='abierto',
    )
    db.session.add(nuevo_pedido)
    db.session.flush()  # Para obtener el ID del nuevo pedido

    # Agregar productos del carrito al nuevo pedido
    carreras_pedido = set()
    for item in carrito_items:
        producto = Producto.query.filter_by(id=item.id_producto).first()
        nuevo_detalle = PedidoProducto(
            id_pedido=nuevo_pedido.id,
            id_producto=item.id_producto,
            cantidad=item.cantidad,
            subtotal=item.total,
            carrera=producto.carrera,
            estatus='abierto'
        )
        db.session.add(nuevo_detalle)
        carreras_pedido.add(producto.carrera)  # Recolectar carreras únicas

    # Vaciar el carrito después de crear el pedido
    for item in carrito_items:
        db.session.delete(item)

    db.session.commit()

    # Notificación a los administradores por carrera
    admins_notificados = []
    for carrera in carreras_pedido:
        admin = Admin.query.filter_by(carrera=carrera).first()
        if admin:
            admins_notificados.append(admin.email)
            enviar_correo(
                destinatarios=[current_user.email],
                asunto=f"Generación de nuevo pedido",
                mensaje=(
                    f"Se ha generado un nuevo pedido con productos relacionados a la carrera {carrera}. "
                ),
                archivos=None,
                cc=[admin.email],  # Notificar también al administrador
                action_text=None,
                action_url=None#url_for('ver_pedido', pedido_id=nuevo_pedido.id, _external=True)
            )

    flash('Pedido creado exitosamente y se notificó a los administradores.', 'success')
    return redirect(url_for(f'perfil_{rol}'))

'''
@app.route('/pedir_carrito', methods=['POST'])
@login_required
def pedir_carrito():
    carrito_items = Carrito.query.filter(
        (Carrito.id_usuario == current_user.id)).all() # | (Carrito.id_admin == current_user.id)

    if not carrito_items:
        flash('Tu carrito esta vacío', 'warning')
        return redirect(url_for('perfil_alumno'))
        
    total_pedido = sum(item.total for item in carrito_items)
    notas_pedido = request.form.get('notas', '')
    
    nuevo_pedido = Pedido(
        id=random_int(8),
        id_usuario=current_user.id,
        total=total_pedido,
        notas=notas_pedido,
        estatus='abierto'
    )

    db.session.add(nuevo_pedido)
    db.session.flush()

    for item in carrito_items:
        nuevo_detalle = PedidoDetalle(
            pedido_id=nuevo_pedido.id,
            id_producto=item.id_producto,
            cantidad=item.cantidad,
            subtotal=item.total
        )
        db.session.add(nuevo_detalle)

    # Vaciar el carrito después de crear los pedidos
    for item in carrito_items:
        db.session.delete(item)

    db.session.commit()
    flash('Pedido creado exitosamente.', 'success')
    return redirect(url_for('perfil_alumno'))
'''
# Ruta para eliminar un item del carrito
@app.route('/eliminar_carrito/<int:id>', methods=['GET', 'POST'])
@login_required
def eliminar_carrito(id):
    rol = (current_user.rol).lower()
    item = Carrito.query.get_or_404(id)
    producto = Producto.query.get_or_404(item.id_producto)
    db.session.delete(item)
    db.session.commit()
    flash(f'{producto.nombre_producto} eliminado de tu carrito', category='success')
    return redirect(url_for(f'perfil_{rol}'))





# --------------- ADMIN -----------------
# Registro de usuario Administrador
@app.route('/registro_admin', methods=['POST', 'GET'])
# @login_required
def registro_admin():
    if request.method == 'POST':
        id = request.form['id']
        nombre = request.form['nombre']
        carrera = request.form['carrera']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        foto_perfil = request.files['foto_perfil']

        if verificar_correo_existente(email):
            flash('Este correo ya está registrado en la plataforma. Por favor, usa otro correo.', category='danger')
            return redirect(url_for('registro_admin'))


        if foto_perfil and foto_perfil.filename != '':
            filename = secure_filename(foto_perfil.filename)
            foto_perfil.save(os.path.join(app.config['UPLOAD_USER'], filename))
            foto_path = os.path.join(app.config['UPLOAD_USER'], filename)
        else:
            foto_path = 'static/default_profile_pic.png'
        
        nuevo_usuario = Admin(
            id=id,
            nombre=nombre.upper(),
            carrera=carrera.upper(),
            email=email,
            password_hash=password,
            foto_perfil=foto_path
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return redirect(url_for('login_admin'))    
    return render_template('admin_templates/registro_admin.html', carreras=Carrera.query.all())

# Autenticación de usuario Administrador
@app.route('/login_admin', methods=['POST', 'GET'])
def login_admin():
    if request.method == 'POST':
        correo = request.form['email']
        contraseña = request.form['password']
        usuario = Admin.query.filter_by(email=correo).first()
        print(usuario)
        if usuario and check_password_hash(usuario.password_hash, contraseña):
            login_user(usuario)
            return redirect(url_for(f'perfil_admin'))
        else:
            flash('Usuario o contraseña incorrectos', category='danger')        
    return render_template('admin_templates/login_admin.html')

@app.route('/perfil_admin', methods=['POST', 'GET'])
@login_required
def perfil_admin():
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

    # Obtener pedidos abiertos relacionados con la carrera del admin
    pedidos = db.session.query(Pedido).filter(Pedido.estatus != 'cerrado').all()

    # Obtener productos asociados a los pedidos abiertos
    productos_pedidos = []
    for pedido in pedidos:
        productos_asociados = PedidoProducto.query.filter_by(id_pedido=pedido.id).all()
        productos_pedidos.append((pedido, productos_asociados))

    # Obtener pedidos cerrados relacionados con la carrera del admin
    pedidos_cerrados = db.session.query(Pedido).filter(Pedido.estatus == 'cerrado').all()

    # Obtener productos asociados a los pedidos cerrados
    productos_pedidos_cerrados = []
    for pedido in pedidos_cerrados:
        productos_asociados = PedidoProducto.query.filter_by(id_pedido=pedido.id).all()
        productos_pedidos_cerrados.append((pedido, productos_asociados))

    # Obtener carrito del admin (si aplica)
    carrito = db.session.query(Carrito, Producto).join(Producto, Carrito.id_producto == Producto.id).filter(Carrito.id_usuario == current_user.id).all()

    return render_template(
        'admin_templates/perfil_admin.html',
        productos=productos,
        productos_pedidos=productos_pedidos,
        productos_pedidos_cerrados=productos_pedidos_cerrados,
        carrito=carrito,
        pedidos=pedidos,
        estatus=estatus
    )

# Crear producto
@app.route('/crear_producto', methods=['POST', 'GET'])
@login_required
def crear_producto():
    if request.method == 'POST':
        nombre_producto = request.form['nombre_producto']
        descripcion = request.form.get('descripcion', '')
        precio = request.form['precio']
        carrera = request.form['carrera']
        imagen_producto = request.files['imagen_producto']
        numero_medida = str(request.form.get('numero_medida', None))
        medida = request.form.get('medida', None)  # Obtener el campo medida

        if imagen_producto and imagen_producto.filename != '':
            filename = secure_filename(imagen_producto.filename)
            # Crear directorio si no existe
            if not os.path.exists(app.config['UPLOAD_PRODUCT']):
                os.makedirs(app.config['UPLOAD_PRODUCT'])
            imagen_path = os.path.join(app.config['UPLOAD_PRODUCT'], filename)
            imagen_producto.save(imagen_path)
            imagen_path.replace('\\', '/')
        else:
            imagen_path = 'static/uploads/icon-box.png'
        
        id_producto = random_int(5)
        nuevo_producto = Producto(
            id=id_producto,
            nombre_producto=nombre_producto,
            descripcion=descripcion,
            precio=precio,
            carrera=carrera,
            imagen_producto=imagen_path,
            medida=str(numero_medida + medida)  # Asignar medida al nuevo producto
        )

        db.session.add(nuevo_producto)
        db.session.commit()
        flash('¡Producto creado exitosamente!', category='success')

        carreras = Carrera.query.all()
    return redirect(url_for('perfil_admin'))

# Editar producto
@app.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    if current_user.rol != 'ADMIN':
        return redirect(url_for('login'))
    
    producto = Producto.query.get_or_404(producto_id)
    
    if request.method == 'POST':
        imagen_producto = request.files['imagen_producto']
        if imagen_producto and imagen_producto.filename != '':
            filename = secure_filename(imagen_producto.filename)
            # Crear directorio si no existe
            if not os.path.exists(app.config['UPLOAD_PRODUCT']):
                os.makedirs(app.config['UPLOAD_PRODUCT'])
            imagen_path = os.path.join(app.config['UPLOAD_PRODUCT'], filename)
            imagen_producto.save(imagen_path)
            imagen_path.replace('\\', '/')
        else:
            imagen_path = producto.imagen_producto

        producto.imagen_producto = imagen_path
        producto.nombre_producto = request.form['nombre_producto']
        producto.precio = request.form['precio']
        producto.medida = str(str(request.form.get('numero_medida', None)) + request.form.get('medida', None))
        producto.descripcion = request.form['descripcion']
        
        db.session.commit()
        flash(f'¡{producto.nombre_producto} editado!', category='success')
        return redirect(url_for('perfil_admin'))
    
    return render_template('admin_templates/editar_producto.html', producto=producto)

# Eliminar producto
@app.route('/eliminar_producto/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def eliminar_producto(producto_id):
    if current_user.rol != 'ADMIN':
        return redirect(url_for('index'))
    
    producto = Producto.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    
    return redirect(url_for('perfil_admin'))

# Actualización en el estatus del pedido (Recibido/Cancelado)
@app.route('/actualizar_pedido', methods=['POST'])
@login_required
@roles_required(RolEnum.ADMIN.value)
def actualizar_pedido():
    def generar_pdf(pedido, productos, ubicacion, notas, fecha):
        # Crear el QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f'{pedido.id}')
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        # Guardar el QR en un archivo temporal
        qr_path = f'temp_qr_{pedido.id}.png'
        img.save(qr_path)

        # Crear el PDF
        pdf_path = f'ticket_pedido_{pedido.id}.pdf'
        c = canvas.Canvas(pdf_path, pagesize=letter)

        # Añadir el logo centrado en la parte superior
        c.drawImage("static/logo_ut.png", 2.5*inch, 8.8*inch, width=2*inch, height=2*inch, mask='auto')
        
        # Añadir el nombre de la universidad
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(4.25*inch, 8.2*inch, "Universidad Tecnológica de Oriental")

        # Escribir información del pedido
        c.setFont("Helvetica", 16)
        c.drawString(1*inch, 7.5*inch, f'Notas: {notas}')
        c.drawString(1*inch, 7*inch, f'Ubicación: {ubicacion}')
        c.drawString(1*inch, 6.5*inch, f'Fecha límite: {fecha}')

        # Listar productos
        c.drawString(1*inch, 4.5*inch, 'Productos:')
        y = 4*inch
        for producto in productos:
            c.drawString(1*inch, y, f'* {producto.producto.nombre_producto}, Cantidad: {producto.cantidad}, Total: ${producto.subtotal}')
            y -= 0.25*inch


        # Añadir el QR al PDF al lado del texto
        c.drawImage(qr_path, 6*inch, 5*inch, width=2.5*inch, height=2.5*inch)  # Ajustar posición y tamaño del QR

        # Pie de página con barra verde
        c.setFillColor(colors.HexColor(f'#{app.config['COLOR1']}'))
        c.rect(0, 0, letter[0], 0.5*inch, fill=1)  # Dibuja un rectángulo verde

        c.save()

        # Eliminar el archivo QR temporal
        os.remove(qr_path)

        return pdf_path
    
    carrera = request.form.get('carrera')
    pedido_id = request.form.get('pedido_id')
    estatus = request.form.get('estatus')
    notas = request.form.get('notas')
    ubicacion = request.form.get('ubicacion')
    fecha_limite_str = request.form.get('fecha_limite')

    pedido = Pedido.query.get_or_404(pedido_id)

    # Obtener todos los productos asociados al pedido
    productos = PedidoProducto.query.filter_by(id_pedido=pedido.id).all()
    productos_carrera = PedidoProducto.query.filter_by(id_pedido=pedido.id, carrera=carrera).all()
    modelos = {
        'ALUMNO': Alumno,
        'DOCENTE': Docente,
        'ADMIN': Admin,
        'INVITADO': Invitado
    }

    usuario = None
    for rol, modelo in modelos.items():
        usuario = modelo.query.filter_by(id=pedido.id_usuario).first()
        if usuario:
            break

    if estatus == 'cancelado':
        if usuario:
            msg = Message('Actualización de Pedido', sender=app.config['MAIL_USERNAME'], recipients=[usuario.email])
            msg.body = f'Tu pedido ha sido cancelado.\n\nEstatus: {estatus}\nNotas: {notas}'
            mail.send(msg)

        for producto in productos_carrera:
            producto.ubicacion = 'Cancelado'
            producto.estatus = 'cancelado'
            producto.fecha_recibido = datetime.utcnow()
            producto.fecha_limite = fecha_limite

        db.session.commit()
        flash('Pedido cancelado y notificación enviada', 'success')
        return redirect(url_for('perfil_admin'))
    else:
        # Convertir fecha_limite a objeto datetime
        fecha_limite = None
        if fecha_limite_str:
            try:
                fecha_limite = datetime.strptime(fecha_limite_str, '%Y-%m-%d')
            except ValueError:
                flash('Formato de fecha límite no válido', 'danger')
                return redirect(url_for('perfil_admin'))

        for producto in productos_carrera:
            producto.ubicacion = ubicacion
            producto.estatus = estatus
            producto.fecha_recibido = datetime.utcnow()
            producto.fecha_limite = fecha_limite

        db.session.commit()

        # Generar el PDF
        pdf_path = generar_pdf(pedido, productos_carrera, ubicacion, notas, fecha_limite)

        if usuario:
            msg = Message('Actualización de Pedido', sender=app.config['MAIL_USERNAME'], recipients=[usuario.email])
            msg.body = f'Tu pedido ha sido actualizado.\n\nEstatus: {estatus}\nNotas: {notas}\nUbicación: {ubicacion}\nFecha Límite: {fecha_limite}'
            with app.open_resource(pdf_path) as pdf:
                msg.attach(pdf_path, 'application/pdf', pdf.read())
            mail.send(msg)

        # Eliminar el PDF temporal
        os.remove(pdf_path)

    # Verificar si todos los productos tienen el estatus "recibido"
    productos_tomados = all(producto.estatus == 'recibido' for producto in productos)

    # Actualizar el estatus del pedido basado en todos los productos
    if productos_tomados:
        pedido.estatus = 'recibido'
    else:
        pedido.estatus = 'abierto'  # Asegúrate de que se mantenga como "abierto" si no todos están "recibidos"

    # Guardar cambios en el pedido
    db.session.commit()

    flash('Pedido actualizado y notificación enviada', 'success')
    return redirect(url_for('perfil_admin'))

# Cierre de pedido completado
@app.route('/cerrar_pedido', methods=['POST'])
@login_required
@roles_required(RolEnum.ADMIN.value, RolEnum.DOCENTE.value)
def cerrar_pedido():
    data = request.json
    pedido_id = data.get('pedido_id')

    if not pedido_id:
        return jsonify({'error': 'No se proporcionó un ID de pedido válido.'}), 400

    try:
        # Obtener todos los productos del pedido
        productos = PedidoProducto.query.filter_by(id_pedido=pedido_id).all()
        
        if not productos:
            return jsonify({'error': 'No se encontraron productos para este pedido.'}), 404

        # Filtrar los productos de la carrera del admin actual
        productos_carrera_admin = [p for p in productos if p.producto.carrera == current_user.carrera]

        # Si no hay productos de la carrera del admin o todos ya están cerrados
        if not productos_carrera_admin or all(p.estatus == 'cerrado' for p in productos_carrera_admin):
            return jsonify({'error': 'No estás autorizado para cerrar productos de este pedido o ya cerraste los que te corresponden.'}), 403

        # Cerrar solo los productos que aún no están cerrados y pertenecen a la carrera del admin
        for producto in productos_carrera_admin:
            if producto.estatus != 'cerrado':
                producto.estatus = 'cerrado'
                producto.id_usuario_cierre = f"(ADMIN) {current_user.nombre}" if current_user.rol == "ADMIN" else current_user.nombre

        # Verificar si todos los productos del pedido están cerrados
        todos_cerrados = all(p.estatus == 'cerrado' for p in productos)

        if todos_cerrados:
            # Si todos los productos están cerrados, actualizar el estatus del pedido
            pedido = Pedido.query.get(pedido_id)
            pedido.estatus = 'cerrado'

        # Guardar los cambios en la base de datos
        db.session.commit()

        return jsonify({
            'message': f'Se cerraron los productos de la carrera {current_user.carrera} del pedido {pedido_id}.',
            'estatus_pedido': 'cerrado' if todos_cerrados else 'abierto'
        }), 200

    except Exception as e:
        print(f"Error al cerrar el pedido: {e}")
        return jsonify({'error': 'Ocurrió un error al cerrar el pedido.'}), 500


@app.route('/confirmar_cierre_pedido', methods=['POST'])
@login_required
@roles_required(RolEnum.ADMIN.value, RolEnum.DOCENTE.value)
def confirmar_cierre_pedido():
    pedido_id = request.form.get('pedido_id')
    carrera = request.form.get('carrera')

    # Obtener el pedido
    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        flash('Pedido no encontrado', 'danger')
        return redirect(url_for('cerrar_pedidos'))

    # Filtrar los productos de la carrera específica
    productos_carrera = PedidoProducto.query.filter_by(id_pedido=pedido.id, carrera=carrera).all()

    # Cambiar el estatus de los productos filtrados a "entregado"
    for producto in productos_carrera:
        producto.estatus = 'cerrado'
        '''
        if current_user.rol:
            #producto.id_usuario_cierre = f'(ADMIN) {current_user.id} {current_user.nombre}'
        else:
            #producto.id_usuario_cierre = f'{current_user.id} {current_user.nombre}'
        '''

    # Verificar si todos los productos del pedido están entregados
    todos_entregados = all(producto.estatus == 'entregado' for producto in pedido.productos)
    
    if todos_entregados:
        pedido.estatus = 'cerrado'

    db.session.commit()

    flash('Pedido cerrado con éxito', 'success')
    return redirect(url_for(f'perfil_{current_user.rol.lower()}'))








# Muestra la página de todos los productos y servicios
@app.route('/productos_servicios', methods=['GET'])
@login_required
def productos_servicios():
    query = request.args.get('query')
    filter_carrera = request.args.get('carrera')

    productos = Producto.query
    if query:
        productos = productos.filter(Producto.nombre_producto.ilike(f'%{query}%'))
    if filter_carrera and filter_carrera != 'all':
        productos = productos.filter_by(carrera=filter_carrera)
    
    productos = productos.all()
    carreras = Carrera.query.all()
    return render_template('productos_servicios.html',  productos=productos, carreras=carreras, query=query, filter_carrera=filter_carrera)





# Escaneo de QR
@app.route('/escaner', methods=['GET', 'POST'])
@roles_required(RolEnum.ADMIN.value, RolEnum.DOCENTE.value)
def escaner():
    user = {
        "nombre": current_user.nombre,
        "rol": current_user.rol,
        "carrera": current_user.carrera
    }
    print("user: ", user)  # Esto imprime el diccionario user en el servidor
    return render_template('qr_scan.html', user=user)


@app.route('/obtener_pedido/<int:pedido_id>', methods=['GET'])
@roles_required(RolEnum.ADMIN.value, RolEnum.DOCENTE.value)
def obtener_pedido(pedido_id):
    carrera = current_user.carrera
    # Filtrar por id del pedido y carrera del usuario actual
    pedido_producto = PedidoProducto.query.filter_by(id_pedido=pedido_id, carrera=carrera).all()

    if pedido_producto:
        # Convertir cada objeto PedidoProducto a un diccionario que incluye el nombre del producto
        productos_dict = [producto.to_dict() for producto in pedido_producto]
        print(productos_dict)
        return jsonify(productos_dict)
    else:
        return jsonify({'error': 'Pedido no encontrado, favor de verificar'}), 404


# --------------- Actualizar foto de perfil -----------------
@app.route('/actualizar_foto_perfil', methods=['GET', 'POST'])
@login_required
def actualizar_foto_perfil():
    app.config['MAX_CONTENT_LENGTH']
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_type = request.form.get('user_type')
        nueva_foto = request.files['nueva_foto']
        print(user_id, user_type, nueva_foto)

    # Validar si se seleccionó un archivo
    if nueva_foto and nueva_foto.filename != '':
        # Validar el tipo de archivo
        if not (nueva_foto.filename.lower().endswith(('.webm','.webp','.png', '.jpg', '.jpeg', '.gif', '.jfif'))):
            flash('Tipo de archivo no permitido. Solo se permiten imágenes PNG, JPG, JPEG o GIF.', 'danger')
            return redirect(url_for(f'perfil_{str(user_type).lower()}'))  # Redirigir al perfil del usuario o a la página adecuada
        
    usuario = None
    if user_type == 'invitado':
        usuario = Invitado.query.get(user_id)
    elif user_type == 'admin':
        usuario = Admin.query.get(user_id)
    elif user_type == 'docente':
        usuario = Docente.query.get(user_id)
    elif user_type == 'alumno':
        usuario = Alumno.query.get(user_id)

    if usuario and usuario.foto_perfil != 'static/default_profile_pic.png':
        try:
            os.remove(usuario.foto_perfil)  # Eliminar la imagen anterior
        except Exception as e:
            print(f"Error al eliminar la foto anterior: {e}")

        
    
    filename = secure_filename(nueva_foto.filename)
    # Guardar la foto en el servidor
    nueva_foto.save(os.path.join(app.config['UPLOAD_USER'], filename))
    foto_path = os.path.join(app.config['UPLOAD_USER'], filename)
        

    # Actualizar la base de datos con la nueva foto para el usuario
    if usuario:
        usuario.foto_perfil = foto_path

        db.session.commit()
        flash('Foto de perfil actualizada correctamente.', 'success')

    else:
        flash('No se seleccionó ninguna imagen válida.', 'danger')


    return redirect(url_for(f'perfil_{str(usuario.rol).lower()}'))  # Redirigir al perfil del usuario o a la página adecuada




# --------------- RUTAS PARA CAMBIAR CONTRASEÑA -----------------
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        
        # Verificar en los cuatro modelos
        user = (
            Admin.query.filter_by(email=email).first() or
            Alumno.query.filter_by(email=email).first() or
            Docente.query.filter_by(email=email).first() or
            Invitado.query.filter_by(email=email).first()
        )
        
        if user:
            token = generate_reset_token(email)
            msg = Message('Restablecimiento de Contraseña', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Para restablecer tu contraseña, visita el siguiente enlace: {url_for("reset_password", token=token, _external=True)}'
            mail.send(msg)
            flash('Se ha enviado un correo con instrucciones para restablecer la contraseña.', 'info')
            return redirect(url_for('index'))  # Redirigir a la página de login
        else:
            flash('No se encontró un usuario con ese correo electrónico.', 'danger')

    return render_template('reset_password_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('El token es inválido o ha expirado.', 'danger')
        return redirect(url_for('reset_password_request'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        
        # Actualizar la contraseña en el modelo correspondiente
        user = (
            Admin.query.filter_by(email=email).first() or
            Alumno.query.filter_by(email=email).first() or
            Docente.query.filter_by(email=email).first() or
            Invitado.query.filter_by(email=email).first()
        )
        
        if user:
            user.set_password(new_password)  
            db.session.commit()
            flash('Tu contraseña ha sido restablecida.', 'success')
            return redirect(url_for('index'))

    return render_template('reset_password.html', token=token)

#_________________________________________________________________________________________________

@app.route('/face', methods=['GET', 'POST'])
def face():
    return render_template('face_recognition.html')

# Reconocimiento facial
@app.route('/recognize', methods=['POST', 'GET'])
def recognize():
    if 'image' not in request.files:
        return jsonify(success=False)

    image_file = request.files['image']
    image = face_recognition.load_image_file(image_file)

    # Aquí debes implementar tu lógica para comparar la imagen
    known_face_encodings = [...]  # Lista de encodings conocidos
    known_face_names = [...]       # Lista de nombres correspondientes

    face_encodings = face_recognition.face_encodings(image)
    
    matches = []

    for face_encoding in face_encodings:
        results = face_recognition.compare_faces(known_face_encodings, face_encoding)
        
        for i in range(len(results)):
            if results[i]:
                matches.append({'name': known_face_names[i], 'confidence': 100})  # Ajusta según sea necesario

    return jsonify(success=True, matches=matches)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'image' not in request.files or 'name' not in request.form:
        return jsonify(success=False)

    image_file = request.files['image']
    name = request.form['name']
    image = face_recognition.load_image_file(image_file)
    
    # Obtener el encoding del rostro
    encoding = face_recognition.face_encodings(image)

    if len(encoding) == 0:
        return jsonify(success=False, message="No se detectó ningún rostro.")

    # Aquí debes almacenar el encoding y el nombre en tu base de datos o en un archivo
    # Ejemplo: almacenar en una lista (esto es solo un ejemplo, deberías usar una base de datos)
    known_face_encodings.append(encoding[0])  # Agregar el encoding a la lista
    known_face_names.append(name)               # Agregar el nombre a la lista

    return jsonify(success=True, message="Rostro registrado exitosamente.")


# Cierre de sesión para todo usuario
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)