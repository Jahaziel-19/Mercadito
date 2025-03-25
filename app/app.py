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
from routes import register_blueprints  # Importa la función para registrar Blueprints

# Módulos personalizados
from config import Config # Importar configuraciones
from models import db, RolEnum, Invitado, Alumno, Docente, Carrera, Producto, Pedido, PedidoProducto, Admin, Carrito # Importación de modelos
from scripts import random_int, verificar_correo_existente #, enviar_correo

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


# Escaneo de QR
@app.route('/escaner', methods=['GET', 'POST'])
def escaner():
    user = {
        "nombre": current_user.nombre,
        "rol": current_user.rol,
        "carrera": current_user.carrera
    }
    print("user: ", user)  # Esto imprime el diccionario user en el servidor
    return render_template('qr_scan.html', user=user)


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


    return redirect(url_for(f'{str(usuario.rol).lower()}.perfil'))  # Redirigir al perfil del usuario o a la página adecuada


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

# Cierre de sesión para todo usuario
@app.route('/logout', methods=['POST', 'GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))

register_blueprints(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)