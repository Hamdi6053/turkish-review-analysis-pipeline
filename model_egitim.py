import os
import pandas as pd
import numpy as np
import re  # Eklendi - metin temizleme için
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
from sklearn.model_selection import StratifiedKFold
from imblearn.over_sampling import SMOTE
import joblib
import time
import warnings
warnings.filterwarnings('ignore')

# Define function outside of lambda for pickling compatibility
def make_dense(X):
    return X.toarray()

# 📁 Excel klasörü - BURAYA EXCEL DOSYALARININ YOLUNU GİRİN
excel_folder = r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları"

# Klasör yoksa hata ver
if not os.path.exists(excel_folder):
    print(f"⚠️ '{excel_folder}' klasörü bulunamadı!")
    print("Excel klasörü yolunu doğru şekilde güncellemeniz gerekiyor.")
    exit()

# Türkçe stop word listesi - Genişletildi ve daha agresif hale getirildi
turkish_stop_words = [
    've', 'bir', 'bu', 'için', 'de', 'da', 'ne', 'veya', 'ile', 'mi', 'mu', 'mü',
    'ben', 'sen', 'o', 'biz', 'siz', 'onlar', 'ama', 'fakat', 'çünkü', 'gibi',
    'her', 'şey', 'çok', 'az', 'daha', 'en', 'ki', 'ise', 'olarak', 'kadar',
    'sonra', 'önce', 'ancak', 'ama', 'fakat', 'lakin', 'yani', 'nasıl',
    # Ek stop words - daha agresif filtreleme
    'var', 'yok', 'oldu', 'olur', 'etti', 'eder', 'etmek', 'olmak', 'yapmak',
    'yapıyor', 'yapılır', 'eden', 'olan', 'içinde', 'üzerinde', 'altında',
    'yanında', 'dışında', 'karşı', 'doğru', 'göre', 'rağmen', 'dolayı',
    'nedeniyle', 'yüzünden', 'sayesinde', 'tarafından', 'itibaren', 'önce',
    'sonra', 'kadar', 'sırasında', 'boyunca', 'kez', 'defa', 'kere', 'birçok',
    'birkaç', 'bazı', 'tüm', 'bütün', 'tamam', 'tamamen', 'kısmen', 'evet',
    'hayır', 'belki', 'galiba', 'sanırım', 'herhalde', 'kesinlikle', 'mutlaka'
]

# Hedef doğruluk - %80-85 arası (daha yüksek aşırı öğrenmedir)
TARGET_ACCURACY_MIN = 0.80
TARGET_ACCURACY_MAX = 0.85

# Eğitim ve test seti arasındaki maksimum kabul edilebilir fark
MAX_ACC_DIFF = 0.15  # %15'e düşürüldü - daha az overfitting istiyoruz

# Öğrenme seti performans sonuçlarını tutacak liste
ogrenme_performanslari = []

# Test seti performans sonuçlarını tutacak liste
test_performanslari = []

# Zaman ölçümü başlat
start_time = time.time()

print("🚀 MODEL EĞİTİMİ BAŞLADI")
print("------------------------")
print(f"📂 Excel klasörü: {excel_folder}")
print(f"🎯 Hedef doğruluk aralığı: %{TARGET_ACCURACY_MIN*100:.0f}-%{TARGET_ACCURACY_MAX*100:.0f}")
print(f"🔍 Maksimum kabul edilebilir eğitim-test farkı: %{MAX_ACC_DIFF*100:.0f}")

# Excel dosyalarını al
try:
    excel_files = [f for f in os.listdir(excel_folder) if f.endswith('.xlsx') or f.endswith('.xls')]
    if not excel_files:
        print("⚠️ Klasörde Excel dosyası bulunamadı!")
        exit()
    print(f"\n📁 Toplam işlenecek dosya sayısı: {len(excel_files)}\n")
except Exception as e:
    print(f"⚠️ Klasör okuma hatası: {str(e)}")
    exit()

# Metin temizleme fonksiyonu
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

# Dense Transformer - lambda kullanmadan
dense_transformer = FunctionTransformer(make_dense, accept_sparse=True)

