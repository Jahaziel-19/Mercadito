from flask import Blueprint

docente_bp = Blueprint('docente', __name__, template_folder='../templates/docente')

@docente_bp.route('/perfil')
@login_required
def perfil_docente():
    return "Perfil del docente"
