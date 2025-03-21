from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, login_required

invitado_bp = Blueprint('invitado', __name__, template_folder='../templates/invitado')

@invitado_bp.route('/registro', methods=['GET', 'POST'])
def registro_invitado():
    if request.method == 'POST':
        email = request.form['email']
        if verificar_correo_existente(email):
            flash('Correo ya registrado.', 'danger')
            return redirect(url_for('invitado.registro_invitado'))

        nuevo_invitado = Invitado(
            id=request.form['id'],
            nombre=request.form['nombre'].upper(),
            email=email,
            foto_perfil='static/default_profile_pic.png'
        )
        nuevo_invitado.set_password('contraseña123')  # Contraseña predeterminada o generada.
        db.session.add(nuevo_invitado)
        db.session.commit()
        flash('Registro exitoso.', 'success')
        return redirect(url_for('general.index'))

    return render_template('registro_invitado.html')

@invitado_bp.route('/perfil')
@login_required
def perfil_invitado():
    return render_template('perfil_invitado.html', usuario=current_user)