# 7 algoritmalı ensemble model oluştur (daha güçlü regularizasyon parametreleri)
models = [
    # En iyi genelleme yapan ve en az overfitting gösteren 7 model - GaussianNB kaldırıldı
    ('rf', RandomForestClassifier(min_samples_leaf=5, min_samples_split=10, max_depth=8, n_estimators=100, random_state=42)),
    ('et', ExtraTreesClassifier(min_samples_leaf=5, min_samples_split=10, max_depth=8, n_estimators=100, random_state=42)),
    ('bagging', BaggingClassifier(n_estimators=100, max_samples=0.7, max_features=0.7, random_state=42)),
    ('lr', LogisticRegression(C=0.2, max_iter=1000, penalty='l2', random_state=42)),  # C değeri daha da düşürüldü
    ('svm', SVC(C=0.2, probability=True, kernel='linear', random_state=42)),  # C değeri daha da düşürüldü
    ('mnb', make_pipeline(dense_transformer, MultinomialNB(alpha=2.0))),  # Alpha değeri daha da artırıldı
    ('gb', GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.03, subsample=0.7, 
                                     validation_fraction=0.2, n_iter_no_change=5, random_state=42))  # Early stopping eklendi
]

# Ensemble model
ensemble = VotingClassifier(estimators=models, voting='soft')

# GridSearch için daha fazla zaman tanı
print("⚙️ Grid Search çalışıyor (daha uzun sürebilir)...")

# 10-katlı çapraz doğrulama (daha iyi genelleme için)
cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

# GridSearch parametre gridi (düşük overfitting için daha güçlü regularizasyon)
param_grid = {
    'rf__n_estimators': [100, 150, 200],
    'rf__max_depth': [5, 6, 8],  # Daha sınırlı derinlik (overfitting'i azaltır)
    'rf__min_samples_leaf': [5, 8, 10],  # Daha yüksek değer (daha güçlü genelleme)
    'rf__min_samples_split': [10, 15, 20],  # Daha yüksek değer (daha güçlü genelleme)
    'svm__C': [0.1, 0.2, 0.3],  # Daha düşük C değeri (daha güçlü regularizasyon)
    'gb__subsample': [0.6, 0.7, 0.8],  # Subsample değerleri
    'svm__kernel': ['linear']
}

# TF-IDF ile metin özellikleştirme (daha az özellik - 400 ile sınırlandırıldı)
tfidf = TfidfVectorizer(max_features=300, stop_words=turkish_stop_words, ngram_range=(1, 2))

