import requests
#con esto nos conectamos con la API de proyectos para obtener los criterios de evaluación de ese proyecto

def obtener_criterios_proyecto(project_id):
    try:
        respuesta = requests.get(f"http://localhost:5001/api/proyectos/{project_id}")
        if respuesta.status_code == 200:
            datos = respuesta.json()
            return {
                "max_criticas": datos.get("max_criticas", 3),
                "max_medias": datos.get("max_medias", 5),
                "score_critico": datos.get("score_critico", 9.0),
                "score_medio": datos.get("score_medio", 5.0),
            }
    except Exception as e:
        print("Error al obtener criterios:", e)
    return None
