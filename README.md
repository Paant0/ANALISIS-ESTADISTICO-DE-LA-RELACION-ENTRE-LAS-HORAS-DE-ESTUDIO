# Horas de estudio y rendimiento académico

Aplicación local para el proyecto conjunto de Ciencia de Datos y Estadística Descriptiva.

## Requisitos
- Python 3.10 o superior
- Conexión a internet al abrir el dashboard para cargar Plotly.js y las fuentes visuales desde CDN.

## Instalación
Abre una terminal dentro de la carpeta `Proyecto_Horas_Estudio` y ejecuta:

```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Windows CMD:
```cmd
.venv\Scripts\activate.bat
```

Instala las librerías:
```bash
pip install -r requirements.txt
```

Inicia la aplicación:
```bash
python app.py
```

Abre en el navegador:
http://127.0.0.1:5000

## Archivos
- `app.py`: carga, limpieza, filtros, cálculos estadísticos y rutas web.
- `templates/index.html`: estructura del dashboard y gráficos interactivos.
- `static/style.css`: estilos visuales y adaptación a móviles.
- `.gitignore`: excluye archivos temporales, entornos locales y la base CSV generada.
- `data/datos_originales.xlsx`: archivo Excel fuente.
- `data/datos_limpios.csv`: base depurada generada al iniciar la aplicación; no se incluye en Git.

## Qué hace
- Elimina filas completamente duplicadas.
- Recorta espacios en campos de texto.
- Convierte horas de estudio y CGPA a variables numéricas.
- Conserva la base completa depurada y excluye del análisis central únicamente registros sin horas o CGPA.
- Calcula estadísticas descriptivas, tablas agrupadas, regresión lineal, Pearson y probabilidades.
- Recalcula resultados al cambiar filtros.
- Presenta tres preguntas de análisis y sus hallazgos sobre horas de estudio, CGPA y probabilidad conjunta; los resultados respetan los filtros.
- Incluye gráficos de barras, histogramas y una ojiva.
- Muestra medidas de probabilidad para `A` (horas de estudio mayores o iguales a la mediana filtrada) y `B` (CGPA mayor o igual a la mediana filtrada). La pregunta 03 usa los umbrales de 3 horas y CGPA 3,21.
- Distingue la unión observada de la unión calculada bajo el supuesto de independencia: `P(A ∪ B) = P(A) + P(B) − P(A) · P(B)`.
- Permite explorar los registros depurados en una tabla paginada de 25 filas que responde a los filtros generales.
- Permite descargar la base limpia completa y los registros filtrados.

## Nota metodológica
La frecuencia relativa acumulada `Hi` se calcula como la suma acumulada de `hi`, no como una suma acumulada de `Fi`. Las medidas descriptivas principales se calculan con los datos individuales. Las tablas agrupadas resumen la distribución en intervalos y no sustituyen los cálculos no agrupados. Los hallazgos son descriptivos y no demuestran causalidad.

La fecha de consulta que aparece en el dashboard corresponde al dato de referencia del proyecto; actualizarla si se consulta nuevamente la fuente.
