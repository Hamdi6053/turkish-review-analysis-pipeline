import os
import pandas as pd
import time

# Zaman ölçümü başlat
start_time = time.time()

print("📊 VERİ TOPLAMA İŞLEMİ BAŞLADI")
print("-------------------------------")

# Excel klasörü
excel_folder = r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları"

# Tüm verileri birleştirmek için
all_data = pd.DataFrame()

# Excel dosyalarını al
excel_files = [f for f in os.listdir(excel_folder) if f.endswith('.xlsx') or f.endswith('.xls')]
print(f"\n📁 Toplam işlenecek dosya sayısı: {len(excel_files)}\n")

# Tüm verileri bir araya toplama
for file_idx, file in enumerate(excel_files):
    print(f"📥 Veri yükleniyor: {file} ({file_idx+1}/{len(excel_files)})")
    try:
        df = pd.read_excel(os.path.join(excel_folder, file))
        
        # Gerekli sütunları kontrol et
        if 'Yorum' not in df.columns:
            print(f"   ⚠️ Uyarı: {file} dosyasında 'Yorum' sütunu bulunamadı.")
            continue
            
        if 'Sonuç' not in df.columns:
            print(f"   ⚠️ Uyarı: {file} dosyasında 'Sonuç' sütunu bulunamadı.")
            continue
        
        # Tarih sütunu olup olmadığını kontrol et ve yoksa oluştur
        if 'Tarih' not in df.columns:
            print(f"   ⓘ Bilgi: {file} dosyasında 'Tarih' sütunu bulunamadı. Boş sütun ekleniyor.")
            df['Tarih'] = 'Belirtilmemiş'
        
        # NaN değerleri temizle
        df.dropna(subset=['Yorum', 'Sonuç'], inplace=True)
        
        # Sonuç sütununun sayısal olduğundan emin ol (0 ve 1 değerleri olmalı)
        df['Sonuç'] = df['Sonuç'].astype(int)
        
        # Sonuç değerlerini kontrol et
        if not df['Sonuç'].isin([0, 1]).all():
            print(f"   ⚠️ Uyarı: {file} dosyasında 'Sonuç' sütununda 0 ve 1 dışında değerler var.")
            # Değerleri 0 ve 1'e dönüştür
            df['Sonuç'] = df['Sonuç'].apply(lambda x: 1 if x > 0 else 0)
            print(f"   ⓘ Bilgi: 'Sonuç' değerleri 0 ve 1'e dönüştürüldü.")
        
        df['Kategori'] = file.split('.')[0]
        print(f"   → Dosyadan alınan veri sayısı: {len(df)}")
        all_data = pd.concat([all_data, df])
    except Exception as e:
        print(f"   ⚠️ Hata: {file} dosyası yüklenemedi. Hata: {str(e)}")

print(f"\n✅ Toplam veri sayısı: {len(all_data)}")

# Toplanan verileri kaydet
all_data.to_csv("tum_veriler.csv", index=False)
print(f"💾 Tüm veriler 'tum_veriler.csv' dosyasına kaydedildi.")

# Kategori istatistiklerini göster
print("\n📊 KATEGORİ İSTATİSTİKLERİ:")
for category in all_data['Kategori'].unique():
    category_data = all_data[all_data['Kategori'] == category]
    positives = category_data[category_data['Sonuç'] == 1]
    negatives = category_data[category_data['Sonuç'] == 0]
    print(f"   {category}: Toplam={len(category_data)}, Pozitif={len(positives)}, Negatif={len(negatives)}")

total_time = time.time() - start_time
print(f"\n⏱️ Toplam çalışma süresi: {total_time:.2f} saniye")
print("\n✅ Veri toplama işlemi tamamlandı. 'veri_bolme.py' ile devam edebilirsiniz.") 