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
        print("Login enviado...")
    except Exception as e:
        print(f"Error durante el login: {e}")

def procesar_correos_y_guardar(driver):
    xpath_correos = '//*[@id="mail-list"]//ul/li'
    # XPath del contenido (ajustado para ser más robusto seleccionando el <pre>)
    xpath_contenido = '//*[@id="preview-mail-detail"]//pre'
    patron_hora = r"^\d{1,2}:\d{2}$"
    
    print("Esperando bandeja de entrada...")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, xpath_correos)))

    total_elementos = len(driver.find_elements(By.XPATH, xpath_correos))
    datos_finales = []

    for i in range(total_elementos):
        try:
            elementos_frescos = driver.find_elements(By.XPATH, xpath_correos)
            if i >= len(elementos_frescos): break
            
            correo = elementos_frescos[i]
            partes = [p.strip() for p in correo.text.split('\n') if p.strip()]
            
            if len(partes) >= 2 and partes[0].lower() == "mail" and re.match(patron_hora, partes[1]):
                print(f"--- Extrayendo correo {i+1} ---")
                
                # Click para abrir
                enlace = correo.find_element(By.TAG_NAME, "a")
                driver.execute_script("arguments[0].click();", enlace)
                
                # Esperar a que el texto aparezca en el panel derecho
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath_contenido)))
                time.sleep(1) # Un segundo extra para asegurar carga
                
                # Extraer el texto del <pre>
                texto_mensaje = driver.find_element(By.XPATH, xpath_contenido).text
                
                # Guardamos el texto bruto junto con la hora
                datos_finales.append({
                    "Hora": partes[1],
                    "Contenido": texto_mensaje.replace('\n', ' | ')
                })
                
                print(f"Datos capturados de: {partes[1]}")
                time.sleep(1) 

        except Exception as e:
            print(f"Error en correo {i}: {e}")

    # Guardar a CSV al finalizar
    if datos_finales:
        guardar_en_csv(datos_finales)

def guardar_en_csv(datos):
    columnas = datos[0].keys()
    try:
        with open(ARCHIVO_SALIDA, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columnas)
            writer.writeheader()
            writer.writerows(datos)
        print(f"\n¡ÉXITO! Se han guardado {len(datos)} registros en {ARCHIVO_SALIDA}")
    except Exception as e:
        print(f"Error al guardar el CSV: {e}")

def main():
    driver = configurar_driver()
    driver.get(URL_CORREO)
    realizar_login(driver)
    procesar_correos_y_guardar(driver)

if __name__ == "__main__":
    main()