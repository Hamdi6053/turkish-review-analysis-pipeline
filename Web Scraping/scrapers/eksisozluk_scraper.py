import time
import os
import csv
import warnings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException

warnings.filterwarnings('ignore')
os.environ['WDM_LOG_LEVEL'] = '0'

class EksiSozlukScraper:
    def __init__(self, topic_url, max_pages=1):
        self.topic_url = topic_url
        self.base_url = topic_url.split('?')[0] 
        self.max_pages = max_pages
        self.entries = []  
        self.total_entries = 0
        self.options = self._setup_chrome_options()
        self.driver = None
        self.csv_file = None
        self.csv_writer = None
        topic_name = self.base_url.split('/')[-1].split('--')[0]
        self.csv_filename = f"{topic_name}_entries.csv"
        self.max_content_length = 300  

    def _setup_chrome_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-extensions") 
        options.add_argument("--disable-gpu")  
        options.add_argument("--disable-dev-shm-usage")  
        options.add_argument("--no-sandbox") 
        options.add_argument("--disable-infobars")  
        options.add_argument("--disable-notifications")  
        options.add_argument("--disable-popup-blocking") 
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        return options

    def start_driver(self):
        self.service = Service(executable_path="chromedriver.exe")
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.set_page_load_timeout(180)  # Sayfa yükleme zaman aşımını 3 dakika yap
        self.wait = WebDriverWait(self.driver, 60)  # Bekleme süresini 60 saniye yap
        self.actions = ActionChains(self.driver)
        
        # CSV dosyasını başlat (append modunda)
        file_exists = os.path.isfile(self.csv_filename)
        self.csv_file = open(self.csv_filename, "a", encoding="utf-8", newline="")
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=["content", "date"])
        if not file_exists:
            self.csv_writer.writeheader()

    def _scroll_down(self, pixels=1000, delay=1):
        self.driver.execute_script(f"window.scrollBy(0, {pixels});")
        time.sleep(delay)

    def _close_popup_ads(self):
        """Ekranda çıkan pop-up reklamları kapatır"""
        try:
            # Genel kapat butonları için seçiciler
            close_button_selectors = [
                "a.close", "span.close", "button.close", "div.close", 
                "a.kapat", "span.kapat", "button.kapat", "div.kapat",
                "[class*='close']", "[id*='close']", "[class*='kapat']", "[id*='kapat']",
                "button[aria-label='Close']", "button[aria-label='Kapat']"
            ]
            
            for selector in close_button_selectors:
                try:
                    close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in close_buttons:
                        if button.is_displayed():
                            button.click()
                            time.sleep(0.5)
                            print("Reklam kapatıldı.")
                except Exception:
                    continue
                    
            # Ekşi sözlük'e özel popup reklamları
            try:
                # Genel overlay kontrolü
                overlays = self.driver.find_elements(By.CSS_SELECTOR, "div[id*='overlay'], div[class*='overlay'], div[id*='modal'], div[class*='modal']")
                for overlay in overlays:
                    if overlay.is_displayed():
                        # İçindeki kapat butonunu bul
                        close_buttons = overlay.find_elements(By.CSS_SELECTOR, "button, a, span, div")
                        for button in close_buttons:
                            if "kapat" in button.text.lower() or "close" in button.text.lower() or "×" in button.text:
                                button.click()
                                time.sleep(0.5)
                                print("Overlay/modal reklam kapatıldı.")
            except Exception:
                pass
                
            # Escape tuşuna basarak bazı reklamları kapatmayı dene
            try:
                self.actions.send_keys(webdriver.Keys.ESCAPE).perform()
            except Exception:
                pass
                
        except Exception as e:
            print(f"Reklam kapatma işlemi sırasında hata: {str(e)}")

    def _expand_entry_if_needed(self, entry_element):
        """Eğer bir entry 'devamını okuyayım' içeriyorsa genişletir"""
        try:
            read_more = entry_element.find_element(By.CSS_SELECTOR, "span.read-more-link-wrapper")
            if read_more:
                read_more.click()
                time.sleep(1)
                return True
        except NoSuchElementException:
            pass  # Devamını oku butonu yoksa sorun değil
        return False

    def _get_entry_data(self, entry_element):
        try:
            # Entry içeriğini almak
            content_element = entry_element.find_element(By.CSS_SELECTOR, "div.content")
            
            # Eğer "devamını okuyayım" varsa genişlet
            self._expand_entry_if_needed(content_element)
            
            # Entry metnini al
            content_text = content_element.text.strip()
            
            # Tarih bilgisini almak
            try:
                # Önce footer içindeki tarih permalink'ini bulmayı deneyelim
                date_element = entry_element.find_element(By.CSS_SELECTOR, "a.entry-date")
                date_text = date_element.text.strip()
            except NoSuchElementException:
                # Bulunamazsa diğer yöntemi deneyelim
                try:
                    footer = entry_element.find_element(By.CSS_SELECTOR, "footer")
                    date_text = footer.text.strip()
                except:
                    date_text = "Tarih bulunamadı"
            
            # CSV için içerik uzunluğunu sınırlayalım (satır içi formatı korumak için)
            csv_content = content_text
            if len(csv_content) > self.max_content_length:
                csv_content = csv_content[:self.max_content_length] + "..."
            
            # Satır sonlarını kaldıralım
            csv_content = csv_content.replace("\n", " ").replace("\r", "")
            
            return {
                "content": csv_content,
                "date": date_text,
                "full_content": content_text  # Tam içerik terminalda göstermek için
            }
            
        except Exception as e:
            print(f"Entry veri çekerken hata: {str(e)}")
            return None

    def _save_entry_to_csv(self, entry_data):
        """Tek bir entry'yi CSV'ye kaydeder"""
        if self.csv_writer and entry_data:
            # Sadece CSV için gerekli alanları ayıklayarak yazdır
            csv_entry = {k: v for k, v in entry_data.items() if k != 'full_content'}
            self.csv_writer.writerow(csv_entry)
            self.csv_file.flush()  # Hemen diske yazılmasını sağla
            print(f"Entry CSV'ye kaydedildi: {csv_entry['content'][:50]}...")

    def scrape_page(self, page_num, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                url = f"{self.base_url}?p={page_num}"
                print(f"\nSayfa {page_num} yükleniyor (Deneme: {retries+1}): {url}")
                self.driver.get(url)
                time.sleep(5)  # Sayfa yüklenme süresini arttırdık

                # Reklamları kapat
                self._close_popup_ads()
                
                # Sayfayı aşağı kaydır
                for _ in range(3):  # Sayfanın tamamını görmek için birkaç kez kaydır
                    self._scroll_down(1000, 1)
                    self._close_popup_ads()  # Her kaydırma sonrası reklamları kontrol et
                
                # Entry elementlerini bul
                entry_elements = self.driver.find_elements(By.CSS_SELECTOR, "li[id^='entry-item']")
                
                print(f"{len(entry_elements)} entry bulundu.")
                
                if not entry_elements:
                    print("Hiç entry bulunamadı. Sayfa yapısı değişmiş olabilir.")
                    return False
                
                for i, entry_element in enumerate(entry_elements):
                    try:
                        entry_data = self._get_entry_data(entry_element)
                        
                        if entry_data:
                            # Entry'yi CSV'ye anında kaydet
                            self._save_entry_to_csv(entry_data)
                            self.total_entries += 1
                            
                            # Terminalde düzenli bir şekilde tam içeriği göster
                            print("\n" + "=" * 80)
                            print(f"ENTRY #{self.total_entries} (Sayfa {page_num}, Entry {i+1})")
                            print(f"TARİH: {entry_data['date']}")
                            print("-" * 80)
                            print(f"{entry_data['full_content']}")
                            print("=" * 80)
                        
                    except Exception as e:
                        print(f"Entry {i + 1} işlenirken hata: {str(e)}")
                        continue
                
                return True
                
            except Exception as e:
                retries += 1
                print(f"Sayfa {page_num} işlenirken hata (Deneme {retries}/{max_retries}): {str(e)}")
                
                # Hata alınca driver'ı yeniden başlat
                if retries < max_retries:
                    try:
                        print("Tarayıcı yeniden başlatılıyor...")
                        self.driver.quit()
                        time.sleep(3)
                        self.start_driver()
                        time.sleep(2)
                    except Exception as driver_error:
                        print(f"Driver yeniden başlatılırken hata: {str(driver_error)}")
                
                time.sleep(5)  # Yeniden denemeden önce bekle
        
        print(f"Sayfa {page_num} için maksimum deneme sayısına ulaşıldı.")
        return False

    def scrape_entries(self):
        try:
            for page in range(1, self.max_pages + 1):
                page_success = self.scrape_page(page)
                
                # Sayfayı çekemediyse durdur
                if not page_success:
                    print(f"Sayfa {page} çekilemedi, işlem durduruluyor.")
                    break
                
                # Her 5 sayfada bir driver'ı yenile
                if page % 5 == 0 and page < self.max_pages:
                    print("Driver düzenli olarak yenileniyor...")
                    # Driver'ı yenile
                    self.driver.quit()
                    time.sleep(3)
                    self.start_driver()
                
            print(f"\nToplam {self.total_entries} entry başarıyla alındı ve CSV'ye kaydedildi.")
        except Exception as e:
            print(f"Entry çekme sırasında hata oluştu: {str(e)}")
    
    def close(self):
        if self.csv_file:
            self.csv_file.close()
            print(f"CSV dosyası kapatıldı: {self.csv_filename}")
        
        if self.driver:
            print("Tarayıcı kapatılıyor...")
            self.driver.quit()

if __name__ == "__main__":
    scraper = None
    try:
        # URL'yi terminalde girebilirsiniz
        topic_url = input("URL giriniz: ")
        
        # Sadece sayfa sayısını sor
        try:
            pages = int(input("Kaç sayfa çekilsin: "))
        except ValueError:
            pages = 1
            print("Geçersiz değer, varsayılan olarak 1 sayfa çekilecek.")

        print(f"\n{topic_url} için {pages} sayfa entry çekiliyor...")

        scraper = EksiSozlukScraper(topic_url=topic_url, max_pages=pages)
        scraper.start_driver()
        scraper.scrape_entries()

    except Exception as e:
        print(f"Program çalışırken hata oluştu: {str(e)}")
    finally:
        if scraper:
            scraper.close()