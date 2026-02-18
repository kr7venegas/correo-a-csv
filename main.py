import csv
import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURACIÓN ---
URL_CORREO = "https://dinahosting.email/login"
ARCHIVO_SALIDA = "datos_extraidos.csv"
USER = "info@cuidamosgranada.com"
PASSWORD = "FCC_cuidamos_granada_2026"

# VARIABLE DE DÍAS: 0 = Hoy, 1 = Ayer...
DIAS_ATRAS = 1 

def configurar_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def realizar_login(driver):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user")))
        driver.find_element(By.ID, "user").send_keys(USER)
        driver.find_element(By.ID, "password").send_keys(PASSWORD + Keys.ENTER)
    except Exception as e:
        print(f"Error login: {e}")

def limpiar_valor(texto):
    """Elimina etiquetas y cualquier rastro de la barra vertical |"""
    etiquetas = ["E-mail:", "Dirección de recogida:", "NºCalle:", "Número de enseres:", "Tipo de mueble/objeto:"]
    # Quitamos saltos de línea y la propia barra por si acaso queda alguna
    resultado = texto.replace('\n', ';').replace('\r', ';').replace('|', ';')
    for etiqueta in etiquetas:
        resultado = resultado.replace(etiqueta, "")
    # Quitar espacios múltiples
    resultado = " ".join(resultado.split())
    return resultado.strip()

def obtener_patron_fecha():
    objetivo = datetime.now() - timedelta(days=DIAS_ATRAS)
    if DIAS_ATRAS == 0:
        return r"^\d{1,2}:\d{2}$", True
    else:
        meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        fecha_str = f"{objetivo.day} {meses[objetivo.month - 1]}"
        return fecha_str, False

def procesar_correos_y_guardar(driver):
    xpath_correos = '//*[@id="mail-list"]//ul/li'
    xpath_contenido = '//*[@id="preview-mail-detail"]//pre'
    patron_o_texto, es_regex = obtener_patron_fecha()
    
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, xpath_correos)))
    elementos_lista = driver.find_elements(By.XPATH, xpath_correos)
    
    datos_finales = []
    ultimo_texto_leido = ""

    for i in range(len(elementos_lista)):
        try:
            frescos = driver.find_elements(By.XPATH, xpath_correos)
            if i >= len(frescos): break
            
            correo_actual = frescos[i]
            partes_fila = [p.strip() for p in correo_actual.text.split('\n') if p.strip()]
            
            if len(partes_fila) < 2: continue
            
            asunto = partes_fila[0].lower()
            fecha_lista = partes_fila[1].lower()

            cumple_fecha = False
            if es_regex:
                if re.match(patron_o_texto, fecha_lista): cumple_fecha = True
            else:
                if patron_o_texto in fecha_lista: cumple_fecha = True

            if "mail" not in asunto or not cumple_fecha:
                continue

            enlace = correo_actual.find_element(By.TAG_NAME, "a")
            driver.execute_script("arguments[0].click();", enlace)
            
            texto_mensaje = ""
            for _ in range(10):
                try:
                    elemento_pre = driver.find_element(By.XPATH, xpath_contenido)
                    texto_mensaje = elemento_pre.text.strip()
                    if texto_mensaje and texto_mensaje != ultimo_texto_leido:
                        break
                except:
                    pass
                time.sleep(1.2)

            if texto_mensaje and texto_mensaje != ultimo_texto_leido:
                ultimo_texto_leido = texto_mensaje
                
                # --- AQUÍ ESTÁ EL CAMBIO CLAVE ---
                # Dividimos el mensaje por la barra | para crear elementos de lista independientes
                bloques_brutos = texto_mensaje.split('|')
                
                # Creamos la fila empezando por la hora
                fila_nueva = [fecha_lista]
                
                for bloque in bloques_brutos:
                    valor_limpio = limpiar_valor(bloque)
                    if valor_limpio:
                        fila_nueva.append(valor_limpio)
                
                # Ahora 'fila_nueva' es algo como: ["12:30", "email@...", "Calle...", "4", "..."]
                datos_finales.append(fila_nueva)

        except Exception as e:
            print(f"Error: {e}")

    if datos_finales:
        guardar_en_csv(datos_finales)

def guardar_en_csv(datos):
    # Esto entra en cada fila, mantiene la fecha (índice 0) 
    # y rompe el segundo elemento (índice 1) usando el punto y coma
    datos_corregidos = []
    for fila in datos:
        fecha = fila[0]
        # Dividimos el bloque de texto por el punto y coma para separar los campos
        campos_separados = fila[1].split(';')
        # Limpiamos espacios de cada trozo y lo juntamos todo en una nueva lista
        fila_limpia = [fecha] + [c.strip() for c in campos_separados]
        datos_corregidos.append(fila_limpia)

    datos = datos_corregidos
    print(datos)
    try:
        with open(ARCHIVO_SALIDA, 'w', newline='', encoding='utf-8-sig') as f:
            # El delimitador ';' se encargará de sustituir las antiguas barras '|'
            writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(datos)
        print(f"\n¡ÉXITO! Archivo generado con punto y coma: {ARCHIVO_SALIDA}")
    except Exception as e:
        print(f"Error CSV: {e}")

def main():
    driver = configurar_driver()
    driver.get(URL_CORREO)
    realizar_login(driver)
    procesar_correos_y_guardar(driver)
    driver.quit()

if __name__ == "__main__":
    main()