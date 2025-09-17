import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, BaggingClassifier, AdaBoostClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import StratifiedKFold
import joblib
import time
from textblob import TextBlob
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Zaman ölçümü başlat
start_time = time.time()

# ✅ Türkçe stop word listesi
turkish_stop_words = [
    've', 'bir', 'bu', 'için', 'de', 'da', 'ne', 'veya', 'ile', 'mi', 'mu', 'mü',
    'ben', 'sen', 'o', 'biz', 'siz', 'onlar', 'ama', 'fakat', 'çünkü', 'gibi',
    'her', 'şey', 'çok', 'az', 'daha', 'en'
]

# 📁 Excel klasörü
# --- CONFIGURATION ---
# Directory containing the labeled Excel files from the LLM labeling step.
excel_folder = "kategori_sonuclari"

# Directories for outputs
output_dir = "outputs"
model_dir = os.path.join(output_dir, "models")
report_dir = os.path.join(output_dir, "reports")

# Create directories if they don't exist
os.makedirs(model_dir, exist_ok=True)
os.makedirs(report_dir, exist_ok=True)
# --- END CONFIGURATION ---

# 📄 Performans sonuçlarını tutacağımız listeler
train_results = []
test_results = []
all_predictions = []  # Tüm tahminleri tutacak liste
all_data = pd.DataFrame()  # Tüm verileri birleştirmek için

# Excel dosyalarını al
excel_files = [f for f in os.listdir(excel_folder) if f.endswith('.xlsx') or f.endswith('.xls')]
print(f"\n📁 Toplam işlenecek dosya sayısı: {len(excel_files)}\n")

# Tüm verileri bir araya toplama
for file_idx, file in enumerate(excel_files):
    print(f"📥 Veri yükleniyor: {file} ({file_idx+1}/{len(excel_files)})")
    df = pd.read_excel(os.path.join(excel_folder, file))
    df.dropna(subset=['Yorum', 'Sonuç'], inplace=True)
    df['Kategori'] = file.split('.')[0]
    all_data = pd.concat([all_data, df])

print(f"\n✅ Toplam veri sayısı: {len(all_data)}")

# Eğitim ve tahmin veri setlerini oluştur
train_data = pd.DataFrame()
predict_data = pd.DataFrame()

for category in all_data['Kategori'].unique():
    category_data = all_data[all_data['Kategori'] == category].copy()
    positives = category_data[category_data['Sonuç'] == 1]
    negatives = category_data[category_data['Sonuç'] == 0]
    
    # Pozitif ve negatif örneklerden 400'er tane al (veya mevcut tüm örnekleri)
    positives_400 = positives.sample(min(400, len(positives)), random_state=42)
    negatives_400 = negatives.sample(min(400, len(negatives)), random_state=42)
    
    # Eğitim setine ekle
    category_train = pd.concat([positives_400, negatives_400])
    train_data = pd.concat([train_data, category_train])
    
    # Kalan verileri tahmin setine ekle
    remaining_positives = positives.drop(positives_400.index)
    remaining_negatives = negatives.drop(negatives_400.index)
    category_predict = pd.concat([remaining_positives, remaining_negatives])
    predict_data = pd.concat([predict_data, category_predict])

print(f"📊 Eğitim veri seti büyüklüğü: {len(train_data)}")
print(f"📊 Tahmin edilecek veri seti büyüklüğü: {len(predict_data)}")

# Eğitim veri setini kaydet
train_data.to_csv("egitim_veri_seti.csv", index=False)
predict_data.to_csv("tahmin_edilecek_veri_seti.csv", index=False)

# Basitleştirilmiş hızlı parametre gridi
simple_param_grid = {
    'rf__n_estimators': [100], 
    'rf__max_depth': [None],
    'svm__C': [1], 
    'svm__kernel': ['linear']
}

# Daha kapsamlı grid - sadece accuracy < 0.80 durumunda kullanılacak
extended_param_grid = {
    'rf__n_estimators': [100, 200], 
    'rf__max_depth': [None, 20],
    'et__n_estimators': [100],
    'gb__n_estimators': [100],
    'ada__n_estimators': [50]
}

