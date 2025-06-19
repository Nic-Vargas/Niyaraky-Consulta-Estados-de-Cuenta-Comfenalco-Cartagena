from flask import Flask, render_template, request, send_file, abort
import pandas as pd
import os
import io
import zipfile

app = Flask(__name__)

# ── RUTAS BÁSICAS ────────────────────────────────────────────────────────────────
DB_PATH      = 'Data/Base Empresas.xlsx'   # Excel con columna DOC_EMPRESA
ZIP_PATH = 'Data/EC.zip'                        # Carpeta con archivos por NIT

# ── CARGA Y LIMPIEZA DEL EXCEL ───────────────────────────────────────────────────
df_base = pd.read_excel(DB_PATH)
df_base.columns = df_base.columns.str.strip()              # quita espacios en encabezados
df_base.rename(columns={'DOC_EMPRESA': 'NIT'}, inplace=True)  # renombramos a 'NIT' interno


# ── RUTA PRINCIPAL ───────────────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def index():
    nit = ''
    resultados = []
    empresa = None

    if request.method == 'POST':
        nit = request.form['nit'].strip()
        fila = df_base[df_base['NIT'].astype(str) == nit]
        if not fila.empty:
            empresa = fila.iloc[0].to_dict()

        with zipfile.ZipFile(ZIP_PATH, 'r') as z:
            for archivo in z.namelist():
                if archivo.endswith(('.xlsx', '.xls')) and nit in archivo:
                    resultados.append({
                        'archivo': archivo,
                        'descargar': f"/descargar_zip_file/{archivo}"
                    })

    return render_template('index.html', nit=nit, empresa=empresa, resultados=resultados)

# ── DESCARGA INDIVIDUAL ──────────────────────────────────────────────────────────
@app.route('/descargar_zip_file/<path:nombre>')
def descargar_zip_file(nombre):
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        if nombre not in z.namelist():
            abort(404)
        data = z.read(nombre)
        return send_file(io.BytesIO(data), as_attachment=True, download_name=os.path.basename(nombre))

# ── DESCARGA ZIP (todos los archivos que contengan ese NIT) ─────────────────────
@app.route('/descargar_zip/<nit>')
def descargar_zip(nit):
    if not os.path.exists(ZIP_PATH):
        abort(404)

    archivos_filtrados = []

    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        for nombre in z.namelist():
            if nombre.endswith(('.xlsx', '.xls')) and nit in nombre:
                archivos_filtrados.append(nombre)

        if not archivos_filtrados:
            abort(404)

        # Crear un ZIP en memoria con solo los archivos que coinciden
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_out:
            for archivo in archivos_filtrados:
                zip_out.writestr(archivo, z.read(archivo))

        buffer.seek(0)

        nombre_zip = f"{nit}_documentos.zip"
        return send_file(buffer, as_attachment=True, download_name=nombre_zip, mimetype='application/zip')

# ── LANZAR SERVIDOR ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))   # Render u otro PaaS usa PORT
    app.run(host='0.0.0.0', port=port, debug=True)
