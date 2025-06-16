import pandas as pd

# Excel dosyasını yükle
df = pd.read_excel("tahmin_sonuclari.xlsx")  # Dosya adını güncelleyin

# Sayılmayacak sütunları belirle (Yorum ve Tarih)
exclude_columns = ["Yorum", "Tarih"]  # İhtiyaca göre düzenleyin

# 1/0 içeren kategorileri seç (sayılmayacakları çıkar)
kategori_sutunlari = [col for col in df.columns if col not in exclude_columns]

# Her kategori için rapor oluştur
for kategori in kategori_sutunlari:
    count_1 = df[kategori].sum()  # 1'lerin sayısı
    count_0 = (df[kategori] == 0).sum()  # 0'ların sayısı (NaN'lar dahil değil)
    
    print(f"📌 **{kategori}**")
    print(f"   • Toplam Veri: {len(df)}")
    print(f"   • 1 (Pozitif) Sayısı: {count_1} → %{count_1/len(df)*100:.2f}")
    print(f"   • 0 (Negatif) Sayısı: {count_0} → %{count_0/len(df)*100:.2f}")
    print("─────")