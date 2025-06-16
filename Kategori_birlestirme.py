import pandas as pd
import os
import glob

# Excel dosyalarının bulunduğu klasör yolu
klasor_yolu = r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları"  # Excel dosyalarınızın bulunduğu klasörü belirtin

# Dosya isimlerinden kategori isimlerini al
dosya_isimleri = [
    "Ürün", 
    "Teslimat", 
    "Sohbet_Desteği", 
    "Sipariş", 
    "Yarışma",
    "Teslimat_Süresi", 
    "Stok", 
    "Ödeme_Seçenekler", 
    "Kullanıcı_Dostu_Arayüz", 
    "İndirim",
    "İade_İptal_Değişim", 
    "Hedonik_Değer", 
    "Güven", 
    "Boykot", 
    "Bilgi_Erişim"
]

# Excel dosyalarının tam yollarını al
excel_dosyalari = []
for dosya_ismi in dosya_isimleri:
    # Excel uzantısı (.xlsx) ile dosya adını ara
    dosya_yolu = glob.glob(os.path.join(klasor_yolu, f"{dosya_ismi}*.xlsx"))
    if dosya_yolu:
        excel_dosyalari.append(dosya_yolu[0])
    else:
        print(f"Uyarı: '{dosya_ismi}' isimli Excel dosyası bulunamadı.")

# Boş bir liste oluştur (tüm DataFrame'leri saklayacak)
tum_veriler = []

# Her Excel dosyasını oku ve listeye ekle
for i, dosya in enumerate(excel_dosyalari):
    try:
        df = pd.read_excel(dosya)
        
        # Hangi kategoriye ait olduğunu belirten bir sütun ekle
        kategori_ismi = dosya_isimleri[i]
        df['Kaynak'] = kategori_ismi
        
        # Veri setinin yapısını kontrol et ve gerekirse düzenle
        if 'Tarih' not in df.columns or 'Yorum' not in df.columns:
            # Mevcut sütunları göster
            print(f"Uyarı: {dosya} dosyasında beklenen sütunlar bulunamadı.")
            print(f"Mevcut sütunlar: {df.columns.tolist()}")
            continue
            
        print(f"{dosya} başarıyla okundu. Satır sayısı: {len(df)}")
        tum_veriler.append(df)
    except Exception as e:
        print(f"Hata: {dosya} dosyası okunamadı. Hata: {e}")

# Tüm DataFrame'leri birleştir
if tum_veriler:
    birlesik_veri = pd.concat(tum_veriler, ignore_index=True)
    
    # Bütün kategorileri sütun olarak ekle ve değerlerini 0 yap
    for kategori in dosya_isimleri:
        birlesik_veri[kategori] = 0
    
    # Kaynak sütunundaki değerlere göre ilgili kategori sütununu 1 yap
    for index, row in birlesik_veri.iterrows():
        kaynak = row['Kaynak']
        if kaynak in dosya_isimleri:
            birlesik_veri.at[index, kaynak] = 1
    
    # Kaynak sütununu sil (isteğe bağlı)
    # birlesik_veri = birlesik_veri.drop('Kaynak', axis=1) 
    
    # Birleştirilmiş veriyi kaydet
    birlesik_veri.to_excel("birlesik_veri.xlsx", index=False)
    
    print(f"Birleştirme tamamlandı. Toplam satır sayısı: {len(birlesik_veri)}")
    print(f"Sütunlar: {birlesik_veri.columns.tolist()}")
else:
    print("Birleştirilecek veri bulunamadı.")