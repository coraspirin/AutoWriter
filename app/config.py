APP_NAME = "Coraspirin Auto Writer"
WINDOW_TITLE = "Coraspirin | Auto Writer"
TRAY_TOOLTIP = "Coraspirin Auto Writer"

WINDOW_MIN_WIDTH = 640
WINDOW_MIN_HEIGHT = 560

FOCUS_POLL_INTERVAL_MS = 250
COUNTDOWN_SECONDS = 4

# Hiz karakter/saniye olarak ifade edilir. Ust sinir 40; daha hizlisi hedefte
# kayba yol acabildigi icin acilmiyor.
TYPE_CPS_MIN = 5
TYPE_CPS_MAX = 40
TYPE_CPS_DEFAULT = 25

# Tus bas/birak arasindaki bekleme. RDP bas/birak olaylarini ayri paketlerde
# tasir; sifir aralikla gidenler uzak tarafta birlestirilip dusebiliyor.
KEY_HOLD_SECONDS = 0.012

# Satir sonlarinda uzak tarafin nefes almasi icin ek gecikme.
LINE_BREAK_EXTRA_SECONDS = 0.15

# Durdur icin global kisayol (WM_HOTKEY). Durdur'a fare ile basmak icin uygulama
# penceresine tiklamak gerekir; o an on pencere degisir ve kalan karakterler kendi
# metin kutumuza yazilir. Bu yuzden kisayol sart.
HOTKEY_ID_STOP = 2
VK_F10 = 0x79
HOTKEY_STOP_LABEL = "F10"
