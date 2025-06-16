import pandas as pd
import time

# Zaman ölçümü başlat
start_time = time.time()

print("📊 VERİ BÖLME İŞLEMİ BAŞLADI")
print("----------------------------")

# Toplanan verileri yükle
try:
    all_data = pd.read_csv("tum_veriler.csv")
    print(f"📥 Toplam veri sayısı: {len(all_data)}")
except FileNotFoundError:
    print("⚠️ 'tum_veriler.csv' dosyası bulunamadı. Önce 'veri_toplama.py' dosyasını çalıştırın.")
    exit()

# Eğitim ve tahmin veri setlerini oluştur
train_data = pd.DataFrame()
predict_data = pd.DataFrame()

# Her kategori için 400 pozitif, 400 negatif örnek seç
for category in all_data['Kategori'].unique():
    print(f"\n🔄 İşleniyor: {category}")
    category_data = all_data[all_data['Kategori'] == category].copy()
    
    # Pozitif ve negatif örnekleri ayır
    positives = category_data[category_data['Sonuç'] == 1]
    negatives = category_data[category_data['Sonuç'] == 0]
    
    print(f"   → Toplam veri: {len(category_data)}, Pozitif: {len(positives)}, Negatif: {len(negatives)}")
    
    # Pozitif ve negatif örneklerden 400'er tane al (veya mevcut tüm örnekleri)
    max_positives = min(400, len(positives))
    max_negatives = min(400, len(negatives))
    
    positives_400 = positives.sample(max_positives, random_state=42)
    negatives_400 = negatives.sample(max_negatives, random_state=42)
    
    print(f"   → Seçilen eğitim verisi: Pozitif: {len(positives_400)}, Negatif: {len(negatives_400)}")
    
    # Eğitim setine ekle
    category_train = pd.concat([positives_400, negatives_400])
    train_data = pd.concat([train_data, category_train])
    
    # Kalan verileri tahmin setine ekle
    remaining_positives = positives.drop(positives_400.index)
    remaining_negatives = negatives.drop(negatives_400.index)
    category_predict = pd.concat([remaining_positives, remaining_negatives])
    
    print(f"   → Kalan tahmin verisi: {len(category_predict)}")
    predict_data = pd.concat([predict_data, category_predict])

print(f"\n📊 Eğitim veri seti büyüklüğü: {len(train_data)}")
print(f"📊 Tahmin edilecek veri seti büyüklüğü: {len(predict_data)}")

# Eğitim ve tahmin veri setlerini kaydet
train_data.to_csv("egitim_veri_seti.csv", index=False)
predict_data.to_csv("tahmin_edilecek_veri_seti.csv", index=False)

print(f"💾 Eğitim veri seti 'egitim_veri_seti.csv' dosyasına kaydedildi.")
print(f"💾 Tahmin veri seti 'tahmin_edilecek_veri_seti.csv' dosyasına kaydedildi.")

# Kategori bazında eğitim seti istatistikleri
print("\n📊 EĞİTİM SETİ KATEGORİ İSTATİSTİKLERİ:")
for category in train_data['Kategori'].unique():
    cat_train = train_data[train_data['Kategori'] == category]
    pos_train = cat_train[cat_train['Sonuç'] == 1]
    neg_train = cat_train[cat_train['Sonuç'] == 0]
    print(f"   {category}: Toplam={len(cat_train)}, Pozitif={len(pos_train)}, Negatif={len(neg_train)}")

total_time = time.time() - start_time
print(f"\n⏱️ Toplam çalışma süresi: {total_time:.2f} saniye")
print("\n✅ Veri bölme işlemi tamamlandı. 'model_egitim.py' ile devam edebilirsiniz.") 