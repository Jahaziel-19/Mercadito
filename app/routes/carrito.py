from flask import Blueprint, request, url_for, redirect, flash, render_template
from flask_login import login_required, current_user
from models import db, Producto, Carrito, Pedido, PedidoProducto, Admin
from scripts import random_int, enviar_correo

carrito_bp = Blueprint('carrito', __name__)

################################################################
# Rutas para el manejo de carrito de compras en la aplicación #
################################################################

# Agregar producto al carrito
@carrito_bp.route('/agregar_carrito/<int:producto_id>', methods=['POST'])
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

        # Verificar que el ID del carrito sea unico
        if Carrito.query.filter_by(id=id_carrito).first():
            nuevo_carrito_item.id = random_int(4)

        db.session.add(nuevo_carrito_item)
        db.session.commit()

        flash('Producto agregado al carrito', category='success')
        return redirect(url_for('productos.productos_servicios'))

# Editar un item del carrito
@carrito_bp.route('/editar_carrito/<int:id>', methods=['GET', 'POST'])
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
        return redirect(url_for(rol + '.perfil'))

    return render_template('carrito/editar_carrito.html', item=item, producto=producto)

# Ruta para eliminar un item del carrito
@carrito_bp.route('/eliminar_carrito/<int:id>', methods=['GET', 'POST'])
@login_required
def eliminar_carrito(id):
    rol = (current_user.rol).lower()
    item = Carrito.query.get_or_404(id)
    producto = Producto.query.get_or_404(item.id_producto)
    db.session.delete(item)
    db.session.commit()
    flash(f'{producto.nombre_producto} eliminado de tu carrito', category='success')
    return redirect(url_for(rol + '.perfil'))

# Pedir items de carrito
@carrito_bp.route('/pedir_carrito', methods=['POST'])
@login_required
def pedir_carrito():
    rol = str(current_user.rol).lower()
    carrito_items = Carrito.query.filter(Carrito.id_usuario == current_user.id).all()

    if not carrito_items:
        flash('Tu carrito está vacío', 'warning')
        return redirect(url_for(rol + '.perfil'))
        
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
    return redirect(url_for(rol + '.perfil'))