# Her kategori için model eğitimi
for category in tqdm(train_data['Kategori'].unique(), desc="Kategori İşleniyor"):
    print(f"\n🔄 İşleniyor: {category}")
    
    # Kategori verilerini al
    category_train = train_data[train_data['Kategori'] == category].copy()
    X = category_train['Yorum']
    y = category_train['Sonuç']
    
    # TF-IDF ile metin özellik çıkarımı
    tfidf = TfidfVectorizer(max_features=1000, stop_words=turkish_stop_words)
    X_tfidf = tfidf.fit_transform(X)
    
    # Veriyi ayırma
    X_train, X_test, y_train, y_test = train_test_split(X_tfidf, y, test_size=0.2, random_state=42, stratify=y)
    
    # SMOTE ile veri dengeleme
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    
    # Dense Transformer - sparse matrisi yoğun matrise dönüştürür
    dense_transformer = FunctionTransformer(lambda x: x.toarray(), accept_sparse=True)
    
    # 11 model oluşturma
    models = [
        ('rf', RandomForestClassifier(random_state=42)),
        ('et', ExtraTreesClassifier(random_state=42)),
        ('bagging', BaggingClassifier(random_state=42)),
        ('lr', LogisticRegression(max_iter=1000, random_state=42)),
        ('knn', KNeighborsClassifier()),
        ('svm', SVC(probability=True, random_state=42)),
        ('dt', DecisionTreeClassifier(random_state=42)),
        ('gnb', make_pipeline(dense_transformer, GaussianNB())),
        ('mnb', make_pipeline(dense_transformer, MultinomialNB())),  # 11. algoritma
        ('gb', GradientBoostingClassifier(random_state=42)),
        ('ada', AdaBoostClassifier(random_state=42))
    ]
    
    # Ensemble model oluşturma
    ensemble = VotingClassifier(estimators=models, voting='soft')
    
    # Hızlı grid search ile model eğitimi
    print("⚙️ Grid Search çalışıyor (basit parametre gridi)...")
    grid_search = GridSearchCV(ensemble, simple_param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=1)
    grid_search.fit(X_train_res, y_train_res)
    
    best_model = grid_search.best_estimator_
    
    # Eğitim seti üzerindeki performans kontrolü
    y_train_pred = best_model.predict(X_train_res)
    train_acc = accuracy_score(y_train_res, y_train_pred)
    
    # Accuracy < 0.80 ise daha kapsamlı grid search çalıştır
    if train_acc < 0.80:
        print(f"⚠️ Uyarı: Eğitim accuracy ({train_acc:.4f}) 0.80'in altında!")
        print("⚙️ Gelişmiş Grid Search çalışıyor...")
        
        grid_search_extended = GridSearchCV(ensemble, extended_param_grid, cv=3, 
                                           scoring='accuracy', n_jobs=-1, verbose=1)
        grid_search_extended.fit(X_train_res, y_train_res)
        best_model = grid_search_extended.best_estimator_
        
        # Tekrar performans kontrolü
        y_train_pred = best_model.predict(X_train_res)
        train_acc = accuracy_score(y_train_res, y_train_pred)
        
        if train_acc < 0.80:
            print(f"⚠️ Hala accuracy yetersiz: {train_acc:.4f}")
    
    # Tüm performans metriklerini hesapla
    train_prec = precision_score(y_train_res, y_train_pred, average='weighted', zero_division=0)
    train_rec = recall_score(y_train_res, y_train_pred, average='weighted', zero_division=0)
    train_f1 = f1_score(y_train_res, y_train_pred, average='weighted', zero_division=0)
    
    # Test seti üzerindeki performans
    y_test_pred = best_model.predict(X_test)
    test_acc = accuracy_score(y_test, y_test_pred)
    test_prec = precision_score(y_test, y_test_pred, average='weighted', zero_division=0)
    test_rec = recall_score(y_test, y_test_pred, average='weighted', zero_division=0)
    test_f1 = f1_score(y_test, y_test_pred, average='weighted', zero_division=0)
    
    # Modeli kaydetme
    model_filename = f"model_{category}.pkl"
    model_path = os.path.join(model_dir, model_filename)
    joblib.dump((best_model, tfidf), model_path)
    print(f"💾 Model kaydedildi: {model_filename}")
    
    # Tahmin edilecek veriler için tahmin yap
    predict_category = predict_data[predict_data['Kategori'] == category].copy()
    if len(predict_category) > 0:
        X_predict = tfidf.transform(predict_category['Yorum'])
        y_predict = best_model.predict(X_predict)
        
        # Tahmin sonuçlarını sakla
        for idx, row in predict_category.iterrows():
            try:
                sentiment = TextBlob(row['Yorum']).sentiment.polarity
                sentiment_label = "Pozitif" if sentiment > 0 else "Negatif" if sentiment < 0 else "Nötr"
            except:
                sentiment = 0
                sentiment_label = "Nötr"
                
            all_predictions.append({
                'Yorum_ID': idx,
                'Tarih': row.get('Tarih', 'Belirtilmemiş'),
                'Yorum': row['Yorum'],
                'Gerçek_Sonuç': row.get('Sonuç', 'Bilinmiyor'),
                'Tahmin': y_predict[idx - predict_category.index[0]],  # Indexi ayarla
                'Kategori': category,
                'Duygu_Polaritesi': sentiment,
                'Duygu': sentiment_label
            })
    
    # Eğitim ve test performansını kaydet
    train_results.append({
        'Kategori': category,
        'Veri_Seti': 'Eğitim',
        'Accuracy': train_acc,
        'Precision': train_prec,
        'Recall': train_rec,
        'F1-Score': train_f1
    })
    
    test_results.append({
        'Kategori': category,
        'Veri_Seti': 'Test',
        'Accuracy': test_acc,
        'Precision': test_prec,
        'Recall': test_rec,
        'F1-Score': test_f1
    })
    
    print(f"✅ Tamamlandı: {category}")
    print(f"   ➤ EĞİTİM SETİ PERFORMANSI:")
    print(f"     ◆ Accuracy:  {train_acc:.4f}")
    print(f"     ◆ Precision: {train_prec:.4f}")
    print(f"     ◆ Recall:    {train_rec:.4f}")
    print(f"     ◆ F1-Score:  {train_f1:.4f}")
    print(f"   ➤ TEST SETİ PERFORMANSI:")
    print(f"     ◆ Accuracy:  {test_acc:.4f}")
    print(f"     ◆ Precision: {test_prec:.4f}")
    print(f"     ◆ Recall:    {test_rec:.4f}")
    print(f"     ◆ F1-Score:  {test_f1:.4f}\n")

