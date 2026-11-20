# Auto Writer

Windows sistem tepsisinde çalışan, girilen metni aktif pencereye klavye ile yazıyormuş gibi gönderen bir masaüstü uygulaması.

## Kurulum

```powershell
pip install -r requirements.txt
python main.py
```

## Davranış

- Uygulama başlangıçta sistem tepsisinde çalışır.
- Tray menüsü içinde `Open` ve `Çıkış` seçenekleri vardır.
- `Open` editör penceresini açar.
- `Kapat` editörü gizler, uygulama tray'de çalışmaya devam eder.
- `Çalıştır` editörü gizler, 4 saniyelik geri sayım gösterir ve süre sonunda o an odakta olan alana yazmaya başlar.

## Not

Windows, yönetici olarak açılan uygulamalara normal yetkideki uygulamalardan klavye girdisi göndermeyi engelleyebilir. Hedef uygulama yönetici olarak çalışıyorsa bu uygulamayı da aynı yetki seviyesiyle çalıştırmanız gerekebilir.

## Güncellemeler

Uygulama açılışta GitHub Releases'teki son sürümü kontrol eder. Daha yeni bir sürüm varsa sağ üstte **Güncelle** butonu çıkar. Butona basınca exe indirilir (SHA-256 ile doğrulanır), mevcut exe'nin yerine konur ve uygulama yeni sürümle yeniden açılır. Kaynaktan (`python main.py`) çalışırken buton sadece release sayfasını açar.

### Yeni sürüm yayınlama

1. `app/config.py` içindeki `APP_VERSION` değerini artırın (ör. `1.2.0`).
2. Exe'yi derleyin:
   ```powershell
   .venv\Scripts\python -m PyInstaller AutoWriter.spec --noconfirm --clean
   ```
3. Değişiklikleri commit/push edin, sonra release oluşturun (etiket `v` + sürüm olmalı ve release'e bir `.exe` eklenmeli):
   ```powershell
   Copy-Item "dist\Auto Writer.exe" dist\AutoWriter.exe
   gh release create v1.2.0 dist\AutoWriter.exe --title "v1.2.0" --notes "Değişiklikler..."
   ```
