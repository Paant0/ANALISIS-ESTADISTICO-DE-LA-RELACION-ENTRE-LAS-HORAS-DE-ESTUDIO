from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import io
import json

app = Flask(__name__)
BASE = Path(__file__).resolve().parent
ARCHIVO = BASE / "data" / "datos_originales.xlsx"

# Nombres originales de las columnas del conjunto de datos
COL_HORAS = "How many hour do you study daily?"
COL_CGPA = "What is your current CGPA?"
COL_PROGRAMA = "Program"
COL_GENERO = "Gender"

def cargar_datos():
    """Lee el Excel original y realiza una limpieza sencilla y reproducible."""
    datos = pd.read_excel(ARCHIVO)

    # Quitar espacios al inicio/final en las columnas de texto
    for columna in datos.select_dtypes(include=["object", "string"]).columns:
        datos[columna] = datos[columna].astype("string").str.strip()

    # Eliminar filas completamente duplicadas
    datos = datos.drop_duplicates().reset_index(drop=True)

    # Convertir las dos variables principales a formato numérico
    datos[COL_HORAS] = pd.to_numeric(datos[COL_HORAS], errors="coerce")
    datos[COL_CGPA] = pd.to_numeric(datos[COL_CGPA], errors="coerce")

    # Normalizar valores vacíos de la variable categórica de habilidades
    if "What are the skills do you have ?" in datos.columns:
        datos["What are the skills do you have ?"] = datos[
            "What are the skills do you have ?"
        ].fillna("No especificado")

    return datos

DATOS = cargar_datos()
DATOS.to_csv(BASE / "data" / "datos_limpios.csv", index=False, encoding="utf-8-sig")

def filtrar_datos(horas_min=None, horas_max=None, programa="Todos", genero="Todos"):
    """Aplica los filtros elegidos por el usuario."""
    datos = DATOS.dropna(subset=[COL_HORAS, COL_CGPA]).copy()
    if horas_min is not None:
        datos = datos[datos[COL_HORAS] >= float(horas_min)]
    if horas_max is not None:
        datos = datos[datos[COL_HORAS] <= float(horas_max)]
    if programa != "Todos":
        datos = datos[datos[COL_PROGRAMA].astype(str) == programa]
    if genero != "Todos":
        datos = datos[datos[COL_GENERO].astype(str) == genero]
    return datos.reset_index(drop=True)

def tabla_frecuencias(serie):
    """Construye una tabla de frecuencias agrupadas con la regla de Sturges."""
    serie = pd.to_numeric(serie, errors="coerce").dropna()
    n = len(serie)
    if n == 0:
        return []
    k = max(1, int(np.ceil(1 + 3.322 * np.log10(n))))
    minimo, maximo = float(serie.min()), float(serie.max())
    if minimo == maximo:
        bordes = np.array([minimo - 0.5, maximo + 0.5])
    else:
        bordes = np.linspace(minimo, maximo, k + 1)
    fi, bordes = np.histogram(serie, bins=bordes)
    hi = fi / n
    Fi = np.cumsum(fi)
    Hi = np.cumsum(hi)  # Frecuencia relativa acumulada correcta
    filas = []
    for i in range(len(fi)):
        filas.append({
            "intervalo": f"{bordes[i]:.2f} – {bordes[i+1]:.2f}",
            "li": round(float(bordes[i]), 3),
            "ls": round(float(bordes[i+1]), 3),
            "marca": round(float((bordes[i] + bordes[i+1]) / 2), 3),
            "fi": int(fi[i]),
            "hi": round(float(hi[i]), 4),
            "Fi": int(Fi[i]),
            "Hi": round(float(Hi[i]), 4)
        })
    return filas

