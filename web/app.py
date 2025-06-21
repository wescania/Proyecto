from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
import requests
from flask import session
import jwt

app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:somos_WESCANIA_24_25@localhost/miappdb"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "supersecret"

# Para ej 3, PRACTICA 4, CREAR LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#Modificado en ej1 pr5
@login_manager.user_loader
def load_user(user_id):
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    # Consulta a la API para obtener los datos del usuario
    response = requests.get(f"http://localhost:5001/api/usuarios/{user_id}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return Usuario(
            id=data["id"],
            nombre=data["nombre"],
            apellidos=data["apellidos"],
            email=data["email"]
        )
    return None

@app.before_request
def comprobar_token():
    # Ignorar ciertas rutas como login, static, etc.
    if request.endpoint in ["login", "static"]:
        return

    token = session.get("access_token")
    if token:
        try:
            # Intenta decodificar el token
            jwt.decode(token, "s3cr3t", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            # Token caducado
            logout_user()
            session.clear()
            flash("Sesión expirada. Por favor, inicia sesión de nuevo.", "warning")
            return redirect(url_for("login"))
        except jwt.InvalidTokenError:
            # Token inválido o manipulado
            logout_user()
            session.clear()
            flash("Sesión inválida. Por favor, inicia sesión de nuevo.", "danger")
            return redirect(url_for("login"))
    else:
        # No hay token y está accediendo a una vista que necesita login
        if request.endpoint not in ["index", "login"]:
            logout_user()
            session.clear()
            flash("Por seguridad, se ha cerrado la sesión.", "info")
            return redirect(url_for("login"))

def es_admin():
    return current_user.is_authenticated and current_user.email == "admin@admin.com"

@app.context_processor
def inject_roles():
    return dict(es_admin=es_admin())

class Usuario(UserMixin):
    def __init__(self, id, nombre, apellidos, email):
        self.id = id
        self.nombre = nombre
        self.apellidos = apellidos
        self.email = email

# Modificado en ej1 pr5
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Solicitar el token al microservicio (NO necesitamos Authorization aquí)
        response = requests.post("http://localhost:5001/api/login", json={
            "email": email,
            "password": password
        })

        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]

            # Decodificamos el token para obtener el id del usuario
            user_info = jwt.decode(token, "s3cr3t", algorithms=["HS256"])
            user_id = user_info["id"]

            # Consultamos al microservicio los datos reales del usuario
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"http://localhost:5001/api/usuarios/{user_id}", headers=headers)

            if response.status_code == 200:
                data = response.json()
                usuario = Usuario(
                    id=user_id,
                    nombre=data["nombre"],
                    apellidos=data["apellidos"],
                    email=data["email"]
                )

                login_user(usuario)
                session["access_token"] = token
                flash("Inicio de sesión correcto.", "success")
                return redirect(url_for("mi_cuenta"))
            else:
                flash("Error al obtener los datos del usuario.", "danger")
                return redirect(url_for("login"))
        else:
            flash("Credenciales incorrectas.", "danger")

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))

# Modificado en ej1 pr5
@app.route("/mi_cuenta")
@login_required
def mi_cuenta():
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    response = requests.get("http://localhost:5001/api/proyectos", headers=headers)
    if response.status_code == 200:
        proyectos = response.json()
        proyectos = [p for p in proyectos if p["usuario_id"] == current_user.id]
        return render_template("mi_cuenta.html", proyectos=proyectos)
    flash("Error al cargar proyectos", "danger")
    return render_template("mi_cuenta.html", proyectos=[])

# Modificado en ej1 pr5
@app.route("/")
def index():
    proyectos = []
    if current_user.is_authenticated:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.get("http://localhost:5001/api/proyectos", headers=headers)
        if response.status_code == 200:
            todos = response.json()
            if es_admin():
                proyectos = todos
            else:
                proyectos = [p for p in todos if p["usuario_id"] == current_user.id]
    return render_template("index.html", proyectos=proyectos)

# Modificado en ej1 pr5
@app.route("/usuarios")
@login_required
def usuarios():
    if not es_admin():
        flash("Acceso denegado. Solo el administrador puede ver esta página.", "danger")
        return redirect(url_for("mi_cuenta"))

    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    response = requests.get("http://localhost:5001/api/usuarios", headers=headers)
    if response.status_code == 200:
        usuarios = response.json()
        return render_template("usuarios.html", usuarios=usuarios)
    flash("Error al cargar usuarios", "danger")
    return render_template("usuarios.html", usuarios=[])

