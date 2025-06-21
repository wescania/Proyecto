# api/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_cors import CORS
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import flask_praetorian
from flask_praetorian import Praetorian, auth_required, current_user

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "s3cr3t" #Clave secreta
app.config["SECRET_KEY"] = "s3cr3t" #Clave secreta para Flask
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://flask_user:password123@localhost/gestion_proyectos"
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:somos_WESCANIA_24_25@localhost/miappdb"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gestion_proyectos.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
api = Api(app)
CORS(app)  # Para permitir llamadas desde otros orígenes

# MODELOS
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    fecha = db.Column(db.Date, nullable=False)
    usuario_id = db.Column(db.Integer, nullable=False)
    fecha_modificacion = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Nuevos criterios de aceptabilidad
    max_criticas = db.Column(db.Integer, default=3)         # Máx. vulnerabilidades críticas permitidas
    max_medias = db.Column(db.Integer, default=5)           # Máx. medias
    score_critico = db.Column(db.Float, default=9.0)        # A partir de qué CVSS es crítica
    score_medio = db.Column(db.Float, default=5.0)          # A partir de qué CVSS es media
    # Nuevos criterios solicitados
    umbral_solucionabilidad = db.Column(db.Float, default=80.0) # % mínimo de vulnerabilidades solucionables
    max_total_vulnerabilidades = db.Column(db.Integer, default=10) # Máximo total de vulnerabilidades
    nivel_maximo_cvss = db.Column(db.Float, default=9.0) # CVSS máximo permitido

class Mensaje(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, server_default=db.func.now())
    project_id = db.Column(db.Integer, nullable=False)
    autor = db.Column(db.String(20), nullable=False)  # "usuario" o "bot"

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    roles = db.Column(db.Text, default='user')  # roles como texto plano

    @classmethod
    def lookup(cls, email):
        return cls.query.filter_by(email=email).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def rolenames(self):
        return self.roles.split(',') if self.roles else []

    @property
    def identity(self):
        return self.id
    
guard = Praetorian()
guard.init_app(app, Usuario)

# RECURSOS (endpoints RESTful)
class ProjectListResource(Resource):
    @auth_required
    def get(self):
        projects = Project.query.all()
        return [{
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "fecha": str(p.fecha),
            "usuario_id": p.usuario_id,
            "fecha_modificacion": str(p.fecha_modificacion) if p.fecha_modificacion else None,
            "max_criticas": p.max_criticas,
            "max_medias": p.max_medias,
            "score_critico": p.score_critico,
            "score_medio": p.score_medio,
            "umbral_solucionabilidad": p.umbral_solucionabilidad,
            "max_total_vulnerabilidades": p.max_total_vulnerabilidades,
            "nivel_maximo_cvss": p.nivel_maximo_cvss
        } for p in projects]

    @auth_required
    def post(self):
        data = request.get_json()

        nuevo_proyecto = Project(
            name=data["name"],
            description=data.get("description"),
            fecha=datetime.strptime(data["fecha"], "%Y-%m-%d"),
            usuario_id=data["usuario_id"],

            # Nuevos campos de criterios de aceptabilidad
            max_criticas=data.get("max_criticas", 3),
            max_medias=data.get("max_medias", 5),
            score_critico=data.get("score_critico", 9.0),
            score_medio=data.get("score_medio", 5.0),
            umbral_solucionabilidad=data.get("umbral_solucionabilidad", 80.0),
            max_total_vulnerabilidades=data.get("max_total_vulnerabilidades", 10),
            nivel_maximo_cvss=data.get("nivel_maximo_cvss", 9.0),
        )

        db.session.add(nuevo_proyecto)
        db.session.commit()

        return {"mensaje": "Proyecto creado correctamente", "id": nuevo_proyecto.id}, 201

