from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, current_user, login_required
from models import Producto, Carrito, db, Pedido, RolEnum, Carrera, PedidoProducto, Admin, Alumno, Docente, Invitado
from scripts import random_int, roles_required, enviar_correo
from werkzeug.utils import secure_filename
import os
import qrcode
from datetime import datetime

# Reportlab para la generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from flask_mail import Message

productos_bp = Blueprint('productos', __name__)


################################################################
# Rutas para el manejo de productos en la aplicación (GENERAL) #
################################################################

# Visualizar productos
@productos_bp.route('/productos_servicios', methods=['POST', 'GET'])
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
    return render_template('productos/productos_servicios.html',  productos=productos, carreras=carreras, query=query, filter_carrera=filter_carrera)

# Previsualización del producto seleccionado
@productos_bp.route('/previsualizar_producto/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def previsualizar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if request.method == 'POST':
        id_user = current_user.id
        cantidad = int(request.form['cantidad'])
        sub_total = cantidad * producto.precio
        notas = request.form.get('notas', '')

        return render_template('productos/previsualizar_producto.html', producto=producto)

    return render_template('productos/previsualizar_producto.html', producto=producto)



########################################################################
# Rutas para el manejo de productos en la aplicación (ADMINISTRADOR) #
########################################################################

# Crear producto
@productos_bp.route('/crear_producto', methods=['POST', 'GET'])
@login_required
@roles_required(RolEnum.ADMIN.value)
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
            if not os.path.exists(current_app.config['UPLOAD_PRODUCT']):
                os.makedirs(current_app.config['UPLOAD_PRODUCT'])
            imagen_path = os.path.join(current_app.config['UPLOAD_PRODUCT'], filename)
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
    return redirect(url_for('admin.perfil'))

# Editar producto
@productos_bp.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
@login_required
@roles_required(RolEnum.ADMIN.value)
def editar_producto(producto_id):
    if current_user.rol != 'ADMIN':
        return redirect(url_for('index'))
    
    producto = Producto.query.get_or_404(producto_id)
    
    if request.method == 'POST':
        imagen_producto = request.files['imagen_producto']
        if imagen_producto and imagen_producto.filename != '':
            filename = secure_filename(imagen_producto.filename)
            # Crear directorio si no existe
            if not os.path.exists(current_app.config['UPLOAD_PRODUCT']):
                os.makedirs(current_app.config['UPLOAD_PRODUCT'])
            imagen_path = os.path.join(current_app.config['UPLOAD_PRODUCT'], filename)
            imagen_producto.save(imagen_path)
            imagen_path.replace('\\', '/')
        else:
            imagen_path = producto.imagen_producto

        producto.imagen_producto = imagen_path
        producto.nombre_producto = request.form['nombre_producto']
        producto.precio = request.form['precio']
        producto.descripcion = request.form['descripcion']
        
        if str(str(request.form.get('numero_medida', None)) and request.form.get('medida', None)):
            producto.medida = str(str(request.form.get('numero_medida', None)) + request.form.get('medida', None))
        else: 
            producto.medida = ""
        
        
        db.session.commit()
        flash(f'¡{producto.nombre_producto} editado!', category='success')
        return redirect(url_for('admin.perfil'))
    
    return render_template('productos/editar_producto.html', producto=producto)

# Eliminar producto
@productos_bp.route('/eliminar_producto/<int:producto_id>', methods=['GET', 'POST'])
@login_required
@roles_required(RolEnum.ADMIN.value)
def eliminar_producto(producto_id):
    if current_user.rol != 'ADMIN':
        return redirect(url_for('index'))
    
    producto = Producto.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    
    return redirect(url_for('admin.perfil'))