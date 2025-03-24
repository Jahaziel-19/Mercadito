from flask import jsonify, render_template, flash, redirect, url_for, current_app
import random
from models import Admin, Docente, Alumno, Invitado
from functools import wraps
from flask_login import current_user
from flask_mail import Message

def random_int(length):
    min_value = 10 ** (length - 1)
    max_value = (10 ** length) - 1
    return random.randint(min_value, max_value)

def enviar_correo(destinatarios, asunto, mensaje, archivos=None, cc=None, action_text=None, action_url=None):
    # Crear un mensaje
    msg = Message(sender=current_app.config['MAIL_USERNAME'], subject=asunto, recipients=destinatarios)

    # Renderizar la plantilla del correo
    msg.html = render_template('email/email_template.html', subject=asunto, message=mensaje, action_text=action_text, action_url=action_url)
    
    mail = current_app.extensions['mail']

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


def verificar_correo_existente(email):
    """
    Verifica si el correo ya está registrado en cualquiera de los modelos de usuario.
    Retorna True si el correo ya existe, de lo contrario retorna False.
    """
    return (
        Admin.query.filter_by(email=email).first() or
        Docente.query.filter_by(email=email).first() or
        Alumno.query.filter_by(email=email).first() or
        Invitado.query.filter_by(email=email).first()
    )

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