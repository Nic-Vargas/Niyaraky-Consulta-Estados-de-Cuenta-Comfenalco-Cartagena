from flask import Flask, render_template, request, send_file, abort
import pandas as pd
import os
import io
import zipfile

app = Flask(__name__)

# ── RUTAS BÁSICAS ────────────────────────────────────────────────────────────────
DB_PATH      = 'Data/Base Junio 2025 Final.xlsx'   # Excel con columna DOC_EMPRESA
ARCHIVOS_DIR = 'Data/EC'                                   # Carpeta con archivos por NIT

# ── CARGA Y LIMPIEZA DEL EXCEL ───────────────────────────────────────────────────
df_base = pd.read_excel(DB_PATH, engine="openpyxl")
df_base.columns = df_base.columns.str.strip()              # quita espacios en encabezados
df_base.rename(columns={'DOC_EMPRESA': 'NIT'}, inplace=True)  # renombramos a 'NIT' interno

# ── RUTA PRINCIPAL ───────────────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def index():
    nit       = ''
    resultados = []   # lista de dicts con {'archivo': '/descargar/…', 'nombre': 'archivo.xlsx'}
    empresa   = None  # para mostrar info adicional si existe en el Excel

    if request.method == 'POST':
        nit = request.form['nit'].strip()
        print(f"🔎 Buscando archivos para NIT: {nit}")

        # 1️⃣ Filtrar Excel para mostrar datos de la empresa (opcional)
        fila_excel = df_base[df_base['NIT'].astype(str) == nit]
        if not fila_excel.empty:
            empresa = fila_excel.iloc[0].to_dict()

        # 2️⃣ Buscar archivos que contengan el NIT en su nombre dentro de Data/EC
        for archivo in os.listdir(ARCHIVOS_DIR):
            if archivo.endswith(('.xlsx', '.xls')) and nit in archivo:
                resultados.append({
                    'archivo': f"/descargar/{archivo}",
                    'nombre': archivo
                })

        print(f"📂 Archivos encontrados: {[r['nombre'] for r in resultados]}")

    return render_template(
        'index.html',
        nit=nit,
        empresa=empresa,           # dict o None
        resultados=resultados      # lista de archivos encontrados
    )

# ── DESCARGA INDIVIDUAL ──────────────────────────────────────────────────────────
@app.route('/descargar/<archivo>')
def descargar(archivo):
    ruta = os.path.join(ARCHIVOS_DIR, archivo)
    if os.path.exists(ruta):
        return send_file(ruta, as_attachment=True)
    abort(404)

# ── DESCARGA ZIP (todos los archivos que contengan ese NIT) ─────────────────────
@app.route('/descargar_zip/<nit>')
def descargar_zip(nit):
    archivos = [
        os.path.join(ARCHIVOS_DIR, f)
        for f in os.listdir(ARCHIVOS_DIR)
        if f.endswith(('.xlsx', '.xls')) and nit in f
    ]

    if not archivos:
        abort(404)

    # Crear ZIP en memoria
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        for ruta in archivos:
            z.write(ruta, os.path.basename(ruta))
    buffer.seek(0)

    nombre_zip = f"{nit}_docs.zip"
    return send_file(buffer, as_attachment=True,
                     download_name=nombre_zip,
                     mimetype='application/zip')

# ── LANZAR SERVIDOR ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))   # Render u otro PaaS usa PORT
    app.run(host='0.0.0.0', port=port, debug=True)
