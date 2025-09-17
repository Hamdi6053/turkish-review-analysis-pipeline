import pandas as pd
import numpy as np
import os
import time
import warnings
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
warnings.filterwarnings('ignore')


print("BERT modeli yükleniyor...")
model_name = "savasy/bert-base-turkish-sentiment-cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
print("✅ BERT modeli yüklendi!")


def analyze_sentiment(text):
    try:
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        
      
        model.eval()
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            sentiment_scores = predictions[0].tolist()
            
        
        sentiment = "Pozitif" if sentiment_scores[1] > sentiment_scores[0] else "Negatif"
        
        polarity = sentiment_scores[1] - sentiment_scores[0]
        
        return sentiment, polarity
    except Exception as e:
        print(f"⚠️ Duygu analizi hatası: {str(e)}")
        return "Nötr", 0.0


start_time = time.time()

print("\n🚀 DUYGU ANALİZİ İŞLEMİ BAŞLADI")
print("-------------------------------")


tahmin_sonuclari = r"tahmin_sonuclari.xlsx"


if not os.path.exists(tahmin_sonuclari):
    print(f"⚠️ HATA: Excel dosyası bulunamadı!")
    print(f"Aranan konum: {tahmin_sonuclari}")
    print("Lütfen dosya yolunu kontrol edin.")
    exit()


try:
    df = pd.read_excel(tahmin_sonuclari)
    print(f"📥 Tahmin sonuçları yüklendi: {len(df)} örnek")
except Exception as e:
    print(f"⚠️ Excel dosyası yüklenirken hata oluştu: {str(e)}")
    exit()


kategori_sutunlari = [col for col in df.columns if col not in ['Yorum', 'Tarih']]
print(f"Bulunan kategori sayısı: {len(kategori_sutunlari)}")
print(f"Kategoriler: {', '.join(kategori_sutunlari)}")


df['Duygu_Polaritesi'] = 0.0
df['Duygu_Etiketi'] = 'Nötr'

print("🔍 En az bir kategoride 1 olan yorumlar bulunuyor...")
bir_olan_satirlar = df[df[kategori_sutunlari].sum(axis=1) > 0]
print(f"✅ Toplam {len(bir_olan_satirlar)} yorumda en az bir kategoride 1 değeri var.")

print("💭 Duygu analizi yapılıyor...")
analiz_sayisi = 0

for idx, row in bir_olan_satirlar.iterrows():
    try:
        yorum = row['Yorum']
        duygu_etiketi, polarite = analyze_sentiment(yorum)
        
        df.at[idx, 'Duygu_Polaritesi'] = polarite
        df.at[idx, 'Duygu_Etiketi'] = duygu_etiketi
        
        analiz_sayisi += 1
     
        if analiz_sayisi % 100 == 0:
            print(f"   ➤ {analiz_sayisi}/{len(bir_olan_satirlar)} yorum analiz edildi.")
            
    except Exception as e:
        print(f"⚠️ Duygu analizi yapılırken hata oluştu: {str(e)}")
        df.at[idx, 'Duygu_Polaritesi'] = 0
        df.at[idx, 'Duygu_Etiketi'] = "Hata"


try:
    sonuc_dosyasi = "duygu_analizi_sonuclari.xlsx"
    df.to_excel(sonuc_dosyasi, index=False)
    print(f"\n Duygu analizi sonuçları '{sonuc_dosyasi}' dosyasına kaydedildi.")
except Exception as e:
    print(f"Excel dosyası oluşturulurken hata oluştu: {str(e)}")

bir_olan_yorumlar = df[df[kategori_sutunlari].sum(axis=1) > 0]
pozitif_sayisi = (bir_olan_yorumlar['Duygu_Etiketi'] == 'Pozitif').sum()
negatif_sayisi = (bir_olan_yorumlar['Duygu_Etiketi'] == 'Negatif').sum()
notr_sayisi = (bir_olan_yorumlar['Duygu_Etiketi'] == 'Nötr').sum()

print("\n DUYGU ANALİZİ İSTATİSTİKLERİ")
print(f"   Pozitif: {pozitif_sayisi} ({pozitif_sayisi/len(bir_olan_yorumlar)*100:.2f}%)")
print(f"   Negatif: {negatif_sayisi} ({negatif_sayisi/len(bir_olan_yorumlar)*100:.2f}%)")
print(f"   Nötr: {notr_sayisi} ({notr_sayisi/len(bir_olan_yorumlar)*100:.2f}%)")

total_time = time.time() - start_time
print(f"\n Toplam çalışma süresi: {total_time:.2f} saniye")
print("\n Duygu analizi işlemi tamamlandı!") 