import pandas as pd
import csv
import os

def filtrele_yorumlar():
    """
    Yorumların kelime sayısı 5'ten küçük olanları filtreleyen fonksiyon
    """
    try:
        # CSV dosyasını oku - doğrudan dosya yolunu belirtiyoruz
        dosya_yolu = "C:/Users/hamdi/Desktop/CSV Halil Tez/birlesik_yorumlar.csv"
        cikti_dosyasi = "C:/Users/hamdi/Desktop/CSV Halil Tez/filtrelenmis_yorumlar.csv"
        
        df = pd.read_csv(dosya_yolu)
        
        # Yorumların bulunduğu sütunun adını belirle
        yorum_sutunu = 'Yorum'
        
        if yorum_sutunu not in df.columns:
            print(f"UYARI: '{yorum_sutunu}' adlı sütun bulunamadı.")
            print(f"Mevcut sütunlar: {df.columns.tolist()}")
            print("Lütfen kod içerisindeki 'yorum_sutunu' değişkenini CSV dosyanızdaki doğru sütun adıyla değiştirin.")
            return
        
        # Orijinal veri sayısı
        orijinal_satir_sayisi = len(df)
        
        # Kelime sayısı 5'ten az olan yorumları filtrele
        df_filtrelenmis = df[df[yorum_sutunu].apply(lambda x: 
                              len(str(x).split()) >= 5 if pd.notnull(x) else False)]
        
        # Filtrelenmiş veri sayısı
        filtrelenmis_satir_sayisi = len(df_filtrelenmis)
        
        # Filtrelenmiş veriyi yeni CSV dosyasına kaydet
        df_filtrelenmis.to_csv(cikti_dosyasi, index=False)
        
        print(f"İşlem tamamlandı!")
        print(f"Orijinal satır sayısı: {orijinal_satir_sayisi}")
        print(f"Filtrelenmiş satır sayısı: {filtrelenmis_satir_sayisi}")
        print(f"Çıkarılan satır sayısı: {orijinal_satir_sayisi - filtrelenmis_satir_sayisi}")
        print(f"Filtrelenmiş veriler '{cikti_dosyasi}' dosyasına kaydedildi.")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")

# Ana program
if __name__ == "__main__":
    # Fonksiyonu çağır - artık parametre almıyor
    filtrele_yorumlar()