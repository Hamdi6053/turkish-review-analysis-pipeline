import pandas as pd
import os

# CSV dosyalarının bulunduğu klasör yolu
klasor_yolu = "C:/Users/hamdi/Desktop/CSV Halil Tez"  # Kendi klasör yolunu buraya yaz

# Tüm CSV dosyalarını listele
csv_dosyalari = [f for f in os.listdir(klasor_yolu) if f.endswith('.csv')]

# CSV dosyalarını tek bir DataFrame olarak birleştir
tum_veriler = pd.DataFrame()

for dosya in csv_dosyalari:
    dosya_yolu = os.path.join(klasor_yolu, dosya)
    df = pd.read_csv(dosya_yolu)
    tum_veriler = pd.concat([tum_veriler, df], ignore_index=True)

# Birleştirilen verileri yeni bir CSV dosyasına kaydet
tum_veriler.to_csv("birlesik_yorumlar.csv", index=False, encoding='utf-8-sig')