# Modificado en ej1 pr5
@app.route("/usuario/nuevo", methods=["GET", "POST"])
@login_required
def usuario_nuevo():
    if not es_admin():
        flash("Solo el administrador puede crear nuevos usuarios.", "danger")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        data = {
            "nombre": request.form["nombre"],
            "apellidos": request.form["apellidos"],
            "email": request.form["email"],
            "password": request.form["password"]
        }
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.post("http://localhost:5001/api/usuarios", headers=headers, json=data)

        if response.status_code == 201:
            flash("Usuario creado con éxito. Inicia sesión desde 'Mi cuenta'.", "success")
            return redirect(url_for("usuarios"))
        elif response.status_code == 400:
            flash("Ese correo ya está registrado. Por favor, usa otro.", "danger")
            return redirect(url_for("usuario_nuevo"))
        else:
            flash("Error al crear usuario.", "danger")

    return render_template("usuarios_form.html", accion="Crear", usuario=None)

# Modificado en ej1 pr5
@app.route("/usuario/<int:id>/editar", methods=["GET", "POST"])
@login_required
def usuario_editar(id):
    url = f"http://localhost:5001/api/usuarios/{id}"

    if request.method == "POST":
        data = {
            "nombre": request.form["nombre"],
            "apellidos": request.form["apellidos"],
            "email": request.form["email"],
            "password": request.form["password"]
        }
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 200:
            flash("Usuario actualizado con éxito.", "success")
            return redirect(url_for("usuarios"))
        else:
            flash("Error al actualizar usuario.", "danger")

    # GET actual
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        usuario = response.json()
        return render_template("usuarios_form.html", accion="Editar", usuario=usuario)
    else:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("usuarios"))

# Modificado en ej1 pr5
@app.route("/usuario/<int:id>/borrar", methods=["POST"])
@login_required
def usuario_borrar(id):
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    response = requests.delete(f"http://localhost:5001/api/usuarios/{id}", headers=headers)
    if response.status_code == 200:
        flash("Usuario eliminado correctamente.", "success")
    else:
        flash("Error al eliminar usuario.", "danger")
    return redirect(url_for("usuarios"))

#Modificado en ej1 pr5
@app.route("/proyectos/")
@login_required
def proyectos():
    proyectos = []
    usuarios = {}

    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    # Obtener todos los proyectos
    response = requests.get("http://localhost:5001/api/proyectos", headers=headers)
    if response.status_code != 200:
        flash("Error al conectar con la API de proyectos.", "danger")
        return render_template("proyectos.html", proyectos=[], usuarios={})

    todos = response.json()

    # Si no es admin, filtrar por los del usuario actual
    if not es_admin():
        proyectos = [p for p in todos if p["usuario_id"] == current_user.id]
    else:
        proyectos = todos
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        # Cargar todos los usuarios solo si eres admin
        usuarios_response = requests.get("http://localhost:5001/api/usuarios", headers=headers)
        if usuarios_response.status_code == 200:
            usuarios_lista = usuarios_response.json()
            # Crear diccionario {id: usuario} para lookup rápido en la plantilla
            usuarios = {u["id"]: u for u in usuarios_lista}

    return render_template("proyectos.html", proyectos=proyectos, usuarios=usuarios)

#Modificado en ej1 pr5
@app.route("/proyecto/<int:id>")
def proyecto(id):
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    response = requests.get(f"http://localhost:5001/api/proyectos/{id}", headers=headers)
    if response.status_code == 200:
        proyecto = response.json()
        return render_template("proyecto.html", proyecto=proyecto)
    else:
        flash("Proyecto no encontrado.", "danger")
        return redirect(url_for("proyectos"))

#Modificado en ej1 pr5
@app.route("/proyectos/crear", methods=["GET", "POST"])
@login_required
def proyecto_nuevo():
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        fecha = request.form["fecha"]

        # Llamamos a la API
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.post("http://localhost:5001/api/proyectos", headers=headers, json={
            "name": nombre,
            "description": descripcion,
            "fecha": fecha,
            "usuario_id": current_user.id,
            "max_criticas": request.form.get("max_criticas", 3),
            "max_medias": request.form.get("max_medias", 5),
            "score_critico": request.form.get("score_critico", 9.0),
            "score_medio": request.form.get("score_medio", 5.0),
            "umbral_solucionabilidad": request.form.get("umbral_solucionabilidad", 80.0),
            "max_total_vulnerabilidades": request.form.get("max_total_vulnerabilidades", 10),
            "nivel_maximo_cvss": request.form.get("nivel_maximo_cvss", 9.0)
        })

        if response.status_code == 201:
            proyecto_id = response.json()["id"]
            return redirect(url_for("chat_id", id_proyecto=proyecto_id))
        else:
            flash("Error al crear el proyecto.", "danger")

    return render_template("proyecto_form.html", accion="Crear", proyecto=None)

#Modificado en ej1 pr5
@app.route("/proyecto/<int:id>/borrar", methods=["POST"])
def proyecto_borrar(id):
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    response = requests.delete(f"http://localhost:5001/api/proyectos/{id}", headers=headers)
    if response.status_code == 200:
        flash("Proyecto eliminado correctamente.", "success")
    else:
        flash("Error al eliminar el proyecto.", "danger")
    return redirect(url_for("proyectos"))

