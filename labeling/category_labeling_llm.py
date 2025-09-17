import pandas as pd
import time
import ollama
import os
from tqdm import tqdm
import json
import random
from functools import lru_cache
import colorama
from colorama import Fore, Style
import datetime


colorama.init()

CONFIG = {
    'output_folder': 'kategori_sonuclari',  
    'model_name': "gemma2:9b",
    'max_retries': 3,
    'retry_delay': 1,
    'cache_size': 1000 
}

def print_colored(text, color=Fore.WHITE, style=Style.NORMAL, end='\n'):
    """Renkli metin yazdır"""
    print(f"{style}{color}{text}{Style.RESET_ALL}", end=end)

def print_header(text, width=50):
    """Başlık yazdır"""
    print_colored("=" * width, Fore.CYAN, Style.BRIGHT)
    print_colored(text.center(width), Fore.CYAN, Style.BRIGHT)
    print_colored("=" * width, Fore.CYAN, Style.BRIGHT)

def print_subheader(text):
    """Alt başlık yazdır"""
    print_colored(f"\n--- {text} ---", Fore.YELLOW, Style.BRIGHT)

@lru_cache(maxsize=CONFIG['cache_size'])
def analyze_comment_for_category(comment, category, description):
    """Bir yorumu tek bir kategori için analiz et"""
    prompt = f"""
    Lütfen aşağıdaki yorumu '{category}' kategorisi için analiz et.
    
    YORUM: "{comment}"
    
    '{category}' kategorisi için sadece 1 (evet) veya 0 (hayır) olarak cevap ver.
    
    KATEGORİ AÇIKLAMASI:
    {description}
    """
    
   
    for attempt in range(CONFIG['max_retries']):
        try:
            print_colored(f"Yorum analiz ediliyor... Deneme: {attempt+1}/{CONFIG['max_retries']}", Fore.BLUE)
            
            response = ollama.chat(
                model=CONFIG['model_name'],
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1}
            )
            
          
            response_text = response['message']['content'].lower()
            
           
            result = 1 if ('1' in response_text or 'evet' in response_text) else 0
            
            print_colored(f"Analiz sonucu: {result}", Fore.GREEN if result == 1 else Fore.RED)
            return result
            
        except Exception as e:
            print_colored(f"Hata: {str(e)}", Fore.RED)
            if attempt < CONFIG['max_retries'] - 1:
                print_colored(f"{CONFIG['retry_delay']} saniye bekleniyor...", Fore.YELLOW)
                time.sleep(CONFIG['retry_delay'])
   
    print_colored("Tüm denemeler başarısız oldu! Varsayılan sonuç: 0", Fore.RED, Style.BRIGHT)
    return 0

def print_category_progress(category, count, target, type_label=""):
    """Kategori ilerleme durumunu yazdır"""
    percentage = (count / target * 100) if target > 0 else 0
    progress_bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
    status = f"[{count}/{target}]"
    
    color = Fore.GREEN if type_label == "Pozitif" else Fore.RED
    
    type_text = f"{type_label} " if type_label else ""
    print_subheader(f"{category} Kategorisi {type_text}İlerlemesi")
    print_colored(f"İlerleme: {progress_bar} {status} - %{percentage:.1f}", color)
    print_colored(f"Hedef: {target} adet {type_label.lower()} eşleşme bulmak", Fore.CYAN)
    print_colored("-----------------------------", Fore.YELLOW)

def save_category_results(category, results, output_file):
    """Bir kategori için sonuçları kaydet"""
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print_colored(f"Sonuçlar {output_file} dosyasına kaydedildi.", Fore.GREEN, Style.BRIGHT)

