import csv
import time
import re
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
    """Limpia etiquetas, saltos de línea y espacios dobles"""
    etiquetas = [
        "E-mail:", "Dirección de recogida:", "NºCalle:", 
        "Número de enseres:", "Tipo de mueble/objeto:"
    ]
    # Quitamos saltos de línea y retornos de carro
    resultado = texto.replace('\n', ' ').replace('\r', ' ')
    for etiqueta in etiquetas:
        resultado = resultado.replace(etiqueta, "")
    
    # Quitar espacios múltiples que sobran
    resultado = " ".join(resultado.split())
    return resultado.strip()

def procesar_correos_y_guardar(driver):
    xpath_correos = '//*[@id="mail-list"]//ul/li'
    xpath_contenido = '//*[@id="preview-mail-detail"]//pre'
    patron_hoy = r"^\d{1,2}:\d{2}$"
    
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
            if "mail" not in partes_fila[0].lower() or not re.match(patron_hoy, partes_fila[1]):
                continue

            hora_o_fecha = partes_fila[1]
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
                
                # SEPARACIÓN CLAVE: Asegurarnos de separar por el carácter |
                bloques = texto_mensaje.split('|')
                
                # Construimos la fila: primero la hora, luego cada bloque limpio
                fila_datos = [hora_o_fecha]
                for bloque in bloques:
                    dato_limpio = limpiar_valor(bloque)
                    if dato_limpio: # Solo añadimos si no está vacío
                        fila_datos.append(dato_limpio)
                
                datos_finales.append(fila_datos)
                print(f"✅ Procesado: {hora_o_fecha}")

        except Exception as e:
            print(f"Error: {e}")

    if datos_finales:
        guardar_en_csv(datos_finales)

def guardar_en_csv(datos):
    try:
        with open(ARCHIVO_SALIDA, 'w', newline='', encoding='utf-8-sig') as f:
            # Forzamos delimitador punto y coma y eliminamos cualquier espacio accidental en el escritor
            writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(datos)
        print(f"\n¡Listo! CSV generado con punto y coma en: {ARCHIVO_SALIDA}")
    except Exception as e:
        print(f"Error CSV: {e}")

def main():
    driver = configurar_driver()
    driver.get(URL_CORREO)
    realizar_login(driver)
    time.sleep(5)
    procesar_correos_y_guardar(driver)
    driver.quit()

if __name__ == "__main__":
    main()