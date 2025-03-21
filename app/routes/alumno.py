from flask import Blueprint

alumno_bp = Blueprint('alumno', __name__, template_folder='../templates/alumno')

@alumno_bp.route('/perfil')
@login_required
def perfil_alumno():
    return "Perfil del alumno"
