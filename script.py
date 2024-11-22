from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import json


def save_to_file(data, filename="data.json"):
    """Save astrologer data to a file."""
    try:
        with open(filename, "a") as file:
            for entry in data:
                file.write(json.dumps(entry) + "\n")
        print(f"Saved {len(data)} astrologers to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")


def scrape_batch(driver, already_scraped, is_first_batch):
    """Scrape a batch of data."""
    astrologer_data = []
    retries = 0
    max_retries = 3

    while retries < max_retries:
        try:
            astrologer_cards = driver.find_elements(By.CLASS_NAME, "astrologer_box")
            break
        except WebDriverException as e:
            retries += 1
            print(f"Retrying fetching astrologer cards due to error: {e}")
            time.sleep(5)

    if retries == max_retries:
        print("Max retries reached while fetching astrologer cards. Exiting batch.")
        return 0

    print(f"Total astrologer cards found: {len(astrologer_cards)}")

    for idx, card in enumerate(astrologer_cards[already_scraped:], start=1):
        try:
            astrologer = {}

            # Use different XPath for the first batch and subsequent batches
            if is_first_batch:
                try:
                    astrologer['name'] = card.find_element(By.XPATH, ".//button[contains(@class, 'home_astro_tile_font')]").text
                except NoSuchElementException:
                    astrologer['name'] = "N/A"
            else:
                try:
                    astrologer['name'] = card.find_element(By.XPATH, ".//a[contains(@class, 'as_profile_font wrapText')]").text
                except NoSuchElementException:
                    astrologer['name'] = "N/A"

            # Extract other details
            try:
                astrologer['languages'] = card.find_element(By.XPATH, ".//div[contains(@class, 'font14') and contains(@class, 'marginBottm5')]").text
            except NoSuchElementException:
                astrologer['languages'] = "N/A"

            try:
                astrologer['specialties'] = card.find_element(By.XPATH, ".//div[contains(@class, 'font14') and contains(@class, 'wrapText')]").text
            except NoSuchElementException:
                astrologer['specialties'] = "N/A"

            try:
                astrologer['experience'] = card.find_element(By.XPATH, ".//li[contains(., 'years')]").text
            except NoSuchElementException:
                astrologer['experience'] = "N/A"

            try:
                astrologer['price'] = card.find_element(By.XPATH, ".//span[contains(@class, 'discount_price')]").text
            except NoSuchElementException:
                astrologer['price'] = "N/A"

            try:
                astrologer['rating'] = card.find_element(By.CLASS_NAME, "star_rating_a").text.split()[0]
            except NoSuchElementException:
                astrologer['rating'] = "N/A"

            astrologer_data.append(astrologer)
            print(f"Scraped astrologer: {astrologer['name']}")

        except Exception as e:
            print(f"Error scraping astrologer: {e}")
            continue

    save_to_file(astrologer_data)
    return len(astrologer_data)


def scrape_astrologers():
    """Main scraping function."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.page_load_strategy = 'eager'

    # Extend driver timeout settings
    options.add_argument('--timeout=180')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        url = "" #put the url
        driver.get(url)
        time.sleep(5)

        total_scraped = 0
        retries = 0
        max_retries = 5
        max_no_new_data_attempts = 3  # Limit for no new data attempts
        no_new_data_attempts = 0

        is_first_batch = True  # Flag for the first batch

        while retries < max_retries:
            try:
                print(f"Current astrologers loaded: {total_scraped}")
                new_scraped = scrape_batch(driver, total_scraped, is_first_batch)

                # After the first batch, set the flag to False
                if is_first_batch:
                    is_first_batch = False

                # If no new data is scraped, increment no_new_data_attempts
                if new_scraped == 0:
                    no_new_data_attempts += 1
                    if no_new_data_attempts >= max_no_new_data_attempts:
                        print("No new data for multiple attempts. Exiting...")
                        break
                else:
                    no_new_data_attempts = 0  # Reset if new data is found

                total_scraped += new_scraped

                # Attempt to load more data
                try:
                    view_more_button = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'View More')]"))
                    )
                    driver.execute_script("arguments[0].click();", view_more_button)
                    time.sleep(5)  # Allow time for loading
                except TimeoutException:
                    print("No more View More button found. Scraping might be completed.")
                    break

                retries = 0  # Reset retries on success

            except TimeoutException:
                print("Timeout occurred, retrying...")
                retries += 1
                time.sleep(10)  # Pause before retrying

        print(f"Scraping completed. Total astrologers scraped: {total_scraped}")

    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_astrologers()