#Modificado en ej1 pr5
@app.route("/proyecto/<int:id>/editar", methods=["GET", "POST"])
def proyecto_editar(id):
    url = f"http://localhost:5001/api/proyectos/{id}"
    
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        fecha = request.form["fecha"]

        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.put(url, headers=headers, json={
            "name": nombre,
            "description": descripcion,
            "fecha": fecha,
            "max_criticas": request.form.get("max_criticas", 3),
            "max_medias": request.form.get("max_medias", 5),
            "score_critico": request.form.get("score_critico", 9.0),
            "score_medio": request.form.get("score_medio", 5.0),
            "umbral_solucionabilidad": request.form.get("umbral_solucionabilidad", 80.0),
            "max_total_vulnerabilidades": request.form.get("max_total_vulnerabilidades", 10),
            "nivel_maximo_cvss": request.form.get("nivel_maximo_cvss", 9.0)
        })

        if response.status_code == 200:
            flash("Proyecto actualizado correctamente.", "success")
            return redirect(url_for("proyecto", id=id))
        else:
            flash("Error al actualizar el proyecto.", "danger")
    
    # GET (cargar datos actuales)
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        proyecto = response.json()
        return render_template("proyecto_form.html", accion="Editar", proyecto=proyecto)
    else:
        flash("Proyecto no encontrado.", "danger")
        return redirect(url_for("proyectos"))

#Modificado en ej1 pr5
@app.route("/api/proyecto/crear", methods=["POST"])
@login_required
def crear_proyecto_ajax():
    data = request.get_json()
    nombre = data.get("nombre")
    if nombre:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.post("http://localhost:5001/api/proyectos", headers=headers, json={
            "name": nombre,
            "description": "Proyecto creado desde el botón +",
            "fecha": datetime.today().strftime("%Y-%m-%d"),
            "usuario_id": current_user.id,
            "max_criticas": 3,
            "max_medias": 5,
            "score_critico": 9.0,
            "score_medio": 5.0
        })
        if response.status_code == 201:
            proyecto = response.json()
            return jsonify(success=True, id=proyecto["id"], nombre=proyecto["name"])
    return jsonify(success=False), 400


# Modificado en ej1 pr5
@app.route("/chat/<int:id_proyecto>")
@login_required
def chat_id(id_proyecto):
    # Obtener info del proyecto desde la API
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    response = requests.get(f"http://localhost:5001/api/proyectos/{id_proyecto}", headers=headers)
    if response.status_code != 200:
        flash("No se pudo obtener el proyecto.", "danger")
        return redirect(url_for("index"))
    proyecto = response.json()

    # Verificar permisos de acceso
    if proyecto["usuario_id"] != current_user.id and not es_admin():
        flash("No tienes permisos para acceder a este proyecto", "danger")
        return redirect(url_for("index"))

    # Obtener todos los proyectos del usuario (para la lista lateral)
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    todos_response = requests.get("http://localhost:5001/api/proyectos", headers=headers)
    if todos_response.status_code != 200:
        flash("Error cargando lista de proyectos", "danger")
        return redirect(url_for("index"))
    proyectos = todos_response.json()
    if not es_admin():
        proyectos = [p for p in proyectos if p["usuario_id"] == current_user.id]

    # Obtener mensajes del proyecto
    headers = {"Authorization": f"Bearer {session.get('access_token')}"}
    msg_response = requests.get(f"http://localhost:5001/api/proyectos/{id_proyecto}/mensajes", headers=headers)
    if msg_response.status_code == 200:
        mensajes = msg_response.json()
    else:
        mensajes = []
        flash("No se pudieron cargar los mensajes del proyecto.", "danger")

    # Si es admin, obtener datos del usuario dueño del proyecto
    usuario_info = {}
    if es_admin():
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        user_response = requests.get(f"http://localhost:5001/api/usuarios/{proyecto['usuario_id']}", headers=headers)
        if user_response.status_code == 200:
            usuario_info = user_response.json()

    return render_template("chat.html", proyectos=proyectos, mensajes=mensajes, project=proyecto, usuario_info=usuario_info)

# Modificado en ej1 pr5
@app.route("/mensaje", methods=["POST"])
def guardar_mensaje():
    data = request.get_json()
    contenido = data.get("contenido")
    project_id = data.get("project_id")
    autor = data.get("autor", "usuario")

    if contenido and project_id:
        headers = {"Authorization": f"Bearer {session.get('access_token')}"}
        response = requests.post(f"http://localhost:5001/api/proyectos/{project_id}/mensajes", headers=headers, json={
            "contenido": contenido,
            "autor": autor
        })
        if response.status_code == 201:
            return jsonify(success=True), 200
        else:
            return jsonify({"error": "Error al guardar mensaje"}), 500
    else: 
        return jsonify({"error": "Datos incompletos"}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
