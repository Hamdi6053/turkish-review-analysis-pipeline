import pandas as pd
import os
import glob


# Path to the folder containing the labeled Excel files from the LLM step
klasor_yolu = "kategori_sonuclari"  


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


excel_dosyalari = []
for dosya_ismi in dosya_isimleri:
  
    dosya_yolu = glob.glob(os.path.join(klasor_yolu, f"{dosya_ismi}*.xlsx"))
    if dosya_yolu:
        excel_dosyalari.append(dosya_yolu[0])
    else:
        print(f"Uyarı: '{dosya_ismi}' isimli Excel dosyası bulunamadı.")


tum_veriler = []


for i, dosya in enumerate(excel_dosyalari):
    try:
        df = pd.read_excel(dosya)
        
        
        kategori_ismi = dosya_isimleri[i]
        df['Kaynak'] = kategori_ismi
        
       
        if 'Tarih' not in df.columns or 'Yorum' not in df.columns:
           
            print(f"Uyarı: {dosya} dosyasında beklenen sütunlar bulunamadı.")
            print(f"Mevcut sütunlar: {df.columns.tolist()}")
            continue
            
        print(f"{dosya} başarıyla okundu. Satır sayısı: {len(df)}")
        tum_veriler.append(df)
    except Exception as e:
        print(f"Hata: {dosya} dosyası okunamadı. Hata: {e}")


if tum_veriler:
    birlesik_veri = pd.concat(tum_veriler, ignore_index=True)
    
    
    for kategori in dosya_isimleri:
        birlesik_veri[kategori] = 0
    
   
    for index, row in birlesik_veri.iterrows():
        kaynak = row['Kaynak']
        if kaynak in dosya_isimleri:
            birlesik_veri.at[index, kaynak] = 1
   
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "birlesik_veri.xlsx")
    birlesik_veri.to_excel(output_path, index=False)
    
    print(f"Birleştirme tamamlandı. Toplam satır sayısı: {len(birlesik_veri)}")
    print(f"Sütunlar: {birlesik_veri.columns.tolist()}")
else:
    print("Birleştirilecek veri bulunamadı.")