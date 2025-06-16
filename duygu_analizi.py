import pandas as pd
import numpy as np
import os
import time
import warnings
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
warnings.filterwarnings('ignore')

# BERT model ve tokenizer'ı yükle
print("🤖 BERT modeli yükleniyor...")
model_name = "savasy/bert-base-turkish-sentiment-cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
print("✅ BERT modeli yüklendi!")

# Duygu analizi fonksiyonu
def analyze_sentiment(text):
    try:
        # Metni tokenize et ve model inputunu hazırla
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        
        # Modeli değerlendirme moduna al ve tahmin yap
        model.eval()
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            sentiment_scores = predictions[0].tolist()
            
        # En yüksek olasılıklı sınıfı seç (0: negatif, 1: pozitif)
        sentiment = "Pozitif" if sentiment_scores[1] > sentiment_scores[0] else "Negatif"
        # Polarite değerini hesapla (-1 ile 1 arasında)
        polarity = sentiment_scores[1] - sentiment_scores[0]
        
        return sentiment, polarity
    except Exception as e:
        print(f"⚠️ Duygu analizi hatası: {str(e)}")
        return "Nötr", 0.0

# Zaman ölçümü başlat
start_time = time.time()

print("\n🚀 DUYGU ANALİZİ İŞLEMİ BAŞLADI")
print("-------------------------------")

# TAHMİN SONUÇLARI EXCEL DOSYASI
tahmin_sonuclari = r"tahmin_sonuclari.xlsx"

# Önce dosyanın varlığını kontrol et
if not os.path.exists(tahmin_sonuclari):
    print(f"⚠️ HATA: Excel dosyası bulunamadı!")
    print(f"Aranan konum: {tahmin_sonuclari}")
    print("Lütfen dosya yolunu kontrol edin.")
    exit()

# Veriyi yükle
try:
    df = pd.read_excel(tahmin_sonuclari)
    print(f"📥 Tahmin sonuçları yüklendi: {len(df)} örnek")
except Exception as e:
    print(f"⚠️ Excel dosyası yüklenirken hata oluştu: {str(e)}")
    exit()

# Kategori sütunlarını bul (model_*.pkl dosyalarından çıkarılan kategoriler)
kategori_sutunlari = [col for col in df.columns if col not in ['Yorum', 'Tarih']]
print(f"📊 Bulunan kategori sayısı: {len(kategori_sutunlari)}")
print(f"📊 Kategoriler: {', '.join(kategori_sutunlari)}")

# Duygu analizi için yeni sütunlar ekle
df['Duygu_Polaritesi'] = 0.0
df['Duygu_Etiketi'] = 'Nötr'

# En az bir kategoride 1 olan yorumları bul
print("🔍 En az bir kategoride 1 olan yorumlar bulunuyor...")
bir_olan_satirlar = df[df[kategori_sutunlari].sum(axis=1) > 0]
print(f"✅ Toplam {len(bir_olan_satirlar)} yorumda en az bir kategoride 1 değeri var.")

# Duygu analizi yap
print("💭 Duygu analizi yapılıyor...")
analiz_sayisi = 0

for idx, row in bir_olan_satirlar.iterrows():
    try:
        yorum = row['Yorum']
        # BERT ile duygu analizi yap
        duygu_etiketi, polarite = analyze_sentiment(yorum)
        
        # Değerleri DataFrame'e kaydet
        df.at[idx, 'Duygu_Polaritesi'] = polarite
        df.at[idx, 'Duygu_Etiketi'] = duygu_etiketi
        
        analiz_sayisi += 1
        # Her 100 analizde bir ilerleme göster (BERT daha yavaş olduğu için 1000'den 100'e düşürdük)
        if analiz_sayisi % 100 == 0:
            print(f"   ➤ {analiz_sayisi}/{len(bir_olan_satirlar)} yorum analiz edildi.")
            
    except Exception as e:
        print(f"⚠️ Duygu analizi yapılırken hata oluştu: {str(e)}")
        df.at[idx, 'Duygu_Polaritesi'] = 0
        df.at[idx, 'Duygu_Etiketi'] = "Hata"

# Sonuçları kaydet
try:
    sonuc_dosyasi = "duygu_analizi_sonuclari.xlsx"
    df.to_excel(sonuc_dosyasi, index=False)
    print(f"\n💾 Duygu analizi sonuçları '{sonuc_dosyasi}' dosyasına kaydedildi.")
except Exception as e:
    print(f"⚠️ Excel dosyası oluşturulurken hata oluştu: {str(e)}")

# Duygu analizi istatistikleri
bir_olan_yorumlar = df[df[kategori_sutunlari].sum(axis=1) > 0]
pozitif_sayisi = (bir_olan_yorumlar['Duygu_Etiketi'] == 'Pozitif').sum()
negatif_sayisi = (bir_olan_yorumlar['Duygu_Etiketi'] == 'Negatif').sum()
notr_sayisi = (bir_olan_yorumlar['Duygu_Etiketi'] == 'Nötr').sum()

print("\n📊 DUYGU ANALİZİ İSTATİSTİKLERİ")
print(f"   ➤ Pozitif: {pozitif_sayisi} ({pozitif_sayisi/len(bir_olan_yorumlar)*100:.2f}%)")
print(f"   ➤ Negatif: {negatif_sayisi} ({negatif_sayisi/len(bir_olan_yorumlar)*100:.2f}%)")
print(f"   ➤ Nötr: {notr_sayisi} ({notr_sayisi/len(bir_olan_yorumlar)*100:.2f}%)")

# Toplam süreyi hesapla
total_time = time.time() - start_time
print(f"\n⏱️ Toplam çalışma süresi: {total_time:.2f} saniye")
print("\n✅ Duygu analizi işlemi tamamlandı!") 