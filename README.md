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
