import csv
import time
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

# --- CREDENCIALES (Cámbialas por las tuyas) ---
USER = "info@cuidamosgranada.com"
PASSWORD = "FCC_cuidamos_granada_2026"

def configurar_driver():
    chrome_options = Options()
    # Mantiene el navegador abierto después de que el script termine
    chrome_options.add_experimental_option("detach", True)
    # Abre en pantalla completa
    chrome_options.add_argument("--start-maximized")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def realizar_login(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "user"))
        )
        
        # Localizar campos de login
        # Nota: Dinahosting suele usar 'rcmloginuser' y 'rcmloginpwd' o '_user' y '_pass'
        input_user = driver.find_element(By.ID, "user")
        input_pass = driver.find_element(By.ID, "password")
        
        # Escribir credenciales
        input_user.send_keys(USER)
        input_pass.send_keys(PASSWORD)
        
        # Pulsar Enter para entrar
        input_pass.send_keys(Keys.ENTER)
        
        print("Login enviado...")
    except Exception as e:
        print(f"Error durante el login: {e}")

def extraer_datos_correo(driver):
    print("Esperando a que carguen los correos...")
    
    # 1. Definimos el XPath de los elementos de la lista (los <li>)
    # He ajustado el XPath para que apunte directamente a los 'li' dentro de esa lista
    xpath_correos = '//*[@id="mail-list"]//ul/li'
    
    try:
        # 2. Esperar hasta 10 segundos a que aparezca al menos un correo
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_correos))
        )
        
        # 3. Guardarlos todos en una lista
        lista_correos = driver.find_elements(By.XPATH, xpath_correos)
        
        print(f"Se han encontrado {len(lista_correos)} correos en la bandeja.")
        
        # Ejemplo: Imprimir el texto de cada correo para verificar
        for i, correo in enumerate(lista_correos):
            # Extraemos el texto para ver qué hay dentro (Asunto, remitente, etc.)
            print(f"Correo {i+1}: {correo.text.replace(chr(10), ' | ')}")
            
        return lista_correos

    except Exception as e:
        print(f"No se pudieron cargar los correos o la lista está vacía: {e}")
        return []

def main():
    driver = configurar_driver()
    driver.get(URL_CORREO)
    
    # Ejecutar el login automáticamente
    realizar_login(driver)

    lista_de_elementos = extraer_datos_correo(driver)

if __name__ == "__main__":
    main()