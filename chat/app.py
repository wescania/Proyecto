from flask import Flask, request, jsonify
from flask_cors import CORS

from extractor import extraer_librerias_js
from evaluador import evaluar_sitio
from utils import obtener_criterios_proyecto

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST"])
def responder():
    data = request.get_json()
    mensaje = data.get("mensaje", "")
    project_id = data.get("project_id")

    if not mensaje.startswith("http"):
        return jsonify({"respuesta": "Por favor, proporciona una URL válida que empiece por http o https."})

    # Extraer librerías de la URL
    librerias, error = extraer_librerias_js(mensaje)
    if error:
        return jsonify({"respuesta": f"No se pudo analizar la URL: {error}"})

    # Obtener criterios del proyecto
    criterios = obtener_criterios_proyecto(project_id)
    if not criterios:
        return jsonify({"respuesta": "No se pudieron obtener los criterios del proyecto."})

    # Evaluar
    resultado = evaluar_sitio(librerias, criterios)

    texto = f"""
    <strong>Análisis de:</strong> <code>{mensaje}</code><br>
    <strong>Librerías detectadas:</strong> {', '.join(librerias) or 'ninguna'}<br>
    <strong>Vulnerabilidades críticas:</strong> {resultado['criticas']}<br>
    <strong>Vulnerabilidades medias:</strong> {resultado['medias']}<br>
    <strong>Total vulnerabilidades:</strong> {resultado['total_vulnerabilidades']}<br>
    <strong>Vulnerabilidades solucionables:</strong> {resultado['solucionables']}<br>
    <strong>% Solucionables:</strong> {resultado['porcentaje_solucionables']:.1f}%<br>
    <strong>CVSS máximo detectado:</strong> {resultado['max_cvss']}<br>
    <strong>Criterio solucionabilidad:</strong> {"✅" if resultado['criterio_solucionabilidad'] else "❌"}<br>
    <strong>Criterio total vulnerabilidades:</strong> {"✅" if resultado['criterio_total'] else "❌"}<br>
    <strong>Criterio nivel máximo:</strong> {"✅" if resultado['criterio_nivel'] else "❌"}<br>
    <strong>Criterio máx. críticas:</strong> {"✅" if resultado['criterio_criticas'] else "❌"}<br>
    <strong>Criterio máx. medias:</strong> {"✅" if resultado['criterio_medias'] else "❌"}<br>
    <strong>Resultado combinado:</strong> {"✅ ACEPTABLE" if resultado["aceptable"] else "❌ NO ACEPTABLE"}
    """

    return jsonify({"respuesta": texto})

if __name__ == "__main__":
    app.run(debug=True, port=5002)
