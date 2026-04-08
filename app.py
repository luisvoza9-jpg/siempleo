from flask import Flask, render_template, request, url_for
import pandas as pd
import re
import os
from datetime import datetime, timedelta

app = Flask(__name__)

def crear_url_amigable(texto):
    texto = str(texto).lower()
    texto = re.sub(r'[^a-z0-9\s-]', '', texto) 
    texto = re.sub(r'[\s-]+', '-', texto)      
    return texto

def cargar_datos():
    try:
        df = pd.read_csv("ofertas_clasificadas_valles.csv")
        df = df.fillna("No especificado")
        
        # Limpieza automática (15 días)
        df['Fecha Captura'] = pd.to_datetime(df['Fecha Captura'], errors='coerce')
        fecha_limite = datetime.now() - timedelta(days=15)
        df = df[df['Fecha Captura'] >= fecha_limite]
        df['Fecha Captura'] = df['Fecha Captura'].dt.strftime('%Y-%m-%d')

        slugs = []
        for index, row in df.iterrows():
            base = f"{row.get('Titulo Oferta', 'oferta')} {row.get('Localidad', '')}"
            slug_limpio = crear_url_amigable(base)
            slugs.append(f"{index}-{slug_limpio}") 
            
        df['slug'] = slugs
        return df
    except Exception as e:
        print(f"Error en base de datos: {e}")
        return pd.DataFrame()

@app.route("/")
def index():
    df = cargar_datos()
    
    # --- LA MAGIA: SACAR LISTAS AUTOMÁTICAS PARA LOS MENÚS ---
    pueblos_disponibles = []
    sectores_disponibles = []
    if not df.empty:
        # Extrae los nombres únicos y los ordena alfabéticamente
        pueblos_disponibles = sorted([str(p) for p in df['Localidad'].unique() if str(p) != 'nan' and str(p) != 'No especificado'])
        sectores_disponibles = sorted([str(s) for s in df['Sector Padre'].unique() if str(s) != 'nan' and str(s) != 'No especificado'])
    
    # Filtros desde la web
    q = request.args.get('q', '').lower()
    pueblo = request.args.get('pueblo', '').lower()
    sector = request.args.get('sector', '').lower()
    
    if not df.empty:
        if q:
            df = df[df['Titulo Oferta'].str.lower().str.contains(q)]
        if pueblo:
            df = df[df['Localidad'].str.lower().str.contains(pueblo)]
        if sector:
            df = df[df['Sector Padre'].str.lower().str.contains(sector) | 
                    df['Puesto Especifico'].str.lower().str.contains(sector)]
    
    todas_las_ofertas = df.to_dict(orient='records') if not df.empty else []
    
    # Lógica de Paginación
    POR_PAGINA = 20 
    pagina = request.args.get('page', 1, type=int)
    inicio = (pagina - 1) * POR_PAGINA
    fin = inicio + POR_PAGINA
    ofertas_paginadas = todas_las_ofertas[inicio:fin]
    
    tiene_siguiente = len(todas_las_ofertas) > fin
    tiene_anterior = pagina > 1

    return render_template("index.html", 
                           ofertas=ofertas_paginadas, 
                           busqueda=q,
                           pagina=pagina,
                           siguiente=tiene_siguiente,
                           anterior=tiene_anterior,
                           # Pasamos nuestras nuevas listas automáticas al HTML
                           pueblos_menu=pueblos_disponibles,
                           sectores_menu=sectores_disponibles,
                           pueblo_seleccionado=request.args.get('pueblo', ''),
                           sector_seleccionado=request.args.get('sector', ''))

@app.route("/oferta/<slug>")
def oferta_individual(slug):
    df = cargar_datos()
    if df.empty: return "Error", 500
    
    oferta_encontrada = df[df['slug'] == slug]
    if oferta_encontrada.empty:
        return "Oferta caducada o no encontrada", 404
        
    datos_oferta = oferta_encontrada.iloc[0].to_dict()
    return render_template("oferta.html", oferta=datos_oferta)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

