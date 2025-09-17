import pandas as pd
import csv
import os

def filtrele_yorumlar():
    """
    Yorumların kelime sayısı 5'ten küçük olanları filtreleyen fonksiyon
    """
    try:
       
        # Define relative paths for input and output
        # Assumes 'birlesik_yorumlar.csv' is in the project's root directory
        dosya_yolu = "birlesik_yorumlar.csv"
        
        # Create an 'outputs' directory if it doesn't exist
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        cikti_dosyasi = os.path.join(output_dir, "filtrelenmis_yorumlar.csv")
        
        df = pd.read_csv(dosya_yolu)
        
        
        yorum_sutunu = 'Yorum'
        
        if yorum_sutunu not in df.columns:
            print(f"UYARI: '{yorum_sutunu}' adlı sütun bulunamadı.")
            print(f"Mevcut sütunlar: {df.columns.tolist()}")
            print("Lütfen kod içerisindeki 'yorum_sutunu' değişkenini CSV dosyanızdaki doğru sütun adıyla değiştirin.")
            return
        
        
        orijinal_satir_sayisi = len(df)
        
       
        df_filtrelenmis = df[df[yorum_sutunu].apply(lambda x: 
                              len(str(x).split()) >= 5 if pd.notnull(x) else False)]
        
        
        filtrelenmis_satir_sayisi = len(df_filtrelenmis)
        
        
        df_filtrelenmis.to_csv(cikti_dosyasi, index=False)
        
        print(f"İşlem tamamlandı!")
        print(f"Orijinal satır sayısı: {orijinal_satir_sayisi}")
        print(f"Filtrelenmiş satır sayısı: {filtrelenmis_satir_sayisi}")
        print(f"Çıkarılan satır sayısı: {orijinal_satir_sayisi - filtrelenmis_satir_sayisi}")
        print(f"Filtrelenmiş veriler '{cikti_dosyasi}' dosyasına kaydedildi.")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")


if __name__ == "__main__":
    
    filtrele_yorumlar()