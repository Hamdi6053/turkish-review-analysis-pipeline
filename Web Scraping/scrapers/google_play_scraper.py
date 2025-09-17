import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime

class GooglePlayParallelScraper:
    def __init__(self, app_url, max_workers=3, output_file='yorumlar'):
        self.app_url = app_url
        self.max_workers = max_workers
        self.output_file = output_file
        self.data = []
        self.lock = threading.Lock()
        self.df = pd.DataFrame(columns=['tarih', 'yorum'])
        self.processed_reviews = set()
        self.unique_reviews = set()
        self.worker_activity = {i: 0 for i in range(max_workers)}  # Worker aktivite takibi

    def setup_driver(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        return driver

    def worker_task(self, worker_id):
        """Her bir paralel çalışanın yapacağı iş"""
        driver = self.setup_driver()
        wait = WebDriverWait(driver, 20)
        
        try:
            self.print_worker_status(worker_id, "Uygulama sayfası açılıyor...")
            driver.get(self.app_url)
            time.sleep(5)

            self.print_worker_status(worker_id, "Sayfa kaydırılıyor...")
            for i in range(5):
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)

            if not self.find_and_click_show_all_reviews(driver, wait, worker_id):
                self.print_worker_status(worker_id, "Tüm yorumları göster butonuna tıklanamadı.", "error")
                return

            popup_container = self.find_popup_container(driver, wait, worker_id)
            if not popup_container:
                self.print_worker_status(worker_id, "Popup container bulunamadı.", "error")
                return

            self.scroll_and_extract(driver, popup_container, worker_id)

        except Exception as e:
            self.print_worker_status(worker_id, f"Hata oluştu: {e}", "error")
            driver.save_screenshot(f"error_worker_{worker_id}.png")
        finally:
            driver.quit()
            self.print_worker_status(worker_id, "Çalışmayı tamamladı", "success")

    def print_worker_status(self, worker_id, message, msg_type="info"):
        """Daha düzenli terminal çıktısı için"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "error": "\033[91m",
            "success": "\033[92m",
            "warning": "\033[93m",
            "info": "\033[94m",
            "review": "\033[0m" 
        }
        
        color_code = colors.get(msg_type, "\033[0m")
        reset_code = "\033[0m"
        

        if msg_type == "review":
            self.worker_activity[worker_id] = time.time()
        
        print(f"{color_code}[{timestamp} Worker {worker_id}] {message}{reset_code}")

    def find_and_click_show_all_reviews(self, driver, wait, worker_id):
        self.print_worker_status(worker_id, "'Tüm yorumları göster' butonu aranıyor...")
        
        selectors = [
            "//button[contains(., 'Tüm yorumları göster')]",
            "//span[contains(text(), 'Tüm yorumları göster')]/ancestor::button",
            "//div[contains(@class, 'VfPpkd-Jh9lGc')]//button",
        ]
        
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(2)
        
        for selector in selectors:
            try:
                button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(1)
                
                try:
                    driver.execute_script("arguments[0].click();", button)
                    self.print_worker_status(worker_id, f"Butona tıklandı: {selector}", "success")
                    time.sleep(3)
                    return True
                except Exception:
                    try:
                        button.click()
                        self.print_worker_status(worker_id, f"Butona tıklandı: {selector}", "success")
                        time.sleep(3)
                        return True
                    except Exception:
                        continue
            except Exception:
                continue
                
        self.print_worker_status(worker_id, "Buton bulunamadı", "warning")
        return False

    def find_popup_container(self, driver, wait, worker_id):
        self.print_worker_status(worker_id, "Popup aranıyor...")
        
        popup_selectors = [
            "//div[@role='dialog']", 
            "//div[@jscontroller='S9fy']",
            "//div[contains(@class, 'fysCi')]",
        ]
        
        for selector in popup_selectors:
            try:
                popup = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                self.print_worker_status(worker_id, "Popup bulundu", "success")
                return popup
            except:
                continue
                
        self.print_worker_status(worker_id, "Popup bulunamadı", "error")
        return None

    def extract_reviews(self, popup_container, worker_id):
        """Thread-safe yorum çekme işlemi"""
        review_cards = popup_container.find_elements(By.XPATH, ".//div[contains(@class, 'RHo1pe')]")
        new_reviews = []
        
        for card in review_cards:
            try:
               
                date = None
                for selector in [".//div[contains(@class, 'bp9Aid')]", ".//span[contains(@class, 'bp9Aid')]"]:
                    try:
                        date = card.find_element(By.XPATH, selector).text.strip()
                        if date: break
                    except: continue
                
                review_text = None
                for selector in [".//div[contains(@class, 'h3YV2d')]", ".//span[contains(@class, 'h3YV2d')]"]:
                    try:
                        review_text = card.find_element(By.XPATH, selector).text.strip()
                        if review_text: break
                    except: continue
                
                if not review_text or not date:
                    continue
                
               
                review_hash = hash((date, review_text[:50]))
                
                with self.lock:
                    if review_hash in self.unique_reviews:
                        continue
                    self.unique_reviews.add(review_hash)
                
                new_review = {'tarih': date, 'yorum': review_text, 'worker_id': worker_id}
                new_reviews.append(new_review)
                
              
                display_review = review_text[:70] + "..." if len(review_text) > 70 else review_text
                self.print_worker_status(worker_id, f"{date} | {display_review}", "review")
                
            except Exception as e:
                self.print_worker_status(worker_id, f"Yorum çekme hatası: {e}", "error")
                continue
        
        return new_reviews

    def scroll_and_extract(self, driver, popup_container, worker_id):
        self.print_worker_status(worker_id, "Yorumlar çekiliyor...")
        
        scroll_element = None
        for selector in [".//div[contains(@class, 'fysCi')]", ".//div[@jsaction='rcuQ6b:npT2md']"]:
            try:
                scroll_element = popup_container.find_element(By.XPATH, selector)
                break
            except:
                continue
        
        if not scroll_element:
            scroll_element = popup_container
            
        last_review_count = 0
        stagnant_count = 0
        max_stagnant = 5
        
        while True:
          
            new_reviews = self.extract_reviews(popup_container, worker_id)
            
           
            if new_reviews:
                with self.lock:
                    self.data.extend(new_reviews)
                    new_df = pd.DataFrame(new_reviews)
                    self.df = pd.concat([self.df, new_df], ignore_index=True)
                    new_df.to_csv(f"{self.output_file}.csv", 
                                mode='a', 
                                header=not bool(self.unique_reviews),
                                index=False, 
                                encoding='utf-8-sig')
                    self.print_worker_status(worker_id, f"{len(new_reviews)} yeni yorum eklendi", "success")
            
           
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scroll_element)
            time.sleep(1)
            
            current_reviews = popup_container.find_elements(By.XPATH, ".//div[contains(@class, 'RHo1pe')]")
            self.print_worker_status(worker_id, f"Toplam {len(current_reviews)} yorum yüklendi", "info")
            
            if len(current_reviews) == last_review_count:
                stagnant_count += 1
                if stagnant_count >= max_stagnant:
                    self.print_worker_status(worker_id, f"{max_stagnant} denemedir yeni yorum yüklenmedi, işlem sonlandırılıyor", "warning")
                    break
            else:
                stagnant_count = 0
                
            last_review_count = len(current_reviews)

    def scrape(self):
        start_time = time.time()
        self.print_worker_status("MAIN", "Scraping işlemi başlatılıyor...", "success")
        
        
        def activity_monitor():
            while any(time.time() - last_active < 10 for last_active in self.worker_activity.values()):
                active_workers = sum(1 for last_active in self.worker_activity.values() if time.time() - last_active < 5)
                self.print_worker_status("MONITOR", f"Aktif worker sayısı: {active_workers}/{self.max_workers}", "info")
                time.sleep(5)
        
        monitor_thread = threading.Thread(target=activity_monitor, daemon=True)
        monitor_thread.start()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.worker_task, i) for i in range(self.max_workers)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.print_worker_status("MAIN", f"Thread hatası: {e}", "error")
        
        
        self.save_final()
        
        total_time = time.time() - start_time
        self.print_worker_status("MAIN", f"Toplam süre: {total_time:.2f} saniye", "success")
        self.print_worker_status("MAIN", f"Toplam {len(self.data)} benzersiz yorum alındı", "success")

    def save_final(self):
        """Son kayıt işlemleri"""
        if not self.data:
            self.print_worker_status("MAIN", "Kaydedilecek veri bulunamadı", "warning")
            return
            
        
        
      
        self.df.drop_duplicates(subset=['tarih', 'yorum'], keep='first', inplace=True)
        self.df.to_csv(f"{self.output_file}_final.csv", index=False, encoding='utf-8-sig')
        self.print_worker_status("MAIN", "Veriler başarıyla kaydedildi", "success")


if __name__ == '__main__':
    scraper = GooglePlayParallelScraper(
        app_url='https://play.google.com/store/apps/details?id=com.a101kapida.android&hl=tr',
        max_workers=3,
        output_file='yorumlar'
    )
    scraper.scrape()