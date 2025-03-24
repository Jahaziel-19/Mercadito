from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Producto, Pedido, RolEnum, PedidoProducto, Admin, Docente, Alumno, Invitado
from scripts import random_int, roles_required
import qrcode
from datetime import datetime
import os

from flask_mail import Message

# Reportlab para la generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas



pedidos_bp = Blueprint('pedidos', __name__)

################################################################
# Generación de pedido por el usuario
################################################################

# Generar pedido
@pedidos_bp.route('/pedido/<int:producto_id>', methods=['POST'])
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
    return redirect(url_for(f'{current_user.rol.lower()}') + '/perfil')

################################################################
# Gestión de pedidos en la aplicación (ADMINISTRADOR) #
################################################################

# Actualización en el estatus del pedido (Recibido/Cancelado)
@pedidos_bp.route('/actualizar_pedido', methods=['POST'])
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
        c.setFillColor(colors.HexColor(f'#{current_app.config['COLOR1']}'))
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
            msg = Message('Actualización de Pedido', sender=current_app.config['MAIL_USERNAME'], recipients=[usuario.email])
            msg.body = f'Tu pedido ha sido cancelado.\n\nEstatus: {estatus}\nNotas: {notas}'
            mail = current_app.extensions['mail']
            mail.send(msg)

        for producto in productos_carrera:
            producto.ubicacion = 'Cancelado'
            producto.estatus = 'cancelado'
            producto.fecha_recibido = datetime.utcnow()
            producto.fecha_limite = fecha_limite

        db.session.commit()
        flash('Pedido cancelado y notificación enviada', 'success')
        return redirect(url_for('admin.perfil'))
    else:
        # Convertir fecha_limite a objeto datetime
        fecha_limite = None
        if fecha_limite_str:
            try:
                fecha_limite = datetime.strptime(fecha_limite_str, '%Y-%m-%d')
            except ValueError:
                flash('Formato de fecha límite no válido', 'danger')
                return redirect(url_for('admin.perfil'))

        for producto in productos_carrera:
            producto.ubicacion = ubicacion
            producto.estatus = estatus
            producto.fecha_recibido = datetime.utcnow()
            producto.fecha_limite = fecha_limite

        db.session.commit()

        # Generar el PDF
        pdf_path = generar_pdf(pedido, productos_carrera, ubicacion, notas, fecha_limite)

        if usuario:
            msg = Message('Actualización de Pedido', sender=current_app.config['MAIL_USERNAME'], recipients=[usuario.email])
            msg.body = f'Tu pedido ha sido actualizado.\n\nEstatus: {estatus}\nNotas: {notas}\nUbicación: {ubicacion}\nFecha Límite: {fecha_limite}'
            mail = current_app.extensions['mail']
            with current_app.open_resource(pdf_path) as pdf:
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
    return redirect(url_for('admin.perfil'))

# Ver pedido
@pedidos_bp.route('/obtener_pedido/<int:pedido_id>', methods=['GET'])
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

# Cierre de pedido completado
@pedidos_bp.route('/cerrar_pedido', methods=['POST'])
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

# Confirmar cierre de pedido
@pedidos_bp.route('/confirmar_cierre_pedido', methods=['POST'])
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

    # Verificar si todos los productos del pedido están entregados
    todos_entregados = all(producto.estatus == 'entregado' for producto in pedido.productos)
    
    if todos_entregados:
        pedido.estatus = 'cerrado'

    db.session.commit()

    flash('Pedido cerrado con éxito', 'success')
    return redirect(url_for(f'{current_user.rol.lower()}') + '/perfil')