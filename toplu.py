import pandas as pd
import time
import ollama
import os
from tqdm import tqdm
import json
import numpy as np
from functools import lru_cache
import random

CONFIG = {
    'output_file': 'sonuclar.xlsx',
    'checkpoint_file': 'checkpoint.json',
    'model_name': "gemma2:9b",
    'max_retries': 3,
    'retry_delay': 1,
    'cache_size': 1000  # Önbellek boyutu
}

def get_categories_and_descriptions():
    categories = [
        "Güven", "Bilgi Erişimi", "Sipariş", "Ödeme (Seçenekler)", 
        "Stok", "Kullanıcı Dostu Arayüz", "Kişiselleştirilmiş Bilgi",
        "Sohbet Desteği", "Ürün", "Boykot", "İndirim", "Yarışma",
        "Hedonik Değer", "İade / İptal / Değişim", "Teslimat", "Teslimat Süresi"
    ]
    
    descriptions = {
        "Güven": """
        Kullanıcıların uygulamanın vaat ettiklerini yapacağına, kendilerine zarar vermeyeceğine (veri çalmayacağına, kötü amaçlı yazılım yüklemeyeceğine), bilgilerini sorumlu bir şekilde kullanacağına ve güvenilir bir şekilde çalışacağına inanması anlamına gelir.
        Anahtar Kelimeler: Bilgi, Veri, Toplamak, Saklamak, Korumak, Gizlilik, Veril gizliliği, Veri Kullanımı, Kişisel veri, Paylaşmak, Veri paylaşımı, Çalışmak, İstikrarlı, Şeffaf, Açıklık, Yardım, Sorumlu, Güvenlik, Veri güvenliği, Siber güvenlik, Malware, Şifreleme, Güvenlik bağlantı, Kimlik doğrulama
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
        Uygulamanın, kullanıcısının davranışlarını, tercihlerini ve özelliklerini dikkate alarak müşterisine özel uyarladığı içeriklerdir.
        Anahtar Kelimeler: Kişiselleştirme, Özelleştirme, Bireyselleştirme, Kullanıcı modelleme, Uyarlama, İlgili olmak, Alakalı olmak, Kullanıcı verisi, Davranış takibi
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
        Müşterilerin, uygulamalarda yer verilen İsrail menşeili veya İsrail'e destek veren kuruluşların markalarına ait ürünleri toplu olarak reddetmesidir.
        Anahtar Kelimeler: Boykot, Reddetmek, Kullanmamak, Silmek, Terk etmek, Bırakmak, Protesto etmek, İsrail, Filistin, İsrail malı, İsrailli, Filistin'e destek
        """,
        "İndirim": """
        Bir ürün veya hizmetin normal fiyatında yapılan aşağı yönlü hareketler / fiyat indirimleridir.
        Anahtar Kelimeler: Kampanya, Fırsat, Promosyon, Ucuzluk, Avantaj, Teklif, Kupon, Hediye çeki, Bedava, İskonto, Özel fiyat, İndirim kodu
        """,
        "Yarışma": """
        Uygulama indirme sayısını / kullanımını ve kullanıcıların (beğeni, paylaşım, yorum, içerik oluşturma gibi) etkileşimlerini artırmak, potansiyel müşteri oluşturmak, kullanıcı verilerini toplamak, marka farkındalığı oluşturmak belirli bir ürünü tanıtmak veya uygulama kullanım trafiğini artırmak maksadıyla yarışmalar düzenlenebilmektedir.
        Yarışma neticesinde müşteriler belirli miktarlarda çeşitli indirim veya ücretsiz alışveriş imkanı elde etmektedirler.

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

@lru_cache(maxsize=CONFIG['cache_size'])
def analyze_comment(comment):
    """Yorumu analiz et (önbellekli)"""
    categories, descriptions = get_categories_and_descriptions()
    
    # Tüm kategoriler ve açıklamaları ile prompt oluştur
    prompt = f"""
    Lütfen aşağıdaki yorumu verilen kategoriler için analiz et.
    
    YORUM: "{comment}"
    
    Her kategori için sadece 1 (evet) veya 0 (hayır) olarak cevap ver.
    Her kategoriyi yeni satırda belirt.
    
    KATEGORİLER VE AÇIKLAMALARI:
    """
    
    # Tüm kategorileri ve açıklamalarını ekle
    for category in categories:
        prompt += f"\n\n{category}:\n{descriptions[category]}"
    
    # Retry mekanizması
    for attempt in range(CONFIG['max_retries']):
        try:
            print(f"Yorum analiz ediliyor... Deneme: {attempt+1}/{CONFIG['max_retries']}")
            
            response = ollama.chat(
                model=CONFIG['model_name'],
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1}
            )
            
            # Yanıtı işle
            response_text = response['message']['content']
            
            # Kategorilere göre sonuçları çıkart
            results = {}
            for category in categories:
                # Kategori adını içeren satırı bul
                category_lines = [line for line in response_text.split('\n') if category in line]
                if category_lines:
                    # Son satırdaki 1 veya 0'ı al
                    result = 1 if '1' in category_lines[-1] else 0
                    results[category] = result
                else:
                    results[category] = 0
            
            print("Analiz tamamlandı!")
            return results
            
        except Exception as e:
            print(f"Hata: {str(e)}")
            if attempt < CONFIG['max_retries'] - 1:
                print(f"{CONFIG['retry_delay']} saniye bekleniyor...")
                time.sleep(CONFIG['retry_delay'])
    
    # Tüm denemeler başarısız olursa varsayılan sonuç döndür
    print("Tüm denemeler başarısız oldu! Varsayılan sonuç döndürülüyor.")
    return {category: 0 for category in categories}

def process_single_comment(comment_data):
    """Tek yorumu işle"""
    try:
        date, comment = comment_data
        result = analyze_comment(comment)
        result_dict = {
            'Tarih': date,
            'Yorum': comment,
            **result
        }
        return result_dict
    except Exception as e:
        print(f"Yorum işleme hatası: {str(e)}")
        categories, _ = get_categories_and_descriptions()
        return {
            'Tarih': date,
            'Yorum': comment,
            **{category: 0 for category in categories}
        }

def save_checkpoint(results, category_counts, target, processed_count):
    """Checkpoint kaydet"""
    checkpoint = {
        'results': results,
        'category_counts': category_counts,
        'target': target,
        'processed_count': processed_count,
        'timestamp': time.time()
    }
    with open(CONFIG['checkpoint_file'], 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, ensure_ascii=False)
    print(f"\nCheckpoint kaydedildi. İşlenen yorum: {processed_count}")

def load_checkpoint():
    """Checkpoint yükle"""
    if os.path.exists(CONFIG['checkpoint_file']):
        try:
            with open(CONFIG['checkpoint_file'], 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Checkpoint yükleme hatası: {str(e)}")
    return None

def print_status(category_counts, target, processed, total):
    """Durum çıktısı yazdır"""
    print("\n" + "="*50)
    print(f"İşlenen Yorum: {processed}/{total} ({processed/total*100:.1f}%)")
    print("-"*50)
    print("Kategori Durumları:")
    
    # Kategorileri iki sütunda göster
    categories = list(category_counts.keys())
    for i in range(0, len(categories), 2):
        cat1 = categories[i]
        count1 = category_counts[cat1]
        percent1 = (count1/target*100) if target > 0 else 0
        
        if i+1 < len(categories):
            cat2 = categories[i+1]
            count2 = category_counts[cat2]
            percent2 = (count2/target*100) if target > 0 else 0
            print(f"{cat1:<25}: {count1}/{target} ({percent1:>5.1f}%) | {cat2:<25}: {count2}/{target} ({percent2:>5.1f}%)")
        else:
            print(f"{cat1:<25}: {count1}/{target} ({percent1:>5.1f}%)")
    
    print("="*50)

def print_category_status(category_counts, target):
    """Kategori durumlarını yazdır"""
    print("\n--- Kategori Durumları ---")
    for category, count in category_counts.items():
        percentage = (count / target * 100) if target > 0 else 0
        status = "[TAMAM]" if count >= target else f"[{count}/{target}]"
        print(f"{category:<25}: {status} - %{percentage:.1f}")
    print("-------------------------")

def print_comment_result(comment, result):
    """Yorum analiz sonucunu yazdır"""
    print("\n>>> Yorum:", comment[:50] + "..." if len(comment) > 50 else comment)
    found_categories = []
    
    for category, value in result.items():
        if value == 1:
            found_categories.append(category)
    
    if found_categories:
        print("Bulunan Kategoriler:", ", ".join(found_categories))
    else:
        print("Hiçbir kategori bulunamadı.")

def main():
    print("="*50)
    print("Yorum Analiz Programı - Tek Tek İşleme (Paralel olmadan)")
    print("="*50)
    
    categories, _ = get_categories_and_descriptions()
    target = int(input("Her kategori için kaç tane 1 istiyorsunuz?: "))
    
    # Veriyi yükle
    try:
        df = pd.read_csv("C:/Users/hamdi/Desktop/CSV Halil Tez/filtrelenmis_yorumlar.csv")
        print(f"Toplam {len(df)} yorum yüklendi.")
    except Exception as e:
        print(f"CSV yükleme hatası: {str(e)}")
        return
    
    # Checkpoint kontrolü
    checkpoint = load_checkpoint()
    if checkpoint and checkpoint['target'] == target:
        user_input = input("Önceki işlemden kalan bir checkpoint bulundu. Devam etmek istiyor musunuz? (e/h): ").lower()
        if user_input == 'e':
            results = checkpoint['results']
            category_counts = checkpoint['category_counts']
            processed_count = checkpoint['processed_count']
            print(f"İşlem kaldığı yerden devam ediyor. Şimdiye kadar {processed_count} yorum işlendi.")
            print_category_status(category_counts, target)
        else:
            results = []
            category_counts = {category: 0 for category in categories}
            processed_count = 0
    else:
        results = []
        category_counts = {category: 0 for category in categories}
        processed_count = 0
    
    # Hedeflere ulaşılıp ulaşılmadığını kontrol et
    all_targets_reached = all(count >= target for count in category_counts.values())
    
    if all_targets_reached:
        print("Tüm kategoriler için yeterli sayıda 1 bulundu!")
    else:
        print("Yorumlar analiz ediliyor...")
        
        # DataFrame'i rastgele sırala
        remaining_rows = list(range(len(df)))
        random.shuffle(remaining_rows)
        
        # Tek tek işleme (random sırayla)
        with tqdm(total=len(remaining_rows), desc="Yorumlar İşleniyor") as pbar:
            for i in remaining_rows:
                row = df.iloc[i]
                date = row['Tarih']
                comment = row['Yorum']
                
                # Eğer bu yorum daha önce işlenmişse atla
                if any(r.get('Yorum') == comment for r in results):
                    pbar.update(1)
                    continue
                
                # Yorumu analiz et
                result = analyze_comment(comment)
                
                # Sonuçları göster
                print_comment_result(comment, result)
                
                # Yeni 1'leri ekrana yazdır
                new_ones = []
                
                # Kategori sayaçlarını güncelle
                for category in categories:
                    if result[category] == 1:
                        # Bu kategori için yeni bir 1 bulduk mu?
                        if category_counts[category] < target:
                            category_counts[category] += 1
                            new_ones.append(category)
                
                # Yeni bulunan 1'leri göster
                if new_ones:
                    print("YENİ BULUNAN KATEGORİLER:", ", ".join(new_ones))
                
                # Sonuçları kaydet
                result_dict = {
                    'Tarih': date,
                    'Yorum': comment,
                    **result
                }
                results.append(result_dict)
                processed_count += 1
                pbar.update(1)
                
                # Her yorumdan sonra kategori durumunu göster
                if processed_count % 1 == 0:  # Her yorumdan sonra
                    print_category_status(category_counts, target)
                
                # Her 5 yorumda bir checkpoint kaydet
                if processed_count % 5 == 0:
                    save_checkpoint(results, category_counts, target, processed_count)
                
                # Tüm hedeflere ulaşıldıysa döngüyü sonlandır
                if all(count >= target for count in category_counts.values()):
                    print("\nTüm kategoriler için hedef sayıda 1 bulundu!")
                    break
    
    # Sonuçları kaydet
    result_df = pd.DataFrame(results)
    result_df.to_excel(CONFIG['output_file'], index=False)
    print(f"\nSonuçlar {CONFIG['output_file']} dosyasına kaydedildi.")
    
    # Final durum göster
    print_status(category_counts, target, processed_count, len(df))
    
    # Eksik 1'leri göster
    missing_ones = {category: max(0, target - category_counts[category]) for category in categories}
    if any(missing > 0 for missing in missing_ones.values()):
        print("\nEksik 1'ler (hedef sayıya ulaşılamayanlar):")
        for category, missing in missing_ones.items():
            if missing > 0:
                print(f"{category}: {missing} tane 1 eksik")
        print("\nNot: Tüm yorumlar işlendi fakat bazı kategoriler için hedef sayıda 1 bulunamadı.")

if __name__ == "__main__":
    main()