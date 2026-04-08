import os
import csv
import time
import random
from ddgs import DDGS

class BotEmpleoCategorizado:
    def __init__(self):
        # 1. CAMBIO: Guardamos directamente en la misma carpeta que la web
        self.archivo_final = "ofertas_clasificadas_valles.csv"
        
        self.pueblos = [
            "Mollet del Valles", "Granollers", "Parets del Valles", 
            "Les Franqueses del Valles", "Montmelo", "La Llagosta"
        ]
        
        self.categorias_laborales = {
            "Hosteleria y Turismo": ["Camarero", "Fregaplatos", "Cocinero", "Ayudante de cocina"],
            "Comercio y Tiendas": ["Dependiente", "Cajero", "Reponedor", "Encargado de tienda"],
            "Logistica y Transporte": ["Mozo de almacen", "Carretillero", "Repartidor", "Chofer"],
            "Limpieza y Mantenimiento": ["Personal de limpieza", "Cristalero", "Mantenimiento"],
            "Construccion e Industria": ["Peon de obra", "Albañil", "Electricista", "Operario de fabrica"],
            "Sanidad y Cuidados": ["Enfermeria", "Auxiliar de geriatria", "Cuidador a domicilio"],
            "Administracion y Oficinas": ["Auxiliar administrativo", "Recepcionista", "Contable"],
            "Atencion al Cliente": ["Teleoperador", "Atencion al cliente", "Soporte tecnico"]
        }
        
        self.objetivo_por_puesto = 10
        self.urls_guardadas = set() 
        
        # 2. CAMBIO: Le damos "memoria" al bot antes de empezar
        self.cargar_memoria_antigua()
        
        self.contador = {pueblo: {} for pueblo in self.pueblos}
        for pueblo in self.pueblos:
            for sector, puestos in self.categorias_laborales.items():
                for puesto in puestos:
                    self.contador[pueblo][puesto] = 0
                    
        self.configurar_csv()

    # --- NUEVA FUNCIÓN: Leer el archivo para evitar duplicados de días anteriores ---
    def cargar_memoria_antigua(self):
        if os.path.exists(self.archivo_final):
            with open(self.archivo_final, 'r', encoding='utf-8-sig') as f:
                lector = csv.DictReader(f)
                for fila in lector:
                    if 'URL' in fila:
                        self.urls_guardadas.add(fila['URL'])
            print(f"🧠 MEMORIA CARGADA: El bot recuerda {len(self.urls_guardadas)} ofertas anteriores. No las repetirá.")
        else:
            print("🧠 MEMORIA: No hay archivo previo. Empezando desde cero.")
    # -----------------------------------------------------------------------------

    def configurar_csv(self):
        # Si el archivo no existe, crea las cabeceras. Si existe, no hace nada (no borra).
        if not os.path.exists(self.archivo_final):
            with open(self.archivo_final, 'w', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow(["Titulo Oferta", "Localidad", "Sector Padre", "Puesto Especifico", "URL", "Plataforma", "Fecha Captura"])

    def guardar_oferta(self, titulo, localidad, sector, puesto, url, plataforma):
        # El modo 'a' (append) añade la oferta al final del archivo sin borrar lo anterior
        with open(self.archivo_final, 'a', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerow([titulo, localidad, sector, puesto, url, plataforma, time.strftime("%Y-%m-%d")])

    def rastrear_portal(self, sector, puesto, pueblo, portal, dork_base):
        query = f'"{puesto}" "{pueblo}" {dork_base}'
        
        try:
            with DDGS() as ddgs:
                resultados = ddgs.text(query, timelimit='m', max_results=15)
                for r in resultados:
                    if self.contador[pueblo][puesto] >= self.objetivo_por_puesto:
                        break 
                        
                    url = r.get('href', '')
                    titulo_bruto = r.get('title', '')
                    
                    # 3. VERIFICACIÓN: Aquí comprueba si la URL ya está en su memoria
                    if url and url not in self.urls_guardadas and any(p in url.lower() or p in titulo_bruto.lower() for p in ['job', 'empleo', 'oferta', 'trabajo']):
                        self.guardar_oferta(titulo_bruto, pueblo, sector, puesto, url, portal)
                        self.urls_guardadas.add(url) # La guarda en memoria para no repetirla en este mismo escaneo
                        self.contador[pueblo][puesto] += 1
                        print(f"      [+] ({self.contador[pueblo][puesto]}/{self.objetivo_por_puesto}) {titulo_bruto[:40]}...")
                        
                time.sleep(random.uniform(1.5, 3.0)) 
        except Exception as e:
            pass 

    def ejecutar_rastreo(self):
        print("🚀 INICIANDO BARRIDO CLASIFICADO POR CATEGORÍAS 🚀\n")
        
        for pueblo in self.pueblos:
            print("="*60)
            print(f"📍 ESCANEANDO CIUDAD: {pueblo.upper()}")
            print("="*60)
            
            for sector, puestos in self.categorias_laborales.items():
                print(f"\n📂 ABRIENDO SECTOR: {sector}")
                
                for puesto in puestos:
                    print(f"  🔎 Buscando: {puesto}...")
                    
                    if self.contador[pueblo][puesto] < self.objetivo_por_puesto:
                        self.rastrear_portal(sector, puesto, pueblo, "InfoJobs", "site:infojobs.net")
                    if self.contador[pueblo][puesto] < self.objetivo_por_puesto:
                        self.rastrear_portal(sector, puesto, pueblo, "Indeed", "site:es.indeed.com/viewjob OR site:es.indeed.com/oferta")
                    if self.contador[pueblo][puesto] < self.objetivo_por_puesto:
                        self.rastrear_portal(sector, puesto, pueblo, "LinkedIn", "site:linkedin.com/jobs/view/")
                    
                    conseguidos = self.contador[pueblo][puesto]
                    if conseguidos == self.objetivo_por_puesto:
                        print(f"    ✅ {puesto}: {conseguidos}/{self.objetivo_por_puesto} completado.")
                    else:
                        print(f"    ⚠️ {puesto}: Mercado seco, solo {conseguidos} ofertas nuevas.")
            
            print(f"\n🏁 {pueblo.upper()} COMPLETADO. Descansando 10 segundos antes de la siguiente ciudad...")
            time.sleep(10)

        print("\n🔥 EXTRACCIÓN FINALIZADA. El archivo 'ofertas_clasificadas_valles.csv' ha sido actualizado sin duplicados.")

if __name__ == "__main__":
    bot = BotEmpleoCategorizado()
    bot.ejecutar_rastreo()

