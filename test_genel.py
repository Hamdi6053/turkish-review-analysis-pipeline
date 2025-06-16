import pandas as pd
import os
from prettytable import PrettyTable
import traceback

def analyze_file(file_path):
    """
    Excel veya CSV dosyasını analiz eder ve 1 sayısını, 0 sayısını ve benzersiz yorum sayısını döndürür
    
    Args:
        file_path: Excel veya CSV dosyasının yolu
        
    Returns:
        dict: 1 sayısı, 0 sayısı ve benzersiz yorum sayısını içeren sözlük
    """
    result = {
        "dosya_adi": os.path.basename(file_path),
        "bir_sayisi": 0,
        "sifir_sayisi": 0,
        "benzersiz_yorum": 0
    }
    
    # Dosya yolunu temizle ve düzelt
    file_path = file_path.strip()
    # Windows yollarında ters eğik çizgiyi düzelt
    file_path = file_path.replace('\\', '/')
    
    print(f"Düzeltilmiş dosya yolu: {file_path}")
    
    # Dosyanın varlığını kontrol et
    if not os.path.exists(file_path):
        print(f"HATA: Dosya bulunamadı: {file_path}")
        
        # Alternatif yol dene (r öneki kullanımı)
        alt_path = file_path.replace('/', '\\')
        print(f"Alternatif yol deneniyor: {alt_path}")
        if os.path.exists(alt_path):
            file_path = alt_path
            print(f"Alternatif yol başarılı!")
        else:
            print("Alternatif yol da başarısız oldu.")
            
            # Bir deneme daha yapalım - çift ters çizgi ile
            alt_path2 = file_path.replace('/', '\\\\')
            print(f"Son bir deneme yapılıyor: {alt_path2}")
            if os.path.exists(alt_path2):
                file_path = alt_path2
                print("Son deneme başarılı!")
            else:
                return result
    
    # Dosya uzantısını kontrol et
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext in ['.xlsx', '.xls', '.xlsm']:
            # Excel dosyasını oku
            print(f"Excel dosyası okunuyor: {file_path}")
            
            # engine parametresini belirtmeden dene
            try:
                # r öneki kullanarak oku
                df = pd.read_excel(r"{}".format(file_path))
                print("Excel dosyası başarıyla okundu.")
            except Exception as e1:
                print(f"Standart okuma başarısız: {e1}")
                
                # openpyxl ile dene
                try:
                    df = pd.read_excel(r"{}".format(file_path), engine='openpyxl')
                    print("openpyxl motoru ile okuma başarılı")
                except Exception as e2:
                    print(f"openpyxl ile okuma başarısız: {e2}")
                    
                    # xlrd ile dene (.xls için)
                    try:
                        df = pd.read_excel(r"{}".format(file_path), engine='xlrd')
                        print("xlrd motoru ile okuma başarılı")
                    except Exception as e3:
                        print(f"xlrd ile okuma başarısız: {e3}")
                        print(f"Detaylı hata: {traceback.format_exc()}")
                        return result
        else:
            # CSV dosyası olarak dene
            try:
                # r öneki ile oku
                df = pd.read_csv(r"{}".format(file_path), sep=',', encoding='utf-8-sig')
            except Exception as e:
                print(f"Virgülle okuma başarısız: {e}")
                # Ayırıcıyı otomatik tespit etmeyi dene
                df = pd.read_csv(r"{}".format(file_path), sep=None, engine='python', encoding='utf-8-sig')
    except Exception as e:
        print(f"{file_path} dosyası okunamadı: {e}")
        print(f"Detaylı hata: {traceback.format_exc()}")
        return result
    
    # Sütun adlarını kontrol et
    sonuc_sutunu = None
    for col in df.columns:
        if 'sonuc' in col.lower() or 'sonuç' in col.lower():
            sonuc_sutunu = col
            break
    
    yorum_sutunu = None
    for col in df.columns:
        if 'yorum' in col.lower() or 'comment' in col.lower():
            yorum_sutunu = col
            break
    
    # Sonuç değerlerini say
    if sonuc_sutunu:
        try:
            # Sayısal değerlere dönüştürme (gerekirse)
            df[sonuc_sutunu] = pd.to_numeric(df[sonuc_sutunu], errors='coerce')
            
            # 1 ve 0 sayılarını hesapla
            result["bir_sayisi"] = (df[sonuc_sutunu] == 1).sum()
            result["sifir_sayisi"] = (df[sonuc_sutunu] == 0).sum()
        except Exception as e:
            print(f"Sonuç sütunu işlenirken hata: {e}")
    
    # Benzersiz yorum sayısını hesapla
    if yorum_sutunu:
        result["benzersiz_yorum"] = df[yorum_sutunu].nunique()
    
    return result

def analyze_multiple_files(file_paths):
    """
    Birden fazla Excel veya CSV dosyasını analiz eder ve sonuçları tablo olarak gösterir
    
    Args:
        file_paths: Excel veya CSV dosya yollarını içeren liste
    """
    # Tablo oluştur
    table = PrettyTable()
    table.field_names = ["Dosya Adı", "1 Sayısı", "0 Sayısı", "Benzersiz Yorum Sayısı"]
    
    # Her dosyayı analiz et ve tabloya ekle
    for file_path in file_paths:
        result = analyze_file(file_path)
        table.add_row([
            result["dosya_adi"], 
            result["bir_sayisi"], 
            result["sifir_sayisi"], 
            result["benzersiz_yorum"]
        ])
    
    # Tabloyu göster
    print("\nEXCEL ANALİZ SONUÇLARI:")
    print(table)

# Kullanım örneği:
if __name__ == "__main__":
    print("Excel/CSV Analiz Programı")
    print("-----------------------")
    
    # Gerekli kütüphaneleri kontrol et
    try:
        import pandas as pd
        print(f"Pandas sürümü: {pd.__version__}")
        
        try:
            import openpyxl
            print(f"Openpyxl sürümü: {openpyxl.__version__}")
        except ImportError:
            print("Openpyxl kütüphanesi yüklü değil! Excel dosyaları için gerekli olabilir.")
            print("Yüklemek için: pip install openpyxl")
        
        try:
            import xlrd
            print(f"xlrd sürümü: {xlrd.__version__}")
        except ImportError:
            print("xlrd kütüphanesi yüklü değil! .xls dosyaları için gerekli olabilir.")
            print("Yüklemek için: pip install xlrd")
    except Exception as e:
        print(f"Kütüphane kontrolünde hata: {e}")
    
    # 📂 Dosya yollarını buraya manuel olarak girin
    file_paths = [
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Ürün.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Teslimat.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Sohbet_Desteği.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Sipariş.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Yarışma.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Teslimat_Süresi.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Stok.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Ödeme_Seçenekler.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Kullanıcı_Dostu_Arayüz.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\İndirim.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\İade_İptal_Değişim.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Hedonik_Değer.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Güven.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Boykot.xlsx",
        r"C:\Users\hamdi\Downloads\Exceller_Kategori_Atamaları\Bilgi_Erişim.xlsx",

     
        # Daha fazla dosya ekleyebilirsiniz
    ]
    
    if file_paths:
        print(f"\n{len(file_paths)} dosya analiz edilecek...")
        analyze_multiple_files(file_paths)
    else:
        print("Hiç dosya yolu girilmedi!")
