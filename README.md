# Proyecto Final
Este proyecto es una aplicación web hecha en Flask que permite gestionar proyectos y analizar sitios web en función de librerías JavaScript y criterios de vulnerabilidad.

## Estructura del Proyecto
- `web/`: interfaz web (páginas HTML, login, crear/ver proyectos)
- `api/`: microservicio REST con la lógica y la base de datos
- `chat/`: microservicio que analiza librerías de una URL y evalúa la aceptabilidad

## Base de datos
- Usa **SQLite**
- Ya está incluida en el proyecto (`gestion_proyectos.db`)
  
## Cómo ejecutar el proyecto
### 1. Clona el repositorio
```bash
git clone https://github.com/wescania/Proyecto
cd Proyecto
```

### 2. Crea y activa un entorno virtual (opcional pero recomendable)
```bash
python -m venv venv
venv\Scripts\activate       # En Windows
source venv/bin/activate    # En Mac/Linux
```

### 3. Instala las dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecuta los tres microservicios en terminales separadas:
#### Terminal 1 – API
```bash
cd api
python app.py
```

#### Terminal 2 – Chat
```bash
cd chat
python app.py
```

#### Terminal 3 – Web (interfaz)
```bash
cd web
python app.py
```

### 5. Abre en el navegador
```
http://localhost:5000
```

## Accesos predefinidos
Puedes iniciar sesión con:

- **Admin:**  
  `admin@admin.com`  
  `admin`

- **Usuario normal:**  
  `user@user.com`  
  `user`

---

## Requisitos técnicos
- Python 3.10 o superior
- Paquetes: Flask, SQLAlchemy, requests, flask-login, flask-cors, flask-restful, flask-praetorian, nvdlib

---
