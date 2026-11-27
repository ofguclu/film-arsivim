#PENCERE 2

# Her yedeklemede güncelleyin
SURUM_NOTU = """muhtelif değişiklikler

Sayfa başı film sayısının varsayılan olarak 60'tan 10'a çekilmesi ve yalnızca Kompleks Görünüm'de görünen 10, 20, 30, 40, 50, 60 ve 100 seçenekli bir dropdown eklenmesi.
Film arama kutusundaki tüm karakterler silindiğinde Enter'a basmaya gerek kalmadan aramanın/filtrenin otomatik güncellenmesi.
'İzledim' işaretlendiğinde ilgili filme güncel izleme tarihinin kaydedilmesi.
"""

#kaydet ve 30 sn bekle
import time
from google.colab import output

# Colab arayüzüne otomatik kaydetme sinyali gönder ve Drive'a yazılması için 3 saniye bekle
output.eval_js('document.querySelector("colab-toolbar-button#save-button")?.click()')
print("30 sn. bekle.")
time.sleep(30)

#google drive'daki kodu çalışma klasörüme kopyala
import shutil

kaynak_dosya = "/content/drive/MyDrive/Colab Notebooks/Film Arşivim ve İzleme Listesi v7.ipynb"
hedef_klasor = "/content/Film Arşivim ve İzleme Listesi v7.ipynb"

# Dosyayı kopyala (hedefte aynı isimde dosya varsa üzerine yazar)
shutil.copy2(kaynak_dosya, hedef_klasor)
print("Dosya başarıyla kopyalandı.")

#önceki py uzantılı dosyaları sil
import os
import glob

# Silme işleminin yapılacağı klasörün tam yolu
silinecek_klasor_yolu = "/content"

# Klasördeki tüm .py uzantılı dosyaları bul
py_dosyalari = glob.glob(os.path.join(silinecek_klasor_yolu, "Film*.py"))

if not py_dosyalari:
    print("Bu klasörde silinecek .py dosyası bulunamadı.")
else:
    for dosya in py_dosyalari:
        os.remove(dosya)
        print(f"Silindi: {os.path.basename(dosya)}")

print("30 sn. bekle.")
time.sleep(30) #30 sn bekle

#github'a yolla
#import os
import json
#import glob
import subprocess
from google.colab import userdata

# 1. Bilgileriniz
KULLANICI_ADI = "ofguclu"
REPO_ADI = "film-arsivim"
EPOSTA = "ofguclu@gmail.com"

# Kasadan token'ı çek ve olası görünmez boşlukları/satır sonlarını temizle
ham_token = userdata.get('GITHUB_TOKEN')
if not ham_token or not ham_token.strip():
    raise ValueError("HATA: Colab Secrets kasasında 'GITHUB_TOKEN' bulunamadı veya içi boş! Sol menüdeki Anahtar simgesinden kontrol edin.")

TOKEN = ham_token.strip()
tam_adres = f"https://{TOKEN}@github.com/{KULLANICI_ADI}/{REPO_ADI}.git"

# 2. Not defterindeki her pencereyi "dosya_adi_pencere1.py" formatında ayır
ipynb_dosyalari = glob.glob("*.ipynb")
if ipynb_dosyalari:
    dosya_yolu = ipynb_dosyalari[0]
    saf_dosya_adi = os.path.splitext(os.path.basename(dosya_yolu))[0]

    # Eski pencere dosyalarını temizle
    for eski_dosya in glob.glob(f"{saf_dosya_adi}_pencere*.py"):
        os.remove(eski_dosya)

    with open(dosya_yolu, "r", encoding="utf-8") as f:
        not_defteri = json.load(f)

    sayac = 1
    for hucre in not_defteri.get("cells", []):
        if hucre.get("cell_type") == "code":
            kod_satirlari = "".join(hucre.get("source", []))
            if kod_satirlari.strip():
                yeni_dosya_adi = f"{saf_dosya_adi}_pencere{sayac}.py"
                with open(yeni_dosya_adi, "w", encoding="utf-8") as out_f:
                    out_f.write(kod_satirlari)
                sayac += 1

    # Orijinal .ipynb dosyasını da GitKraken'da okunabilir formata çevir
    with open(dosya_yolu, "w", encoding="utf-8") as f:
        json.dump(not_defteri, f, indent=2, ensure_ascii=False)
        f.write("\n")

# 3. Gereksiz sistem klasörlerini hariç tut
with open(".gitignore", "w") as f:
    f.write("sample_data/\n.config/\n.ipynb_checkpoints/\ndrive/\n*.tmp\n")

# 4. Global ayarları sıfırla ve Git deposunu temiz biçimde eşitle
!rm -f ~/.gitconfig
!rm -rf .git
subprocess.run(["git", "config", "--global", "user.email", EPOSTA])
subprocess.run(["git", "config", "--global", "user.name", KULLANICI_ADI])
subprocess.run(["git", "init"])
subprocess.run(["git", "branch", "-M", "main"])
subprocess.run(["git", "remote", "add", "origin", tam_adres])

subprocess.run(["git", "fetch", "--depth=1", "origin", "main"])
subprocess.run(["git", "reset", "--soft", "origin/main"])

# 5. Tüm dosyaları kaydet ve GitHub'a gönder
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", SURUM_NOTU])
sonuc = subprocess.run(["git", "push", "-u", tam_adres, "main"], capture_output=True, text=True)

print("DURUM:", sonuc.stderr if sonuc.stderr else "İşlem başarıyla tamamlandı.")