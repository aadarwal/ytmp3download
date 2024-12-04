import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def wait_for_conversion(driver, timeout=60):
    try:
        WebDriverWait(driver, timeout).until(
            EC.text_to_be_present_in_element((By.ID, "progress"), "conversion completed")
        )
        print("Conversion completed.")
        return True
    except Exception as e:
        print(f"Conversion did not complete in time: {e}")
        return False


def wait_for_download_to_complete(download_dir, expected_file_name=None, timeout=60):
    start_time = time.time()
    while True:
        if expected_file_name:
            file_path = os.path.join(download_dir, expected_file_name)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                print(f"File {expected_file_name} downloaded successfully.")
                return True

        downloading_files = [f for f in os.listdir(download_dir) if f.endswith('.crdownload')]
        if not downloading_files:
            return True

        if time.time() - start_time > timeout:
            print(f"Download timed out after {timeout} seconds.")
            return False
        time.sleep(1)


def youtube_search_and_download(input_file, download_dir):
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless") 
    options.add_argument("--disable-gpu") 
    options.add_argument("--no-sandbox") 
    options.add_argument("--disable-dev-shm-usage")  
    options.add_argument("--window-size=1920,1080")  
    prefs = {"download.default_directory": download_dir}  
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    with open(input_file, 'r') as file:
        video_names = [line.strip() for line in file.readlines()]

    failed_downloads = []

    for index, video_name in enumerate(video_names):
        try:
            print(f"Searching for: {video_name}")
            driver.get("https://www.youtube.com")
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "search_query")))
            search_box.send_keys(video_name)
            search_box.send_keys(Keys.RETURN)

            video_links = wait.until(EC.presence_of_all_elements_located((By.ID, "video-title")))

            video_url = None
            for video in video_links:
                try:
                    aria_label = video.get_attribute("aria-label")
                    if not aria_label or "Ad" not in aria_label:  
                        video_url = video.get_attribute("href")
                        if video_url:
                            print(f"Non-ad video URL for '{video_name}': {video_url}")
                            break
                except Exception:
                    continue

            if not video_url:
                print(f"No valid non-ad video found for: {video_name}")
                failed_downloads.append(video_name)
                continue

            driver.get("https://ytmp3.cc")
            url_input = wait.until(EC.presence_of_element_located((By.ID, "video")))
            url_input.send_keys(video_url)
            convert_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
            convert_button.click()

            if not wait_for_conversion(driver):
                print(f"Conversion failed for: {video_name}")
                failed_downloads.append(video_name)
                continue

            try:
                download_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Download']")))
                download_button.click()
                print(f"Download initiated for: {video_name}")

                expected_file_name = f"{video_name}.mp3"  
                if not wait_for_download_to_complete(download_dir, expected_file_name=expected_file_name):
                    print(f"Download failed for: {video_name}")
                    failed_downloads.append(video_name)
            except Exception as e:
                print(f"Failed to click download button for {video_name}: {e}")
                failed_downloads.append(video_name)
                continue

        except Exception as e:
            print(f"An error occurred while processing '{video_name}': {e}")
            failed_downloads.append(video_name)
            continue

    print("Waiting for all downloads to complete...")
    time.sleep(10)

    driver.quit()

    if failed_downloads:
        print("The following videos failed to download:")
        for video in failed_downloads:
            print(f"- {video}")


input_file = "vids.txt"  #change to .txt file name you use. 
download_dir = "/Downloads" #path to downloads pls change. 
youtube_search_and_download(input_file, download_dir)