def process_category(category_name, category_description, target_positive, target_negative, df, file_type="all"):
    """Belirtilen kategori için yorumları analiz et"""
    print_header(f"KATEGORİ: {category_name}")
    print_colored(f"Açıklama: {category_description}", Fore.CYAN)
    
   
    results = []
    
    
    count_positive = 0
    count_negative = 0
    
    
    safe_category_name = "".join(c if c.isalnum() else "_" for c in category_name)
    
    
    os.makedirs(CONFIG['output_folder'], exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    output_file = os.path.join(CONFIG['output_folder'], f"{safe_category_name}_{timestamp}.csv")
    
   
    checkpoint_file = os.path.join(CONFIG['output_folder'], f"{safe_category_name}_checkpoint.json")
    
    processed_indices = []
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            
            if checkpoint['target_positive'] == target_positive and checkpoint['target_negative'] == target_negative and checkpoint['category'] == category_name:
                results = checkpoint['results']
                count_positive = checkpoint['count_positive']
                count_negative = checkpoint['count_negative']
                processed_indices = checkpoint.get('processed_indices', [])
                
                print_colored(f"Checkpoint yüklendi. Şimdiye kadar {count_positive}/{target_positive} adet pozitif eşleşme ve {count_negative}/{target_negative} adet negatif eşleşme bulundu.", Fore.GREEN)
                print_colored(f"{len(processed_indices)} yorum işlendi.", Fore.BLUE)
                
                
                remaining_indices = [i for i in range(len(df)) if i not in processed_indices]
            else:
                
                results = []
                count_positive = 0
                count_negative = 0
                processed_indices = []
                remaining_indices = list(range(len(df)))
        except Exception as e:
            print_colored(f"Checkpoint yükleme hatası: {str(e)}. Yeniden başlanıyor.", Fore.RED)
            results = []
            count_positive = 0
            count_negative = 0
            processed_indices = []
            remaining_indices = list(range(len(df)))
    else:
        
        results = []
        count_positive = 0
        count_negative = 0
        processed_indices = []
        remaining_indices = list(range(len(df)))
    
    
    if file_type == "all":
       
        random.shuffle(remaining_indices)
    elif file_type == "positive_only":
       
        pass
    elif file_type == "all_comments":
       
        pass
    
    
    print_category_progress(category_name, count_positive, target_positive, "Pozitif")
    print_category_progress(category_name, count_negative, target_negative, "Negatif")
    
    
    start_time = time.time()
    total_target = target_positive + target_negative if file_type != "all_comments" else len(remaining_indices)
    
    with tqdm(total=total_target, 
              desc=f"{category_name} İşleniyor", 
              colour="green") as pbar:
        
        if file_type != "all_comments":
            pbar.update(count_positive + count_negative) 
        
        for i in remaining_indices:
           
            if count_positive >= target_positive and count_negative >= target_negative and file_type != "all_comments":
                print_colored(f"\n{category_name} için hedefler tamamlandı! ({target_positive} pozitif, {target_negative} negatif eşleşme bulundu)", Fore.GREEN, Style.BRIGHT)
                break
                
            row = df.iloc[i]
            date = row.get('Tarih', 'Tarih Yok')
            comment = row.get('Yorum', '')
            
            if not isinstance(comment, str) or len(comment.strip()) == 0:
                processed_indices.append(i)
                if file_type == "all_comments":
                    pbar.update(1)
                continue
            
           
            if count_positive >= target_positive and count_negative < target_negative and file_type != "all_comments":
               
                result = analyze_comment_for_category(comment, category_name, category_description)
                if result == 1:
                   
                    processed_indices.append(i)
                    continue
            
          
            if count_negative >= target_negative and count_positive < target_positive and file_type != "all_comments":
                
                result = analyze_comment_for_category(comment, category_name, category_description)
                if result == 0:
                    
                    processed_indices.append(i)
                    continue
            
            
            if 'result' not in locals():
                result = analyze_comment_for_category(comment, category_name, category_description)
            
           
            result_dict = {
                'Tarih': date,
                'Yorum': comment,
                'Sonuç': result
            }
            results.append(result_dict)
            
            
            processed_indices.append(i)
            
           
            if result == 1:
                count_positive += 1
                if count_positive <= target_positive and file_type != "all_comments":
                    pbar.update(1)  
                
               
                if count_positive <= target_positive or file_type == "all_comments":
                    print_colored("\nYENİ POZİTİF EŞLEŞME BULUNDU!", Fore.GREEN, Style.BRIGHT)
                    print_colored(f"Kategori: {category_name} - İlerleme: {count_positive}/{target_positive}", Fore.YELLOW)
                    print_colored(f"Yorum: {comment[:150]}..." if len(comment) > 150 else f"Yorum: {comment}", Fore.CYAN)
                    print_colored("-" * 50, Fore.YELLOW)
            else:  
                count_negative += 1
                if count_negative <= target_negative and file_type != "all_comments":
                    pbar.update(1)  
               
                if count_negative <= target_negative or file_type == "all_comments":
                    print_colored("\nYENİ NEGATİF EŞLEŞME BULUNDU!", Fore.RED, Style.BRIGHT)
                    print_colored(f"Kategori: {category_name} - İlerleme: {count_negative}/{target_negative}", Fore.YELLOW)
                    print_colored(f"Yorum: {comment[:150]}..." if len(comment) > 150 else f"Yorum: {comment}", Fore.CYAN)
                    print_colored("-" * 50, Fore.YELLOW)
            
           
            if 'result' in locals():
                del result
            
            if file_type == "all_comments":
                pbar.update(1)
            
           
            if len(results) % 5 == 0:
              
                elapsed_time = time.time() - start_time
                total_count = count_positive + count_negative
                
                if file_type != "all_comments" and total_count > 0:
                    total_target = target_positive + target_negative
                    estimated_total = (elapsed_time / total_count) * total_target
                    remaining_time = max(0, estimated_total - elapsed_time)
                else:
                    remaining_time = 0
                
                checkpoint = {
                    'category': category_name,
                    'target_positive': target_positive,
                    'target_negative': target_negative,
                    'count_positive': count_positive,
                    'count_negative': count_negative,
                    'results': results,
                    'processed_indices': processed_indices,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                with open(checkpoint_file, 'w', encoding='utf-8') as f:
                    json.dump(checkpoint, f, ensure_ascii=False)
                
                if file_type != "all_comments":
                    print_category_progress(category_name, count_positive, target_positive, "Pozitif")
                    print_category_progress(category_name, count_negative, target_negative, "Negatif")
                    
               
                    if remaining_time > 0:
                        hours, remainder = divmod(remaining_time, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        print_colored(f"Tahmini kalan süre: {int(hours)}:{int(minutes):02d}:{int(seconds):02d}", Fore.BLUE)
    

    save_category_results(category_name, results, output_file)

    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    print_header("İŞLEM TAMAMLANDI")
    print_colored(f"Toplam süre: {int(hours)}:{int(minutes):02d}:{int(seconds):02d}", Fore.BLUE)
    print_colored(f"İşlenen yorum sayısı: {len(processed_indices)}", Fore.YELLOW)
    print_colored(f"Bulunan pozitif eşleşme sayısı: {count_positive}/{target_positive}", Fore.GREEN)
    print_colored(f"Bulunan negatif eşleşme sayısı: {count_negative}/{target_negative}", Fore.RED)
    

    return (count_positive >= target_positive and count_negative >= target_negative), count_positive, count_negative, output_file

def get_default_categories_and_descriptions():
    """Referans için öntanımlı kategorileri ve açıklamalarını döndürür"""
    categories = [
        "Güven", "Bilgi Erişimi", "Sipariş", "Ödeme (Seçenekler)", 
        "Stok", "Kullanıcı Dostu Arayüz", "Kişiselleştirilmiş Bilgi",
        "Sohbet Desteği", "Ürün", "Boykot", "İndirim", "Yarışma",
        "Hedonik Değer", "İade / İptal / Değişim", "Teslimat", "Teslimat Süresi"
    ]
    
    descriptions = {
        "Güven": """
        Kullanıcıların uygulamanın vaat ettiklerini yapacağına, kendilerine zarar vermeyeceğine (veri çalmayacağına, kötü amaçlı yazılım yüklemeyeceğine), bilgilerini sorumlu bir şekilde kullanacağına ve güvenilir bir şekilde çalışacağına inanması anlamına gelir.
        Anahtar Kelimeler: Bilgi, Veri, Toplamak, Saklamak, Korumak, Gizlilik, Veri gizliliği, Veri Kullanımı, Kişisel veri, Paylaşmak, Veri paylaşımı, Çalışmak, İstikrarlı, Şeffaf, Açıklık, Yardım, Sorumlu, Güvenlik, Veri güvenliği, Siber güvenlik, Malware, Şifreleme, Güvenlik bağlantı, Kimlik doğrulama
        """,
        "Bilgi Erişimi": """
        Uygulamanın işlevini yerine getirebilmek için ihtiyaç duyduğu verilere ulaşması ve bu verileri kullanmasıdır.
        Anahtar Kelimeler: Rehber, Kişi listesi, Fotoğraf, Video, Konum, Takvim, Etkinlik, Mesajlar, Depolama, Kamera, Mikrofon, Profil bilgileri, Kullanıcı bilgileri, Sosyal Medya, Katalog, Harita, API, Veri erişimi, Bilgi erişimi
        """,
        "Sipariş": """
        Müşterinin uygulamayı kullanarak ürün satın alma işlemini gerçekleştirmesidir.
        Anahtar Kelimeler: Müşteri, İstek, Tercih, Seçim, Seçmek, Sepet, Eklemek, Çıkarmak, Onaylamak, Sipariş onayı, Ödemek, Ödeme yöntemi, Kredi kartı, Banka kartı, Kapıda ödeme, Online ödeme
        """,
        "Ödeme (Seçenekler)": """
        Müşterilerin uygulamada seçmiş oldukları ürün/ürünleri satın alma isteğine dönüştürdüğü bölümdür.
        Anahtar Kelimeler: Kredi kartı, Banka kartı, Sanal Kart, Kapıda ödeme, Havale, EFT, Cüzdan, Dijital cüzdan, Mobil ödeme, Puanla ödeme, Taksit, Ödeme yap, Ödeme seçenekleri
        """,
        "Stok": """
        Uygulamada yer verilen ürünlerin seçilen mağazadaki satışa hazır olan miktarını göstermektedir.
        Anahtar Kelimeler: Satın almak, Envanter, Sepete eklemek, Seçmek, Mağaza, Şube, Stok miktarı, Stokta var, Stokta yok, Tükendi, Sınırlı stok, Stok durumu, Stok takibi
        """,
        "Kullanıcı Dostu Arayüz": """
        Kullanım kolaylığı, anlaşılırlığı ve verimliliği ile uygulamanın müşterilerine olumlu ve etkili bir deneyim sunmasıdır.
        Anahtar Kelimeler: Kullanıcı arayüzü, Kullanıcı deneyimi, Kullanılabilirlik, Kolay kullanım, Basitlik, Yalın, Sezgisel, Anlaşılır, Öğrenilebilir, Kolayca gezinme
        """,
        "Kişiselleştirilmiş Bilgi": """
        Kişiselleştirilmiş bilgi, market zincirlerinin müşteri yorumlarını analiz ederek, kullanıcının davranışları, tercihleri ve özelliklerine göre uyarlanmış içerik sunmayı amaçlar. Bu, müşteriye özel teklifler, indirimler, son görüntülenen ürünler veya terk edilmiş sepet hatırlatıcıları gibi önerilerle kullanıcı deneyimini benzersiz, sezgisel ve alakalı hale getirir. Müşterinin kişisel verileri, bildirim tercihleri ve geçmiş etkileşimleri dikkate alınarak, veri analizi ve makine öğrenimiyle desteklenen öneri motorları aracılığıyla dinamik ve hedeflenmiş içerik üretilir. Böylece müşteri memnuniyeti, sadakati ve katılımı artırılarak satın alma veya abonelik motivasyonu güçlendirilir.
        Anahtar Kelimeler: Kişiselleştirilmiş bilgi, Kişiselleştirilmiş öneriler, Kişiselleştirilmiş içerik, Kişiselleştirilmiş teklifler, Kişiselleştirilmiş bildirimler, Kişiselleştirilmiş deneyim, Kişisel veriler, Veri analizi, Makine öğrenimi, Öneri motorları, Dinamik içerik, Hedeflenmiş içerik, Kullanıcı davranışları, Kullanıcı tercihleri, Kullanıcı özellikleri
        """,
        "Sohbet Desteği": """
        Uygulamanın sohbet / mesajlaşma yoluyla müşteri desteği sağlamasıdır.
        Anahtar Kelimeler: Sohbet desteği, Canlı destek, ChatBot, Sohbet robotu, Uygulama içi sohbet, Mesajlaşma desteği, Müşteri hizmetleri, Teknik destek, Yardım merkezi
        """,
        "Ürün": """
        Marketlerin uygulamaları aracılığıyla müşterilerine satın almaları amacıyla sundukları çeşitli eşyalardır.
        Anahtar Kelimeler: Renk, Boyut, Marka, Tür, Kalite, Muadil, Sepete eklemek, Satın almak, Stok, Katalog, Koleksiyon, Listelemek, Ayrıntılar, Eşya, Parça, Çeşit
        """,
        "Boykot": """
        Kullanıcıların, bir markayı ya da ürün grubunu politik, ahlaki veya dini sebeplerle kullanmayı bırakması, alışveriş yapmaması, uygulamayı silmesi ya da sosyal medyada boykot çağrısı yapması. Bu eylemler çoğunlukla İsrail-Filistin çatışması, toplumsal adaletsizlik, etik dışı davranışlar gibi konular etrafında şekillenir.
        Anahtar Kelimeler:Boykot, Reddetmek, Kullanmamak, Silmek, Terk etmek, Bırakmak, Protesto etmek, İsrail, Filistin, İsrail malı, İsrailli, Filistin'e destek, Tepki, Hareket, Boykot kampanyası, Çağrı, Boykot çağrısı, Destek vermemek, İslam, Yahudi, Masum, Kadın ve çocuklar, Katledilmek, Haksızlık, Barbarlık, Hukuksuzluk, Hainlik, Çocuk katili, Katil, Bombalanmak, Terörist, Terör devleti, Kullanmamak, Satın almamak, Kamuoyu baskısı, Marka imajı

        """,
        "İndirim": """
        Bir ürün veya hizmetin normal fiyatında yapılan aşağı yönlü hareketler / fiyat indirimleridir.
        Anahtar Kelimeler: Kampanya, Fırsat, Promosyon, Ucuzluk, Avantaj, Teklif, Kupon, Hediye çeki, Bedava, İskonto, Özel fiyat, İndirim kodu
        """,
        "Yarışma": """
        Uygulama indirme sayısını / kullanımını ve kullanıcıların etkileşimlerini artırmak amacıyla düzenlenen etkinliklerdir.
        Anahtar Kelimeler: Çekiliş, Ödül, Hediye, Kazan, Katılım, Anket, Oyun, Sosyal medya yarışması, Katıl, Oyna, Cevapla, Paylaş
        """,
        "Hedonik Değer": """
        Yapılan alışverişten elde edilen haz, keyif, eğlence ve duygusal tatmindir.
        Anahtar Kelimeler: Duygu, Keyif, Eğlence, Haz, Zevk, Heyecan, Memnuniyet, Duygusal bağlılık, Estetik zevk, Rahatlama, Merak
        """,
        "İade / İptal / Değişim": """
        Müşterilerin uygulama üzerinden gerçekleştirdikleri satın alma veya sürdürme işlemlerini geri alma, durdurma veya değiştirme süreçlerini ifade eder.
        Anahtar Kelimeler: İade, İptal, Değişim, Geri ödeme, Cayma hakkı, Sipariş iptali, Üyelik iptali, İade talebi, Değişim talebi, Geri gönderme
        """,
        "Teslimat": """
        Müşterilerin mobil uygulamalar vasıtasıyla sipariş ettiği ürünün mağazadan / depodan belirtilen adrese belirtilen zaman aralığında ulaştırılması sürecidir.
        Anahtar Kelimeler: Teslimat, Gönderim, Sevkiyat, Adres, Adres seçmek, Ev, Kapı, Sipariş takibi, Teslimat adresi, Teslimat süresi
        """,
        "Teslimat Süresi": """
        Siparişin verilmesi ile teslimatın gerçekleşmesi arasında geçen zaman dilimidir.
        Anahtar Kelimeler: Zaman, Süre, Dönem, Program, Randevu, Tahmini varış zamanı, Aralık, Saat, Gün, Hızlı, Çabuk, Aynı gün
        """
    }
    return categories, descriptions

def main():
    print_header("Tek Kategori Analiz Programı", 60)
    print_colored("\nVeri setini seçin:", Fore.YELLOW)
    print_colored("1. filtrelenmis_yorumlar.csv (varsayılan)", Fore.CYAN)
    print_colored("2. Başka bir CSV dosyası", Fore.CYAN)
    
    choice = input("Seçiminiz (1/2): ").strip()
    
    if choice == "2":
        csv_file_path = input("CSV dosya yolunu girin: ").strip()
    else:
        csv_file_path = "filtrelenmis_yorumlar.csv"
    
   
    categories, descriptions = get_default_categories_and_descriptions()
    
    print_colored("\nÖnceden tanımlı kategoriler:", Fore.YELLOW)
    for i, category in enumerate(categories, 1):
        print_colored(f"{i}. {category}", Fore.CYAN)
    
    print_colored("\nİşlem türünü seçin:", Fore.YELLOW)
    print_colored("1. Önceden tanımlı kategorilerden birini seç", Fore.CYAN)
    print_colored("2. Özel kategori tanımla", Fore.CYAN)
    
    category_choice = input("Seçiminiz (1/2): ").strip()
    
    if category_choice == "1":
       
        cat_index = int(input("\nKategori numarası seçin (1-16): ")) - 1
        if 0 <= cat_index < len(categories):
            category_name = categories[cat_index]
            category_description = descriptions[category_name]
        else:
            print_colored("Geçersiz kategori numarası. Program sonlandırılıyor.", Fore.RED)
            return
    else:
        
        category_name = input("\nKategori adı: ")
        
        
        print_colored("\nKategori açıklaması ve anahtar kelimeleri girin:", Fore.YELLOW)
        print_colored("(Birden fazla satır yazabilirsiniz. Bitirmek için boş bir satır girin)", Fore.BLUE)
        category_description = ""
        while True:
            line = input()
            if not line: 
                break
            category_description += line + "\n"
    
    
    print_colored("\nAnalizin nasıl yapılacağını seçin:", Fore.YELLOW)
    print_colored("1. Belirli sayıda pozitif ve negatif eşleşme bulana kadar rastgele ara (varsayılan)", Fore.CYAN)
    print_colored("2. Tüm yorumları analiz et ve hepsini CSV'ye kaydet", Fore.CYAN)
    
    process_type = input("Seçiminiz (1/2): ").strip()
    
   
    if process_type != "2":
        target_positive = int(input("\nBu kategori için kaç tane pozitif eşleşme (1) bulmak istiyorsunuz?: "))
        target_negative = int(input("Bu kategori için kaç tane negatif eşleşme (0) bulmak istiyorsunuz?: "))
        file_type = "all"  
    else:
        target_positive = 0  
        target_negative = 0
        file_type = "all_comments"  
    
    
    try:
        print_colored(f"\nVeri seti yükleniyor: {csv_file_path}", Fore.BLUE)
        df = pd.read_csv(csv_file_path)
        print_colored(f"Veri seti yüklendi. Toplam {len(df)} yorum var.", Fore.GREEN)
    except Exception as e:
        print_colored(f"CSV yükleme hatası: {str(e)}", Fore.RED, Style.BRIGHT)
        return
    
   
    completed, count_positive, count_negative, output_file = process_category(
        category_name, 
        category_description, 
        target_positive,
        target_negative,
        df,
        file_type
    )
    

    print_header("SONUÇ RAPORU")
    
    if file_type == "all_comments":
        print_colored(f"Tüm yorumlar {category_name} kategorisi için analiz edildi.", Fore.GREEN, Style.BRIGHT)
        print_colored(f"Toplam {count_positive} adet pozitif eşleşme ve {count_negative} adet negatif eşleşme bulundu.", Fore.YELLOW)
    elif completed:
        print_colored(f"{category_name} kategorisi için {target_positive} adet pozitif ve {target_negative} adet negatif eşleşme bulundu!", Fore.GREEN, Style.BRIGHT)
    else:
        print_colored(f"{category_name} kategorisi için {count_positive}/{target_positive} adet pozitif ve {count_negative}/{target_negative} adet negatif eşleşme bulunabildi.", Fore.YELLOW)
        print_colored("Tüm yorumlar işlendi, ancak hedef sayılara tam olarak ulaşılamadı.", Fore.RED)
    
    print_colored(f"\nSonuçlar şu dosyada kaydedildi: {output_file}", Fore.CYAN)
    print_colored(f"\nProgram tamamlandı. Teşekkürler!", Fore.GREEN, Style.BRIGHT)

if __name__ == "__main__":
    main()