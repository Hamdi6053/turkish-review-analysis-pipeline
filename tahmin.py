import pandas as pd
import numpy as np
import joblib
import os
import re
import time
import warnings
warnings.filterwarnings('ignore')

# Metin temizleme fonksiyonu (model_egitim.py ile aynı olmalı)
def clean_text(text):
    if not isinstance(text, str):
        return ""
    # Küçük harfe dönüştür
    text = text.lower()
    # Rakamları kaldır
    text = re.sub(r'\d+', '', text)
    # Özel karakterleri kaldır
    text = re.sub(r'[^\w\s]', '', text)
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def make_dense(X):
    if hasattr(X, "toarray"):
        return X.toarray()
    return X

# Zaman ölçümü başlat
start_time = time.time()

print("🚀 TAHMİN İŞLEMİ BAŞLADI")
print("-----------------------")

# TAHMİN YAPILACAK EXCEL DOSYASI - BURAYI DEĞİŞTİRİN
tahmin_excel = r"C:\Users\hamdi\Downloads\cleaned_data2.xlsx"  # Tahmin yapılacak excel dosyası

# Önce dosyanın varlığını kontrol et
if not os.path.exists(tahmin_excel):
    print(f"⚠️ HATA: Excel dosyası bulunamadı!")
    print(f"Aranan konum: {tahmin_excel}")
    print("Lütfen dosya yolunu kontrol edin.")
    exit()

# Model dosyalarını kontrol et
model_files = [f for f in os.listdir() if f.startswith("model_") and f.endswith(".pkl")]
if not model_files:
    print("⚠️ Hiç model dosyası bulunamadı. Önce 'model_egitim.py' dosyasını çalıştırın.")
    exit()

print(f"📁 Bulunan model sayısı: {len(model_files)}")

# Tahmin yapılacak veriyi yükle
try:
    predict_data = pd.read_excel(tahmin_excel)
    print(f"📥 Tahmin edilecek veri seti yüklendi: {len(predict_data)} örnek")
    
    # Yorum sütununu kontrol et
    if 'Yorum' not in predict_data.columns:
        print("⚠️ Excel dosyasında 'Yorum' sütunu bulunamadı!")
        exit()
except FileNotFoundError:
    print(f"⚠️ '{tahmin_excel}' dosyası bulunamadı!")
    exit()
except Exception as e:
    print(f"⚠️ Excel dosyası yüklenirken hata oluştu: {str(e)}")
    exit()

# Metinleri temizle
print("🧹 Metinler temizleniyor...")
predict_data['Temiz_Yorum'] = predict_data['Yorum'].apply(clean_text)

# Kategorileri hazırla
categories = []
for model_file in model_files:
    category = model_file.replace("model_", "").replace(".pkl", "")
    categories.append(category)
    # Sonuç sütununu oluştur (varsayılan 0)
    predict_data[category] = 0

print(f"📊 Toplam {len(categories)} kategori için tahmin yapılacak: {', '.join(categories)}")

# Her model ile tahmin yap
for model_file in model_files:
    category = model_file.replace("model_", "").replace(".pkl", "")
    print(f"\n🔄 İşleniyor: {category}")
    
    try:
        # Model ve vektörleyiciyi yükle
        saved_data = joblib.load(model_file)
        model = saved_data['model']
        vectorizer = saved_data['vectorizer']
        
        # Yorumları vektörleştir - temizlenmiş yorumları kullan
        X_predict = vectorizer.transform(predict_data['Temiz_Yorum'])
        
        # Tahmin yap
        y_predict = model.predict(X_predict)
        
        # Sonuçları kaydet
        predict_data[category] = y_predict
        
        # İstatistikleri göster
        positive_count = sum(y_predict)
        print(f"   ➤ Toplam: {len(y_predict)}, Pozitif Tahmin: {positive_count} ({positive_count/len(y_predict)*100:.2f}%)")
        
    except Exception as e:
        print(f"⚠️ {category} için tahmin yapılırken hata oluştu: {str(e)}")

# Temiz yorum sütununu çıkar
predict_data = predict_data.drop(columns=['Temiz_Yorum'])

# Sonuçları kaydet
try:
    predict_data.to_excel("tahmin_sonuclari.xlsx", index=False)
    print("\n💾 Tahmin sonuçları 'tahmin_sonuclari.xlsx' dosyasına kaydedildi.")
except Exception as e:
    print(f"⚠️ Excel dosyası oluşturulurken hata oluştu: {str(e)}")

# Toplam süreyi hesapla
total_time = time.time() - start_time
print(f"\n⏱️ Toplam çalışma süresi: {total_time:.2f} saniye")
print("\n✅ Tahmin işlemi tamamlandı!") 