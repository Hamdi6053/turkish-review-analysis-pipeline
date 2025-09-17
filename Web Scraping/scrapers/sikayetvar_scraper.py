import time
import os
import json
import csv
import requests
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

class SikayetvarScraper:
    def __init__(self, market_name="migros", max_pages=1, show_full_comment=True, max_workers=5):
        self.market = market_name.lower()
        self.max_pages = max_pages
        self.comments = []
        self.total_comments = 0
        self.show_full_comment = show_full_comment
        self.max_workers = max_workers
        self.base_url = f"https://www.sikayetvar.com/{self.market}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.error_log_file = "hatali_sayfalar.txt"  # Hatalı sayfaları kaydedeceğimiz dosya

    def log_error(self, page_num, url):
        with open(self.error_log_file, "a", encoding="utf-8") as f:
            f.write(f"Sayfa {page_num} yüklenemedi: {url}\n")

    def get_comment_links(self, page_num):
        url = f"{self.base_url}?page={page_num}"
        print(f"\nSayfa {page_num} linkler yükleniyor: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                print(f"Hata: Sayfa {page_num} yüklenemedi. Durum kodu: {response.status_code}")
                self.log_error(page_num, url)  # Hata kaydını yap
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            comment_links = []

            cards = soup.select('.complaint-card a')
            for link in cards:
                href = link.get('href')
                if href and self.market in href:
                    comment_links.append(urljoin(self.base_url, href))

            if not comment_links:
                links = soup.select('a.complaint-layer')
                for link in links:
                    href = link.get('href')
                    if href and self.market in href:
                        comment_links.append(urljoin(self.base_url, href))

            if not comment_links:
                links = soup.select(f'a[href*="/{self.market}/"]')
                for link in links:
                    href = link.get('href')
                    if href and self.market in href:
                        comment_links.append(urljoin(self.base_url, href))

            comment_links = list(set(comment_links))
            print(f"{len(comment_links)} şikayet linki bulundu (Sayfa {page_num})")
            return comment_links
            
        except Exception as e:
            print(f"Sayfa {page_num} linklerini çekerken hata: {str(e)}")
            self.log_error(page_num, url)  # Hata kaydını yap
            return []

    def get_comment_content(self, url, page_num, comment_num):
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                print(f"Hata: {url} yüklenemedi. Durum kodu: {response.status_code}")
                self.log_error(page_num, url)  # Hata kaydını yap
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            content = ""

            selectors = [
                "div.complaint-description",
                "div.complaint-body",
                "article.complaint-content",
                "div.complaint-detail-description",
                ".complaint-detail"
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text().strip()
                    if content:
                        break

            if not content:
                return None

            date = "Tarih bulunamadı"
            date_element = soup.select_one('div[class*="js-tooltip"][class*="time"]')
            if date_element:
                date = date_element.get_text().strip()

            content = re.sub(r'\s+', ' ', content).strip()

            comment_data = {
                "sayfa": page_num,
                "sıra": comment_num,
                "içerik": content,
                "tarih": date,
            }

            if self.show_full_comment:
                print(f"Sayfa {page_num}, Yorum {comment_num} ({date}): {content}")
            else:
                short = content[:70] + "..." if len(content) > 70 else content
                print(f"Sayfa {page_num}, Yorum {comment_num} ({date}): {short}")

            return comment_data

        except Exception as e:
            print(f"Yorum içeriği alınamadı ({url}): {str(e)}")
            self.log_error(page_num, url)  # Hata kaydını yap
            return None

    def process_page(self, page_num):
        comment_links = self.get_comment_links(page_num)
        page_comments = []

        with ThreadPoolExecutor(max_workers=min(10, self.max_workers)) as executor:
            futures = {}
            for i, link in enumerate(comment_links):
                future = executor.submit(self.get_comment_content, link, page_num, i + 1)
                futures[future] = (link, i + 1)

            for future in as_completed(futures):
                comment_data = future.result()
                if comment_data:
                    page_comments.append(comment_data)
        time.sleep(10)

        return page_comments

    def scrape_comments(self):
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.process_page, page): page for page in range(1, self.max_pages + 1)}

                for future in as_completed(futures):
                    page_comments = future.result()
                    self.comments.extend(page_comments)
                    self.total_comments += len(page_comments)
                    print(f"Sayfa işlemi tamamlandı. Toplam: {self.total_comments} yorum")

            print(f"\nToplam {self.total_comments} yorum başarıyla alındı.")

            if self.comments:
                self.save_csv()

        except Exception as e:
            print(f"Yorum çekme sırasında hata oluştu: {str(e)}")
            if self.comments:
                self.save_csv()

    def save_json(self, filename=None):
        if not filename:
            filename = f"{self.market}_yorumlar.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.comments, f, ensure_ascii=False, indent=2)
        print(f"\nJSON kayıt tamamlandı: {filename}")

    def save_csv(self, filename=None):
        if not filename:
            filename = f"{self.market}_yorumlar.csv"
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["sayfa", "sıra", "içerik", "tarih"])
            writer.writeheader()
            writer.writerows(self.comments)
        print(f"CSV kayıt tamamlandı: {filename}")

if __name__ == "__main__":
    scraper = None
    try:
        market = input("Market adı: ") or "migros"
        try:
            pages = int(input("Kaç sayfa çekilsin: ") or 1)
        except ValueError:
            pages = 1

        max_workers = int(input("Kaç paralel işçi çalıştırılsın (önerilen: 5-10): ") or 5)
        show_full = input("Yorumların tamamını görmek istiyor musunuz? (E/H): ").strip().lower() == 'e'

        print(f"\n{market.capitalize()} için {pages} sayfa şikayet {max_workers} paralel işçi ile çekiliyor...")

        scraper = SikayetvarScraper(market_name=market, max_pages=pages, show_full_comment=show_full, max_workers=max_workers)
        scraper.scrape_comments()

    except Exception as e:
        print(f"Program çalışırken hata oluştu: {str(e)}")
        if scraper and scraper.comments:
            print("Hata nedeniyle program sonlandırılıyor. Çekilen yorumlar kaydediliyor...")
            scraper.save_csv()