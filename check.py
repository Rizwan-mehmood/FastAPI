import logging
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename="card_check_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Path to ChromeDriver
# chrome_driver_path = (
#     "C:\\Users\\Rizwan Mehmood\\OneDrive\\Desktop\\Fiverr\\chromedriver.exe"
# )
driver = webdriver.Chrome()
# FastAPI application
app = FastAPI()


# Pydantic model for request body
class CardRequest(BaseModel):
    cards: List[dict]  # Each card as a dict with card_number, exp_date, cvv


# Global variable to hold the WebDriver
driver = None


# Function to load cookies from the JSON file and add them to the driver
def load_cookies(driver, cookie_file="cookies.json"):
    with open(cookie_file, "r") as file:
        cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)


# Function to check balance for a card
def check_card_balance(card_number, exp_date, cvv):
    balance_result = {}
    try:
        global driver
        if driver is None:
            # Configure Selenium WebDriver options
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")

            # Initialize the WebDriver
            service = Service(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Navigate to the website
            driver.get("https://shop.giftcards.com/us/en/self-serve/check-balance")
            load_cookies(driver)
            driver.refresh()

            # Wait for the original content to be loaded after setting cookies
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "cardNumber"))
            )
            time.sleep(5)
            driver.refresh()

        # Fill in card details
        card_number_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "cardNumber"))
        )
        for char in card_number:
            card_number_field.send_keys(char)
            time.sleep(0.05)

        exp_date_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "exp"))
        )
        for char in exp_date:
            exp_date_field.send_keys(char)
            time.sleep(0.05)

        cvv_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "cvv"))
        )
        for char in cvv:
            cvv_field.send_keys(char)
            time.sleep(0.05)

        # Click the 'Check Balance' button
        check_balance_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(@class, 'card-management_widget__button') and text()='Check Balance']",
                )
            )
        )
        check_balance_button.click()

        # Wait for balance result to appear
        balance_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "card-management-widget__balance"))
        )
        balance_text = balance_element.text.split("\n")[-1]

        # Log balance information
        balance_result = {
            "card_number": card_number,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "balance": balance_text,
        }
        log_balance(card_number, balance_text)

        # Click the 'Check balance for another card' button
        reset_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.ID, "card-management-widget__check-balance-button")
            )
        )
        reset_button.click()

    except Exception as e:
        logging.error(f"Error while checking card {card_number}: {str(e)}")
        balance_result = {
            "card_number": card_number,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "balance": "Error occurred",
        }

    return balance_result


# Function to log card details and balance to a text file
def log_balance(card_number, balance):
    with open("card_balances.txt", "a") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{timestamp} - Card: {card_number}, Balance: {balance}\n")


# FastAPI endpoint to check balances
@app.post("/check-balances/")
async def check_balances(card_request: CardRequest, background_tasks: BackgroundTasks):
    results = []
    for card in card_request.cards:
        card_number = card.get("card_number")
        exp_date = card.get("exp_date")
        cvv = card.get("cvv")
        result = check_card_balance(card_number, exp_date, cvv)
        results.append(result)

    return results


# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