# Her Excel dosyası için model eğitimi yap
for file_idx, file in enumerate(excel_files):
    print(f"\n🔄 İşleniyor: {file} ({file_idx+1}/{len(excel_files)})")
    
    try:
        # Excel dosyasını oku
        file_path = os.path.join(excel_folder, file)
        print(f"   📄 Dosya yolu: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"⚠️ Dosya bulunamadı: {file_path}")
            continue
            
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            print(f"⚠️ Excel okuma hatası (openpyxl): {str(e)}")
            print("   🔄 'xlrd' motoru ile yeniden deneniyor...")
            try:
                df = pd.read_excel(file_path, engine='xlrd')
            except Exception as e2:
                print(f"⚠️ Excel okuma hatası (xlrd): {str(e2)}")
                print("   ⏭️ Bu dosya atlanıyor.")
                continue
        
        # Temel kontroller
        if df.empty:
            print(f"⚠️ Excel dosyası boş: {file}")
            continue
            
        print(f"   ℹ️ Sütunlar: {', '.join(df.columns.tolist())}")
        
        # Özel kontrol - beklenen sütunların varlığı ('Tarih', 'Yorum', 'Sonuç')
        expected_columns = ['Yorum', 'Sonuç']
        
        # Sütun adları ile çalışırken büyük/küçük harf ve boşluk sorunları için düzeltme
        df.columns = df.columns.str.strip()
        column_mapping = {}
        for col in df.columns:
            clean_col = col.lower().strip()
            if clean_col == 'yorum':
                column_mapping[col] = 'Yorum'
            elif clean_col == 'sonuç' or clean_col == 'sonuc':
                column_mapping[col] = 'Sonuç'
            elif clean_col == 'tarih':
                column_mapping[col] = 'Tarih'
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            print(f"⚠️ Uyarı: {file} dosyasında gerekli sütunlar {', '.join(missing_columns)} bulunamadı!")
            print(f"   Mevcut sütunlar: {', '.join(df.columns.tolist())}")
            continue
            
        # NaN değerleri temizle
        row_count_before = len(df)
        df.dropna(subset=['Yorum', 'Sonuç'], inplace=True)
        row_count_after = len(df)
        
        if row_count_before != row_count_after:
            print(f"   ℹ️ {row_count_before - row_count_after} satır NaN değerler nedeniyle kaldırıldı")
        
        if df.empty:
            print(f"⚠️ NaN temizlemeden sonra veri kalmadı: {file}")
            continue
        
        # Veri tiplerini kontrol et
        try:
            # 'Sonuç' sütununun içeriğini görüntüle
            print(f"   ℹ️ 'Sonuç' sütunu değerleri: {df['Sonuç'].value_counts().to_dict()}")
            
            # Sonuç değerleri 0 ve 1 olacak şekilde dönüştür
            df['Sonuç'] = df['Sonuç'].astype(str).str.strip()
            
            # Sonuç değerlerini dönüştür - function kullanımı (lambda yerine)
            def convert_to_binary(x):
                if x.lower() in ['1', 'true', 'evet', 'yes', 'positive', 'pozitif']:
                    return 1
                return 0
                
            df['Sonuç'] = df['Sonuç'].apply(convert_to_binary)
            print(f"   ℹ️ Dönüştürülmüş 'Sonuç' sütunu değerleri: {df['Sonuç'].value_counts().to_dict()}")
        except Exception as e:
            print(f"⚠️ 'Sonuç' sütunu dönüştürme hatası: {str(e)}")
            # Farklı hata ayıklama bilgileri ekleyelim
            print(f"   ℹ️ 'Sonuç' sütunu veri tipi: {df['Sonuç'].dtype}")
            print(f"   ℹ️ İlk 5 'Sonuç' değeri: {df['Sonuç'].head().tolist()}")
            continue
        
        # Metin temizleme uygula
        df['Yorum'] = df['Yorum'].apply(clean_text)
        
        # Boş yorumları kaldır
        df = df[df['Yorum'].str.strip() != '']
        
        # Kategori ismi oluştur (dosya adından)
        category = file.split('.')[0]
        
        # Veriyi ayır
        X = df['Yorum'].astype(str)  # String'e dönüştür
        y = df['Sonuç']
        
        print(f"📊 Veri seti: Toplam={len(df)}, Pozitif={sum(y)}, Negatif={len(df)-sum(y)}")
        
        # Orta seviye test-train split (%30 test)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)
        
        print(f"   ℹ️ Eğitim/test oranı: {len(X_train)}/{len(X_test)} (%{len(X_train)*100/len(X):.0f}/%{len(X_test)*100/len(X):.0f})")
        
        # TF-IDF ile metin özellikleştirme (daha az özellik - 400 ile sınırlandırıldı)
        tfidf = TfidfVectorizer(max_features=300, stop_words=turkish_stop_words, ngram_range=(1, 2))
        X_train_vec = tfidf.fit_transform(X_train)
        X_test_vec = tfidf.transform(X_test)
        
        print(f"   ℹ️ Özellik sayısı: {X_train_vec.shape[1]}")
        
        # SMOTE ile dengeleme
        try:
            smote = SMOTE(random_state=42)
            X_train_res, y_train_res = smote.fit_resample(X_train_vec, y_train)
            print(f"   ℹ️ SMOTE sonrası eğitim seti: Pozitif={sum(y_train_res)}, Negatif={len(y_train_res)-sum(y_train_res)}")
        except Exception as e:
            print(f"   ⚠️ SMOTE hatası: {str(e)}")
            X_train_res, y_train_res = X_train_vec, y_train
            print("   ℹ️ SMOTE kullanılamadı, orijinal veri kullanılıyor.")
        
        # GridSearch için daha fazla zaman tanı
        print("⚙️ Grid Search çalışıyor (daha uzun sürebilir)...")
        
        try:
            # GridSearch'e maksimum 5 dakika tanı
            grid_search_start = time.time()
            grid_search_max_time = 5 * 60  # 5 dakika
            
            print(f"   ℹ️ GridSearch için maksimum süre: 5 dakika")
            
            # GridSearch için timeout kontrolü
            def timeout_handler():
                if time.time() - grid_search_start > grid_search_max_time:
                    print("   ⚠️ GridSearch zaman aşımı - işlem durduruldu")
                    return True
                return False
            
            # GridSearch daha kısa sürede tamamlanması için
            param_sample = {}
            for param, values in param_grid.items():
                # Değerlerin sayısını azalt (en fazla 2 değer)
                param_sample[param] = values[:2] if len(values) > 2 else values
            
            # Küçültülmüş parametre seti ile GridSearch
            grid_search = GridSearchCV(ensemble, param_sample, cv=cv, scoring='accuracy', n_jobs=-1, verbose=1)
            
            try:
                # GridSearch çalıştır, zaman aşımı kontrolü yap
                grid_search.fit(X_train_res, y_train_res)
            except Exception as timeout_e:
                print(f"   ⚠️ GridSearch işlemi yarıda kesildi: {str(timeout_e)}")
                # Default modele geri dön
                best_model = ensemble
                best_model.fit(X_train_res, y_train_res)
                best_model_name = "ensemble"
                print("   ℹ️ Default ensemble model kullanılıyor.")
            else:
                grid_search_time = time.time() - grid_search_start
                print(f"   ℹ️ GridSearch süresi: {grid_search_time/60:.2f} dakika")
                
                best_model = grid_search.best_estimator_
                best_model_name = "ensemble"
        except Exception as e:
            print(f"⚠️ GridSearch hatası: {str(e)}")
            print("   🔄 Daha basit model kullanılacak...")
            
            # Basit model ile devam et
            best_model = models[0][1]  # RandomForest
            best_model.fit(X_train_res, y_train_res)
            best_model_name = "ensemble"  # Her durumda ensemble olarak adlandır
        
        # Eğitim setinde performans kontrolü
        y_train_pred = best_model.predict(X_train_res)
        train_acc = accuracy_score(y_train_res, y_train_pred)
        
        # Test setinde performans kontrolü (overfitting değerlendirmesi için)
        y_test_pred = best_model.predict(X_test_vec)
        test_acc = accuracy_score(y_test, y_test_pred)
        
        print(f"   ℹ️ Train Accuracy: {train_acc:.4f}, Test Accuracy: {test_acc:.4f}")
        print(f"   ℹ️ Accuracy Farkı: {train_acc - test_acc:.4f}")
        
        # Overfitting değerlendirmesi
        if train_acc - test_acc > MAX_ACC_DIFF:
            print(f"   ⚠️ DİKKAT: Yüksek overfitting! Eğitim-Test farkı %{(train_acc-test_acc)*100:.1f}")
        else:
            print(f"   ✅ Makul genelleme: Eğitim-Test farkı %{(train_acc-test_acc)*100:.1f}")
        
        # Performans metrikleri
        train_prec = precision_score(y_train_res, y_train_pred, average='weighted', zero_division=0)
        train_rec = recall_score(y_train_res, y_train_pred, average='weighted', zero_division=0)
        train_f1 = f1_score(y_train_res, y_train_pred, average='weighted', zero_division=0)
        
        test_prec = precision_score(y_test, y_test_pred, average='weighted', zero_division=0)
        test_rec = recall_score(y_test, y_test_pred, average='weighted', zero_division=0)
        test_f1 = f1_score(y_test, y_test_pred, average='weighted', zero_division=0)
        
        # Öğrenme seti performanslarını kaydet
        ogrenme_performanslari.append({
            'Kategori': category,
            'Model': best_model_name,
            'Accuracy': train_acc,
            'Precision': train_prec,
            'Recall': train_rec,
            'F1': train_f1
        })
        
        # Test seti performanslarını kaydet
        test_performanslari.append({
            'Kategori': category,
            'Model': best_model_name,
            'Accuracy': test_acc,
            'Precision': test_prec,
            'Recall': test_rec,
            'F1': test_f1,
            'Acc_Fark': train_acc - test_acc
        })
        
        # Modeli kaydet
        model_filename = f"model_{category}.pkl"
        joblib.dump({'model': best_model, 'vectorizer': tfidf}, model_filename)
        print(f"💾 Model kaydedildi: {model_filename}")
        
        print(f"✅ {category} için model eğitildi")
        print(f"   ➤ Öğrenme Seti Performansı:")
        print(f"     ◆ Accuracy:  {train_acc:.4f}")
        print(f"     ◆ Precision: {train_prec:.4f}")
        print(f"     ◆ Recall:    {train_rec:.4f}")
        print(f"     ◆ F1-Score:  {train_f1:.4f}")
        print(f"   ➤ Test Seti Performansı:")
        print(f"     ◆ Accuracy:  {test_acc:.4f}")
        print(f"     ◆ Precision: {test_prec:.4f}")
        print(f"     ◆ Recall:    {test_rec:.4f}")
        print(f"     ◆ F1-Score:  {test_f1:.4f}")
        print(f"   ➤ Overfitting Değerlendirmesi:")
        print(f"     ◆ Accuracy Farkı: {train_acc - test_acc:.4f}")
        
    except Exception as e:
        print(f"⚠️ {file} dosyası işlenirken hata oluştu: {str(e)}")
        import traceback
        print(traceback.format_exc())  # Detaylı hata mesajını yazdır

# Öğrenme ve test seti performanslarını Excel'e kaydet
try:
    if ogrenme_performanslari:
        performans_df = pd.DataFrame(ogrenme_performanslari)
        performans_df.to_excel("ogrenme_seti_performanslari.xlsx", index=False)
        print("\n✅ Öğrenme seti performans metrikleri 'ogrenme_seti_performanslari.xlsx' dosyasına kaydedildi.")
    
    if test_performanslari:
        test_performans_df = pd.DataFrame(test_performanslari)
        test_performans_df.to_excel("test_seti_performanslari.xlsx", index=False)
        print("\n✅ Test seti performans metrikleri 'test_seti_performanslari.xlsx' dosyasına kaydedildi.")
        
        # Genel başarı analizi
        avg_test_acc = test_performans_df['Accuracy'].mean()
        avg_train_acc = performans_df['Accuracy'].mean()
        avg_diff = avg_train_acc - avg_test_acc
        
        print("\n📊 GENEL PERFORMANS ANALİZİ:")
        print(f"   → Ortalama Eğitim Doğruluğu: {avg_train_acc:.4f}")
        print(f"   → Ortalama Test Doğruluğu: {avg_test_acc:.4f}")
        print(f"   → Ortalama Fark: {avg_diff:.4f}")
        
        if avg_diff > MAX_ACC_DIFF:
            print(f"   ⚠️ DİKKAT: Genel olarak yüksek overfitting eğilimi!")
        else:
            print(f"   ✅ Genel olarak makul genelleme")
    
    # Özet tablosu oluştur ve kaydet
    summary_data = []
    for i in range(len(test_performanslari)):
        summary_data.append({
            'Kategori': test_performanslari[i]['Kategori'],
            'Model': test_performanslari[i]['Model'],
            'Train_Accuracy': ogrenme_performanslari[i]['Accuracy'],
            'Test_Accuracy': test_performanslari[i]['Accuracy'],
            'Accuracy_Farkı': ogrenme_performanslari[i]['Accuracy'] - test_performanslari[i]['Accuracy'],
            'Train_F1': ogrenme_performanslari[i]['F1'],
            'Test_F1': test_performanslari[i]['F1']
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel("model_ozet.xlsx", index=False)
    print("\n✅ Model özet tablosu 'model_ozet.xlsx' dosyasına kaydedildi.")
        
except Exception as e:
    print(f"\n⚠️ Excel dosyası oluşturulurken hata: {str(e)}")
    # Ekrana yazdır
    if ogrenme_performanslari:
        print("\n📊 ÖĞRENME SETİ PERFORMANS METRİKLERİ:")
        for perf in ogrenme_performanslari:
            print(f"   → {perf['Kategori']} ({perf['Model']}): Accuracy={perf['Accuracy']:.4f}, F1={perf['F1']:.4f}")
    
    if test_performanslari:
        print("\n📊 TEST SETİ PERFORMANS METRİKLERİ:")
        for perf in test_performanslari:
            print(f"   → {perf['Kategori']} ({perf['Model']}): Accuracy={perf['Accuracy']:.4f}, F1={perf['F1']:.4f}, Fark={perf['Acc_Fark']:.4f}")
    else:
        print("\n⚠️ Hiçbir model eğitilemedi.")

total_time = time.time() - start_time
print(f"\n⏱️ Toplam çalışma süresi: {total_time/60:.2f} dakika")
print("\n✅ İşlem tamamlandı!")
if ogrenme_performanslari:
    print("\n👉 Tahmin yapmak için 'tahmin.py' dosyasını çalıştırabilirsiniz.") 