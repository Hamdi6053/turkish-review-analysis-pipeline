import pandas as pd
import numpy as np
import joblib
import os
import re
import time
import warnings
warnings.filterwarnings('ignore')

def clean_text(text):
    if not isinstance(text, str):
        return ""
   
    text = text.lower()
   
    text = re.sub(r'\d+', '', text)
  
    text = re.sub(r'[^\w\s]', '', text)
   
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def make_dense(X):
    if hasattr(X, "toarray"):
        return X.toarray()
    return X


start_time = time.time()

print("🚀 TAHMİN İŞLEMİ BAŞLADI")
print("-----------------------")


# --- CONFIGURATION ---
# Define the input file for prediction.
# IMPORTANT: Place your Excel file to be predicted in the 'data/processed_data' directory.
input_dir = os.path.join("data", "processed_data")
tahmin_excel = os.path.join(input_dir, "cleaned_data2.xlsx")
# --- END CONFIGURATION ---  


if not os.path.exists(tahmin_excel):
    print(f"⚠️ HATA: Excel dosyası bulunamadı!")
    print(f"Aranan konum: {tahmin_excel}")
    print("Lütfen dosya yolunu kontrol edin.")
    exit()


model_files = [f for f in os.listdir() if f.startswith("model_") and f.endswith(".pkl")]
if not model_files:
    print("⚠️ Hiç model dosyası bulunamadı. Önce 'model_egitim.py' dosyasını çalıştırın.")
    exit()

print(f"📁 Bulunan model sayısı: {len(model_files)}")


try:
    predict_data = pd.read_excel(tahmin_excel)
    print(f"📥 Tahmin edilecek veri seti yüklendi: {len(predict_data)} örnek")
    
    
    if 'Yorum' not in predict_data.columns:
        print("⚠️ Excel dosyasında 'Yorum' sütunu bulunamadı!")
        exit()
except FileNotFoundError:
    print(f"⚠️ '{tahmin_excel}' dosyası bulunamadı!")
    exit()
except Exception as e:
    print(f"⚠️ Excel dosyası yüklenirken hata oluştu: {str(e)}")
    exit()


print("🧹 Metinler temizleniyor...")
predict_data['Temiz_Yorum'] = predict_data['Yorum'].apply(clean_text)


categories = []
for model_file in model_files:
    category = model_file.replace("model_", "").replace(".pkl", "")
    categories.append(category)
  
    predict_data[category] = 0

print(f"📊 Toplam {len(categories)} kategori için tahmin yapılacak: {', '.join(categories)}")


for model_file in model_files:
    category = model_file.replace("model_", "").replace(".pkl", "")
    print(f"\n🔄 İşleniyor: {category}")
    
    try:
        
        saved_data = joblib.load(model_file)
       
        if isinstance(saved_data, tuple) and len(saved_data) == 2:
            model, vectorizer = saved_data
        elif isinstance(saved_data, dict):
            model = saved_data.get('model')
            vectorizer = saved_data.get('vectorizer')
        else:
            raise ValueError("Beklenmeyen model dosyası formatı. Tuple (model, vectorizer) veya dict {'model','vectorizer'} bekleniyor.")
        
    
        X_predict = vectorizer.transform(predict_data['Temiz_Yorum'])
        
       
        y_predict = model.predict(X_predict)
        

        predict_data[category] = y_predict
        
        
        positive_count = sum(y_predict)
        print(f"   ➤ Toplam: {len(y_predict)}, Pozitif Tahmin: {positive_count} ({positive_count/len(y_predict)*100:.2f}%)")
        
    except Exception as e:
        print(f"⚠️ {category} için tahmin yapılırken hata oluştu: {str(e)}")


predict_data = predict_data.drop(columns=['Temiz_Yorum'])


try:
    # Create an 'outputs' directory if it doesn't exist
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "tahmin_sonuclari.xlsx")
    
    predict_data.to_excel(output_path, index=False)
    print(f"\n💾 Tahmin sonuçları '{output_path}' dosyasına kaydedildi.")
except Exception as e:
    print(f"⚠️ Excel dosyası oluşturulurken hata oluştu: {str(e)}")


total_time = time.time() - start_time
print(f"\n⏱️ Toplam çalışma süresi: {total_time:.2f} saniye")
print("\n✅ Tahmin işlemi tamamlandı!") 