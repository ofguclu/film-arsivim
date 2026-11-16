#PENCERE 1

#alttaki satır bu kod penceresinin play'e basılsa yada Tümünü çalıştır dense bile -hata uyarısı vermeden- çalışmasını engelliyor
#repoyu bir sebeple sıfırlamak istersen bu satırı kaldırırsın (sürüm notunu da uygun bri şekilde değiştirirsin)
#bunu çalıştırdoktan sonra GitKraken'de Pull'ın yanında oka basarak Fetch All demen lazım
#sonra da en solda ana branch'e sağ tıklayıp Reset main to this commit / Hard - discard all changes demelisin
%%script false --no-raise-error

#repoyu temizle

import subprocess
from google.colab import userdata

# 1. Bilgileriniz
KULLANICI_ADI = "ofguclu"
REPO_ADI = "film-arsivim"
EPOSTA = "ofguclu@gmail.com"
SURUM_NOTU = "Ilk surum (Seri, Remake ve Tür ile filmler 1:1 ilişkili)"

TOKEN = userdata.get('GITHUB_TOKEN').strip()
tam_adres = f"https://{KULLANICI_ADI}:{TOKEN}@github.com/{KULLANICI_ADI}/{REPO_ADI}.git"

# 2. Gereksiz sistem klasörlerini hariç tut
with open(".gitignore", "w") as f:
    f.write("sample_data/\n.config/\n.ipynb_checkpoints/\ndrive/\n*.tmp\n")

# 3. Mevcut bozuk ayarları temizle ve sıfırdan tek kayıt oluştur
!rm -f ~/.gitconfig
!rm -rf .git
subprocess.run(["git", "init"])
subprocess.run(["git", "config", "user.email", EPOSTA])
subprocess.run(["git", "config", "user.name", KULLANICI_ADI])
subprocess.run(["git", "branch", "-M", "main"])

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", SURUM_NOTU])

# 4. Sistemdeki gizli URL yönlendirmelerini (-c ile) devre dışı bırakarak zorla gönder
sonuc = subprocess.run([
    "git",
    "-c", "credential.helper=",
    "-c", f"url.{tam_adres}.insteadOf=https://github.com{KULLANICI_ADI}/{REPO_ADI}.git",
    "push", "--force", "-u", tam_adres, "main"
], capture_output=True, text=True)

print("DURUM:", sonuc.stderr if sonuc.stderr else "Depo başarıyla sıfırlandı.")