def resumen(serie):
    serie = pd.to_numeric(serie, errors="coerce").dropna()
    if len(serie) == 0:
        return {}
    moda = serie.mode()
    media = serie.mean()
    de = serie.std(ddof=1)
    return {
        "n": int(serie.count()),
        "media": float(media),
        "mediana": float(serie.median()),
        "moda": ", ".join(f"{x:g}" for x in moda.tolist()),
        "q1": float(serie.quantile(.25)),
        "q2": float(serie.quantile(.50)),
        "q3": float(serie.quantile(.75)),
        "varianza": float(serie.var(ddof=1)),
        "desviacion": float(de),
        "cv": float(de / abs(media) * 100) if media != 0 else None,
        "min": float(serie.min()),
        "max": float(serie.max())
    }

def analizar(datos):
    if len(datos) < 3:
        return {"error": "No hay suficientes registros para realizar el análisis. Amplía los filtros."}

    horas = datos[COL_HORAS].astype(float)
    cgpa = datos[COL_CGPA].astype(float)
    rh = resumen(horas)
    rc = resumen(cgpa)
    horas_1_a_4 = (horas >= 1) & (horas <= 4)
    cgpa_mayor_3 = (cgpa > 3) & (cgpa <= 4)

    # Regresión lineal por mínimos cuadrados y correlación de Pearson
    if horas.nunique() > 1 and cgpa.nunique() > 1:
        regresion = stats.linregress(horas, cgpa)
        pendiente, intercepto = float(regresion.slope), float(regresion.intercept)
        r, p_reg = float(regresion.rvalue), float(regresion.pvalue)
        r2 = r ** 2
    else:
        pendiente = intercepto = r = p_reg = r2 = 0.0

    # Eventos de probabilidad: valores iguales o superiores a la mediana filtrada
    umbral_h = float(horas.median())
    umbral_c = float(cgpa.median())
    A = horas >= umbral_h
    B = cgpa >= umbral_c
    pA, pB = float(A.mean()), float(B.mean())
    pAB = float((A & B).mean())
    pUnion = float((A | B).mean())
    producto = pA * pB

    # Probabilidad de los eventos definidos en la pregunta de análisis
    evento_horas = horas >= 3
    evento_cgpa = cgpa >= 3.21
    pregunta_probabilidad = {
        "pA": float(evento_horas.mean()),
        "pB": float(evento_cgpa.mean()),
        "pInterseccion": float((evento_horas & evento_cgpa).mean()),
        "producto": float(evento_horas.mean() * evento_cgpa.mean())
    }

    # Comparación sencilla de CGPA en tres rangos de horas
    rangos = [-np.inf, 2, 4, np.inf]
    etiquetas = ["0–2 horas", "3–4 horas", "5 o más horas"]
    grupos = pd.cut(horas, bins=rangos, labels=etiquetas, include_lowest=True)
    comparacion = []
    for etiqueta in etiquetas:
        sub = cgpa[grupos == etiqueta]
        comparacion.append({
            "grupo": etiqueta,
            "cantidad": int(sub.count()),
            "promedio": float(sub.mean()) if len(sub) else None,
            "mediana": float(sub.median()) if len(sub) else None,
            "porcentaje": float(len(sub) / len(datos) * 100)
        })

    return {
        "n": len(datos), "horas": rh, "cgpa": rc,
        "horas_1_a_4": {
            "cantidad": int(horas_1_a_4.sum()),
            "porcentaje": float(horas_1_a_4.mean() * 100)
        },
        "cgpa_mayor_3": {
            "cantidad": int(cgpa_mayor_3.sum()),
            "porcentaje": float(cgpa_mayor_3.mean() * 100)
        },
        "regresion": {"pendiente": pendiente, "intercepto": intercepto, "r": r, "r2": r2, "p": p_reg},
        "probabilidad": {"pA": pA, "pB": pB,
                         "pAB": pAB, "pUnion": pUnion, "producto": producto},
        "pregunta_probabilidad": pregunta_probabilidad,
        "comparacion": comparacion,
        "tabla_horas": tabla_frecuencias(horas),
        "tabla_cgpa": tabla_frecuencias(cgpa)
    }