# ------- SONUÇLARI EXCEL DOSYALARINA YAZMA -------

# 1. Performans sonuçları
all_results = train_results + test_results
results_df = pd.DataFrame(all_results)
results_df.to_excel(os.path.join(report_dir, "ensemble_model_tum_performanslar.xlsx"), index=False)

# 2. Özet performans tablosu
pivot_df = results_df.pivot_table(index='Kategori', 
                                 columns='Veri_Seti', 
                                 values=['Accuracy', 'Precision', 'Recall', 'F1-Score'],
                                 aggfunc='first')
pivot_df.to_excel(os.path.join(report_dir, "ensemble_model_ozet_performanslar.xlsx"))

# 3. Tüm tahminleri içeren tablo
predictions_df = pd.DataFrame(all_predictions)

# 4. Kategori sütunlarını oluşturma
categories = train_data['Kategori'].unique()
for category in categories:
    predictions_df[category] = 0

# Her kategori için 1/0 değerlerini atama
for idx, row in predictions_df.iterrows():
    if row['Tahmin'] == 1:  # Eğer tahmin 1 ise
        predictions_df.at[idx, row['Kategori']] = 1

# Son formatta tahmin sonuçlarını kaydetme
final_columns = ['Yorum_ID', 'Tarih', 'Yorum', 'Duygu', 'Duygu_Polaritesi'] + list(categories)
predictions_df[final_columns].to_excel(os.path.join(report_dir, "ensemble_tahmin_sonuclari.xlsx"), index=False)

# Sadece 1 atanan yorumlar için duygu analizi sonuçlarını kaydetme
positives_df = predictions_df[predictions_df['Tahmin'] == 1]
positives_df.to_excel(os.path.join(report_dir, "pozitif_tahmin_duygu_analizi.xlsx"), index=False)

total_time = time.time() - start_time
print(f"\n⏱️ Toplam çalışma süresi: {total_time/60:.2f} dakika")
print("\n📊 Tüm sonuçlar Excel dosyalarına kaydedildi:")
print("   ➤ 'egitim_veri_seti.csv' - Eğitim için kullanılan 12.000~ veri seti")
print("   ➤ 'tahmin_edilecek_veri_seti.csv' - Tahmin için kullanılan 63.000~ veri seti")
print("   ➤ 'ensemble_model_tum_performanslar.xlsx' - Tüm performans metrikleri")
print("   ➤ 'ensemble_model_ozet_performanslar.xlsx' - Kategori bazlı özet performans")
print("   ➤ 'ensemble_tahmin_sonuclari.xlsx' - Tüm tahmin sonuçları ve kategori atamaları")
print("   ➤ 'pozitif_tahmin_duygu_analizi.xlsx' - 1 atanan yorumlar için duygu analizi")
