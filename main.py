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

def procesar_correos(driver):
    xpath_correos = '//*[@id="mail-list"]//ul/li'
    patron_hora = r"^\d{1,2}:\d{2}$"
    
    print("Esperando bandeja de entrada...")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, xpath_correos)))

    # Detectamos cuántos hay
    total_elementos = len(driver.find_elements(By.XPATH, xpath_correos))
    print(f"Detectados {total_elementos} elementos. Iniciando escaneo...")

    for i in range(total_elementos):
        try:
            # Volvemos a buscar la lista para que los elementos estén "vivos"
            elementos_frescos = driver.find_elements(By.XPATH, xpath_correos)
            
            # Si por algún motivo la lista cambió y el índice ya no existe, saltamos
            if i >= len(elementos_frescos): break
            
            correo = elementos_frescos[i]
            partes = [p.strip() for p in correo.text.split('\n') if p.strip()]
            
            if len(partes) >= 2:
                remitente = partes[0].lower()
                tiempo = partes[1]
                
                if remitente == "mail" and re.match(patron_hora, tiempo):
                    # Para saber qué correo estamos tocando:
                    asunto = partes[2] if len(partes) > 2 else "Sin asunto"
                    print(f"--- TRABAJANDO EN: {asunto} ({tiempo}) ---")
                    
                    # Scroll y Click
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", correo)
                    time.sleep(0.5)
                    
                    enlace = correo.find_element(By.TAG_NAME, "a")
                    driver.execute_script("arguments[0].click();", enlace)
                    
                    # ESPERA CRUCIAL: Dale 5 segundos para que veas cómo cambia la pantalla
                    print(f"Esperando a que el panel derecho cargue el correo {i+1}...")
                    time.sleep(5) 
                    
                    # --- AQUÍ ES DONDE INSPECCIONAREMOS EL CUERPO ---
                    
                else:
                    pass

        except Exception as e:
            print(f"Error en posición {i}: {e}")
            time.sleep(1)

def main():
    driver = configurar_driver()
    driver.get(URL_CORREO)
    
    realizar_login(driver)
    
    # Ejecutamos la nueva función robusta
    procesar_correos(driver)

if __name__ == "__main__":
    main()