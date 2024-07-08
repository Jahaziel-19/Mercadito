from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_migrate import Migrate
from models import User, Carrera, Producto, Pedido, Admin
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

import os

app = Flask(__name__)
app.config.from_object(Config)

app.app_context().push()
db.init_app(app)
migrate = Migrate(app, db, render_as_batch=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    admin = Admin.query.get(user_id)

    if user:
        return user
    elif admin:
        return admin
    else:
        return None

    '''

    '''



# ---------------------  RUTAS -----------------------
@app.route('/', methods=['POST', 'GET'])
def home():
    return render_template('home.html')

# --------------- User -----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id = request.form['id']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form['apellido_materno']
        carrera = request.form['carrera']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        foto_perfil = request.files['foto_perfil']

        if foto_perfil and foto_perfil.filename != '':
            filename = secure_filename(foto_perfil.filename)
            foto_perfil.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        else:
            foto_path = 'static/default_profile_pic.png'

        nuevo_usuario = User(
            id=id,
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            carrera=carrera,
            email=email,
            password_hash=password,
            foto_perfil=foto_path
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        return redirect(url_for('login'))

    carreras = Carrera.query.all()
    return render_template('register.html', carreras=carreras)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        usuario = User.query.filter_by(email=correo).first()
        if usuario and check_password_hash(usuario.password_hash, contraseña):
            login_user(usuario)
            return redirect(url_for('productos_servicios'))
        else:
            flash('Usuario o contraseña incorrectos')    
    return render_template('login.html')

@app.route('/profile', methods=['POST', 'GET'])
def profile():
    return render_template('profile.html')

@app.route('/crear_producto', methods=['POST', 'GET'])
def crear_producto():
    if request.method == 'POST':
        nombre_producto = request.form['nombre_producto']
        descripcion = request.form.get('descripcion', '')
        precio = request.form['precio']
        carrera = request.form['carrera']
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
            imagen_path = 'static/uploads/icon-box.png'
        
        print(f'Path de imagen: {imagen_path}')
        nuevo_producto = Producto(
            nombre_producto=nombre_producto,
            descripcion=descripcion,
            precio=precio,
            carrera=carrera,
            imagen_producto=imagen_path
        )

        db.session.add(nuevo_producto)
        db.session.commit()

        return redirect(url_for('crear_producto'))

    carreras = Carrera.query.all()
    return render_template('crear_producto.html', carreras=carreras)


@app.route('/productos_servicios', methods=['GET'])
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



@app.route('/pedido/<int:producto_id>', methods=['GET', 'POST'])
def pedido(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if request.method == 'POST':
        id_user = current_user.id  # Suponiendo que el usuario está guardado en la sesión
        cantidad = int(request.form['cantidad'])
        sub_total = cantidad * producto.precio
        notas = request.form.get('notas', '')

        nuevo_pedido = Pedido(
            id_producto=producto.id,
            id_user=id_user,
            cantidad=cantidad,
            sub_total=sub_total,
            notas=notas
        )

        db.session.add(nuevo_pedido)
        db.session.commit()

        return redirect(url_for('productos_servicios'))

    return render_template('pedido.html', producto=producto)

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    logout_user()
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)