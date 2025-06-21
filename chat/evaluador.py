import nvdlib

def contar_vulnerabilidades(libreria, score_critico=9.0, score_medio=5.0):
    # busca vulnerabilidades reales por nombre de librería
    criticas = 0
    medias = 0
    solucionables = 0
    total = 0
    max_cvss = 0

    try:
        resultados = nvdlib.searchCVE(keywordSearch=libreria, limit=20)
    except Exception as e:
        return (0, 0, 0, 0, 0), f"Error al buscar CVEs para {libreria}: {e}"

    for cve in resultados:
        try:
            metricas = cve.metrics.get('cvssMetricV31') or cve.metrics.get('cvssMetricV30')
            if metricas:
                score = metricas[0].cvssData.baseScore
                max_cvss = max(max_cvss, score)
                total += 1
                # Solucionabilidad: si hay al menos una solución documentada
                solucion = False
                if hasattr(cve, 'configurations') and cve.configurations:
                    solucion = True
                if hasattr(cve, 'weaknesses') and cve.weaknesses:
                    solucion = True
                if hasattr(cve, 'references') and cve.references:
                    for ref in cve.references:
                        if 'Patch' in ref.get('tags', []) or 'Vendor Advisory' in ref.get('tags', []):
                            solucion = True
                if solucion:
                    solucionables += 1
                if score >= score_critico:
                    criticas += 1
                elif score >= score_medio:
                    medias += 1
        except:
            continue

    return (criticas, medias, solucionables, total, max_cvss), None

def evaluar_sitio(librerias, criterios):
    # aplica los criterios definidos por el usuario para este proyecto
    total_criticas = 0
    total_medias = 0
    total_solucionables = 0
    total_vulns = 0
    max_cvss = 0
    errores = []

    for lib in librerias:
        (c, m, s, t, max_lib_cvss), error = contar_vulnerabilidades(lib, criterios["score_critico"], criterios["score_medio"])
        if error:
            errores.append(error)
        total_criticas += c
        total_medias += m
        total_solucionables += s
        total_vulns += t
        max_cvss = max(max_cvss, max_lib_cvss)

    # Criterio 1: solucionabilidad
    porcentaje_solucionables = (total_solucionables / total_vulns * 100) if total_vulns > 0 else 100
    criterio_solucionabilidad = porcentaje_solucionables >= criterios.get("umbral_solucionabilidad", 80.0)

    # Criterio 2: número total
    criterio_total = total_vulns <= criterios.get("max_total_vulnerabilidades", 10)

    # Criterio 3: nivel máximo
    criterio_nivel = max_cvss <= criterios.get("nivel_maximo_cvss", 9.0)

    # Criterio 4: cálculo combinado (todos deben cumplirse)
    criterio_criticas = total_criticas <= criterios.get("max_criticas", 3)
    criterio_medias = total_medias <= criterios.get("max_medias", 5)
    criterio_comb = all([
        criterio_solucionabilidad,
        criterio_total,
        criterio_nivel,
        criterio_criticas,
        criterio_medias
    ])

    return {
        "criticas": total_criticas,
        "medias": total_medias,
        "total_vulnerabilidades": total_vulns,
        "solucionables": total_solucionables,
        "porcentaje_solucionables": porcentaje_solucionables,
        "max_cvss": max_cvss,
        "criterio_solucionabilidad": criterio_solucionabilidad,
        "criterio_total": criterio_total,
        "criterio_nivel": criterio_nivel,
        "criterio_criticas": criterio_criticas,
        "criterio_medias": criterio_medias,
        "aceptable": criterio_comb,
        "errores": errores
    }