def preparar_respuesta(datos):
    resultado = analizar(datos)
    if "error" in resultado:
        return resultado

    horas = datos[COL_HORAS].astype(float)
    cgpa = datos[COL_CGPA].astype(float)
    # Datos de gráficos
    bins_h = np.histogram_bin_edges(horas, bins="sturges")
    hist_h, edges_h = np.histogram(horas, bins=bins_h)
    hist_c, edges_c = np.histogram(cgpa, bins="sturges")

    resultado["graficos"] = {
        "barras_horas": {"x": [x["intervalo"] for x in resultado["tabla_horas"]], "y": [x["fi"] for x in resultado["tabla_horas"]]},
        "hist_horas": {"x": [round(float((edges_h[i]+edges_h[i+1])/2), 2) for i in range(len(hist_h))], "y": hist_h.tolist(), "ancho": [float(edges_h[i+1]-edges_h[i]) for i in range(len(hist_h))]},
        "ojiva_horas": {"x": [x["ls"] for x in resultado["tabla_horas"]], "y": [x["Fi"] for x in resultado["tabla_horas"]]},
        "hist_cgpa": {"x": [round(float((edges_c[i]+edges_c[i+1])/2), 3) for i in range(len(hist_c))], "y": hist_c.tolist(), "ancho": [float(edges_c[i+1]-edges_c[i]) for i in range(len(hist_c))]}
    }
    return resultado

@app.route("/")
def inicio():
    programas = ["Todos"] + sorted(DATOS[COL_PROGRAMA].dropna().astype(str).unique().tolist())
    generos = ["Todos"] + sorted(DATOS[COL_GENERO].dropna().astype(str).unique().tolist())
    max_horas = int(DATOS[COL_HORAS].max())
    return render_template("index.html", programas=programas, generos=generos, max_horas=max_horas)

@app.route("/api/analisis")
def api_analisis():
    try:
        hmin = request.args.get("hmin", type=float)
        hmax = request.args.get("hmax", type=float)
        programa = request.args.get("programa", "Todos")
        genero = request.args.get("genero", "Todos")
        datos = filtrar_datos(hmin, hmax, programa, genero)
        return jsonify(preparar_respuesta(datos))
    except Exception as error:
        return jsonify({"error": f"No fue posible calcular el análisis: {error}"}), 500

@app.route("/api/datos")
def api_datos():
    try:
        datos = filtrar_datos(
            request.args.get("hmin", type=float),
            request.args.get("hmax", type=float),
            request.args.get("programa", "Todos"),
            request.args.get("genero", "Todos")
        )
        total = len(datos)
        por_pagina = 25
        paginas = max(1, (total + por_pagina - 1) // por_pagina)
        pagina = request.args.get("pagina", default=1, type=int) or 1
        pagina = max(1, min(pagina, paginas))
        inicio = (pagina - 1) * por_pagina
        registros = json.loads(
            datos.iloc[inicio:inicio + por_pagina].to_json(
                orient="records", date_format="iso", force_ascii=False
            )
        )
        return jsonify({
            "columnas": datos.columns.tolist(),
            "registros": registros,
            "total": total,
            "pagina": pagina,
            "paginas": paginas
        })
    except Exception as error:
        return jsonify({"error": f"No fue posible cargar el dataset: {error}"}), 500

@app.route("/descargar")
def descargar():
    datos = filtrar_datos(
        request.args.get("hmin", type=float),
        request.args.get("hmax", type=float),
        request.args.get("programa", "Todos"),
        request.args.get("genero", "Todos")
    )
    salida = io.BytesIO()
    datos.to_csv(salida, index=False, encoding="utf-8-sig")
    salida.seek(0)
    return send_file(salida, mimetype="text/csv", as_attachment=True, download_name="datos_filtrados_limpios.csv")

@app.route("/datos-limpios")
def descargar_limpios():
    return send_file(BASE / "data" / "datos_limpios.csv", as_attachment=True, download_name="datos_limpios.csv")

if __name__ == "__main__":
    print("\\nDashboard disponible en: http://127.0.0.1:5000")
    app.run(debug=True)
