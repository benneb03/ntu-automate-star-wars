from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from time import sleep
import sys

# --- account info ---
options = Options()
# options.add_argument("--window-size=1680x1050") 
options.add_experimental_option("excludeSwitches", ["enable-automation", 'enable-logging'])

key={}
TIMEOUT = 30 

# --- Helper Functions ---

def init():
    """Reads accountinfo (DRIVE, USERNAME, PASSWORD) from accountinfo.txt."""
    try:
        # NOTE: Using the path you provided earlier.
        with open('/Users/ben/142822176/starwarsss/accountinfo.txt') as f:
            for line in f:
                if line.strip() and "=" in line:
                    (k, val) = line.split("=", 1)
                    key[k.strip()] = val.strip()
        
        if not key.get('DRIVE') or not key.get('USERNAME') or not key.get('PASSWORD'):
             raise ValueError("accountinfo.txt is missing DRIVE, USERNAME, or PASSWORD keys.")

    except FileNotFoundError:
        print("ERROR: accountinfo.txt not found. Ensure it exists in the correct path.")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

def clicker():
    """Main function to execute the module registration automation."""
    driver = None
    try:
        # 1. Initialize Driver (FIXED: Ensured Service and Options are passed)
        print("Initializing Chrome driver...")
        # Create a Service object using the driver path from your accountinfo
        service = Service(key.get('DRIVE'))
        # Pass the Service object and Options to the Chrome constructor
        driver = webdriver.Chrome()# <-- CORRECTED
        
        driver.get('https://wish.wis.ntu.edu.sg/pls/webexe/ldap_login.login?w_url=https://wish.wis.ntu.edu.sg/pls/webexe/aus_stars_planner.main')
        
        # 2. Login
        print("Logging in...")
        
        input_uid = driver.find_element(By.ID, 'UID')
        input_uid.send_keys(key.get('USERNAME'))
        driver.find_element(By.XPATH, "//input[@type='submit']").click()
        sleep(1)  # Wait for password field to load
        
        input_pw = driver.find_element(By.ID, 'PW')
        input_pw.send_keys(key.get('PASSWORD'))
        driver.find_element(By.XPATH, "//input[@type='submit']").click()

        # 3. Registration Loop
        done = False
        while not done:
            print("Waiting for registration button...")
            element_present = EC.presence_of_element_located((By.XPATH, "//input[@type='submit' and @value='Add (Register) Selected Course(s)']"))
            WebDriverWait(driver, TIMEOUT).until(element_present)

            registration_open = False
            while not registration_open:
                print("Clicking 'Add (Register) Selected Course(s)'...")
                # Click the Add button
                driver.find_element(By.XPATH, "//input[@type='submit' and @value='Add (Register) Selected Course(s)']").click()
                
                try: 
                    # 1. EXPLICITLY WAIT for the alert to appear (up to 5 seconds)
                    WebDriverWait(driver, 1).until(EC.alert_is_present())
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    
                    # 2. Check Alert Content 
                    if 'not allowed to register' in alert_text:
                        registration_open = False
                        # The server datetime shows Dec 02 2025, confirming the bid hasn't started yet.
                        print(f"Registration not open yet. Message: '{alert_text[:40]}...' Retrying...") 
                    else: 
                        registration_open = True
                        print(f"Alert received, proceeding. Message: '{alert_text[:40]}...'")

                    # 3. Dismiss the alert so the script can proceed
                    alert.accept()
                
                except TimeoutException:
                    # If the alert wait times out, it means no alert appeared, 
                    # so the page successfully advanced to the confirmation page.
                    registration_open = True 
                    print("No alert detected within 5 seconds, proceeding to confirmation page.")

                except NoAlertPresentException:
                    # Fallback for immediate page navigation
                    registration_open = True 
                    print("No alert detected, proceeding to confirmation page.")

                if not registration_open:
                    sleep(0.5) # Wait half a second before trying to click the button again

            # 4. Confirm Registration
            print("Confirming course registration...")
            confirm_button_present = EC.presence_of_element_located((By.XPATH, "//input[@type='submit' and @value='Confirm to add course(s)']"))
            WebDriverWait(driver, TIMEOUT).until(confirm_button_present)
            
            driver.find_element(By.XPATH, "//input[@type='submit' and @value='Confirm to add course(s)']").click()

            # Handle second-level alerts (e.g., session expired, warnings)
            try: 
                alert = driver.switch_to.alert
                alert_text = alert.text
                print(f"Alert after confirmation: {alert_text}")
                
                if 'expired' in alert_text:
                    print("Session expired, restarting automation...")
                    alert.accept()
                    driver.quit()
                    clicker()
                    return 

                alert.accept()
            except NoAlertPresentException:
                pass
            
            # 5. Check Results and Loop Control
            
            result_table_present = EC.presence_of_element_located((By.TAG_NAME, 'table'))
            WebDriverWait(driver, TIMEOUT).until(result_table_present)

            root = driver.find_element(By.TAG_NAME, 'table').text
            print("\n--- REGISTRATION ATTEMPT RESULT ---\n")
            print(root)
            print("\n-----------------------------------\n")

            if 'no more vacancy' in root:
                done = False
                driver.find_element(By.XPATH, "//input[@type='submit']").click()
                print("Vacancy issue detected. Number of courses still pending: " + str(root.count('no more vacancy')))
                print("Starting next attempt cycle in 1 second...")
                sleep(1) 
            else:
                done = True
                print("--------------------- ALL COURSES PROCESSED --------------------")
                
    except TimeoutException:
        print("ERROR: Automation timed out while waiting for a page element.")
        print("--------------------- FAILED --------------------")
    except Exception as e:
        print("CRITICAL ERROR:  " + str(e))
        print("--------------------- FAILED --------------------")
    finally:
        if driver:
            driver.quit()
        
if __name__ == "__main__":
    init()
    if len(sys.argv) >= 2 and sys.argv[1] == "-bg": 
        options.add_argument("--headless")
        print("Running in headless (background) mode.")
    else:
        print("Running in visible mode.")
        
    clicker()