class ProjectResource(Resource):
    def get(self, project_id):
        p = Project.query.get_or_404(project_id)
        return {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "fecha": str(p.fecha),
            "usuario_id": p.usuario_id,
            "fecha_modificacion": str(p.fecha_modificacion) if p.fecha_modificacion else None,
            "max_criticas": p.max_criticas,
            "max_medias": p.max_medias,
            "score_critico": p.score_critico,
            "score_medio": p.score_medio,
            "umbral_solucionabilidad": p.umbral_solucionabilidad,
            "max_total_vulnerabilidades": p.max_total_vulnerabilidades,
            "nivel_maximo_cvss": p.nivel_maximo_cvss
        }

    def put(self, project_id):
        p = Project.query.get_or_404(project_id)
        data = request.get_json()
        p.name = data["name"]
        p.description = data["description"]
        p.fecha = datetime.strptime(data["fecha"], "%Y-%m-%d")
        p.max_criticas = data.get("max_criticas", 3)
        p.max_medias = data.get("max_medias", 5)
        p.score_critico = data.get("score_critico", 9.0)
        p.score_medio = data.get("score_medio", 5.0)
        p.umbral_solucionabilidad = data.get("umbral_solucionabilidad", 80.0)
        p.max_total_vulnerabilidades = data.get("max_total_vulnerabilidades", 10)
        p.nivel_maximo_cvss = data.get("nivel_maximo_cvss", 9.0)
        db.session.commit()
        return {"message": "Proyecto actualizado"}

    def delete(self, project_id):
        p = Project.query.get_or_404(project_id)
        db.session.delete(p)
        db.session.commit()
        return {"message": "Proyecto eliminado"}
    
class MensajeListResource(Resource):
    def get(self, project_id):
        mensajes = Mensaje.query.filter_by(project_id=project_id).order_by(Mensaje.fecha).all()
        return [{
            "id": m.id,
            "contenido": m.contenido,
            "fecha": str(m.fecha),
            "project_id": m.project_id,
            "autor": m.autor
        } for m in mensajes]

    def post(self, project_id):
        data = request.get_json()
        mensaje = Mensaje(
            contenido=data["contenido"],
            project_id=project_id,
            autor=data.get("autor", "usuario")
        )
        db.session.add(mensaje)
        db.session.commit()
        return {"message": "Mensaje guardado"}, 201

def check(password, hashed):
    return check_password_hash(hashed, password)

class UsuarioListResource(Resource):
    def get(self):
        usuarios = Usuario.query.all()
        return [{
            "id": u.id,
            "nombre": u.nombre,
            "apellidos": u.apellidos,
            "email": u.email
        } for u in usuarios]

    def post(self):
        data = request.get_json()
        if Usuario.query.filter_by(email=data["email"]).first():
            return {"error": "Email ya registrado"}, 400

        nuevo = Usuario(
            nombre=data["nombre"],
            apellidos=data["apellidos"],
            email=data["email"],
            password=hash(data["password"])
        )
        db.session.add(nuevo)
        db.session.commit()
        return {"message": "Usuario creado"}, 201

class UsuarioResource(Resource):
    def get(self, id):
        u = Usuario.query.get_or_404(id)
        return {
            "id": u.id,
            "nombre": u.nombre,
            "apellidos": u.apellidos,
            "email": u.email
        }

    def put(self, id):
        u = Usuario.query.get_or_404(id)
        data = request.get_json()
        u.nombre = data["nombre"]
        u.apellidos = data["apellidos"]
        u.email = data["email"]
        if "password" in data:
            u.password = hash(data["password"])
        db.session.commit()
        return {"message": "Usuario actualizado"}

    def delete(self, id):
        u = Usuario.query.get_or_404(id)
        db.session.delete(u)
        db.session.commit()
        return {"message": "Usuario eliminado"}

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = guard.authenticate(email, password)
    token = guard.encode_jwt_token(user)
    return jsonify({"access_token": token})

# RUTAS
api.add_resource(ProjectListResource, "/api/proyectos")
api.add_resource(ProjectResource, "/api/proyectos/<int:project_id>")
api.add_resource(MensajeListResource, "/api/proyectos/<int:project_id>/mensajes")
api.add_resource(UsuarioListResource, "/api/usuarios")
api.add_resource(UsuarioResource, "/api/usuarios/<int:id>")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Crear usuario administrador si no existe
        if not Usuario.query.filter_by(email="admin@admin.com").first():
            admin = Usuario(
                nombre="admin",
                apellidos="admin",
                email="admin@admin.com",
                password=guard.hash_password("admin"),
                roles="admin"  # Asignar rol de administrador
            )
            db.session.add(admin)

        # Crear usuario normal si no existe
        if not Usuario.query.filter_by(email="user@user.com").first():
            user = Usuario(
                nombre="user",
                apellidos="user",
                email="user@user.com",
                password=guard.hash_password("user"),
                roles="user"  # Asignar rol de usuario normal
            )
            db.session.add(user)

        db.session.commit()

    app.run(debug=True, port=5001)
