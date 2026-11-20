# Surum: her yayinda burayi artirin (MAJOR.MINOR.PATCH). Arayuzde gosterilir.
APP_VERSION = "1.2.0"

# Guncellemeler bu deponun GitHub Releases sayfasindan kontrol edilir. Release
# etiketi "v1.2.0" biciminde olmali ve release'e bir .exe dosyasi eklenmeli.
GITHUB_REPO = "coraspirin/AutoWriter"
UPDATE_CHECK_DELAY_MS = 3000

APP_NAME = "Coraspirin Auto Writer"
WINDOW_TITLE = "Coraspirin | Auto Writer"
TRAY_TOOLTIP = "Coraspirin Auto Writer"

WINDOW_MIN_WIDTH = 640
WINDOW_MIN_HEIGHT = 560

FOCUS_POLL_INTERVAL_MS = 250
COUNTDOWN_SECONDS = 4

from dataclasses import dataclass


@dataclass(frozen=True)
class TypingProfile:
    """Yazma modunun zamanlama ayarlari.

    key_hold_seconds: tus bas/birak arasindaki bekleme. RDP bas/birak olaylarini
        ayri paketlerde tasir; tarayici RDP'de sifir aralikla gidenler uzak
        tarafta birlestirilip dusebiliyor.
    line_break_extra_seconds: satir sonlarinda uzak tarafin nefes almasi icin.
    burst_size / burst_pause_seconds: her N karakterde bir kisa mola. Karakterler
        hizli gider, mola sirasinda uzak taraf tamponunu bosaltir. 0 = kapali.
    """

    key: str
    label: str
    cps_max: int
    cps_default: int
    key_hold_seconds: float
    line_break_extra_seconds: float
    burst_size: int
    burst_pause_seconds: float


# Hiz karakter/saniye olarak ifade edilir.
TYPE_CPS_MIN = 5

# Tek yazma profili: Guvenli. Tarayici (HTML5) RDP dahil en guvenilir ayarlar.
# Hizli/Turbo modlari kaldirildi; zamanlama her zaman bu profille yapilir.
SAFE_PROFILE = TypingProfile(
    key="safe",
    label="Güvenli",
    cps_max=40,
    cps_default=25,
    key_hold_seconds=0.012,
    line_break_extra_seconds=0.15,
    # RDPPaste'ten: her 50 karakterde kisa mola; uzak taraf tamponunu bosaltir.
    burst_size=50,
    burst_pause_seconds=0.10,
)
TYPE_CPS_MAX = SAFE_PROFILE.cps_max
TYPE_CPS_DEFAULT = SAFE_PROFILE.cps_default

# Hedef (uzak makine) klavye duzeni. Karakterler scan-code olarak gider ve uzak
# taraf onlari KENDI duzenine gore cevirir; duzenler farkliysa harfler bozulur.
# "auto" = bu bilgisayarin duzeni. Deger: KLID (LoadKeyboardLayout kimligi).
TARGET_LAYOUTS: dict[str, tuple[str, str | None]] = {
    "auto": ("Otomatik (bu bilgisayar)", None),
    "tr_q": ("Türkçe Q", "0000041F"),
    "us": ("İngilizce (US)", "00000409"),
}
TARGET_LAYOUT_DEFAULT = "auto"

# Tab'lari yazmadan once bosluga cevir (IDE'lerde Tab otomatik tamamlama tetikler).
EXPAND_TABS_DEFAULT = False
TAB_WIDTH_CHOICES = (2, 4, 8)
TAB_WIDTH_DEFAULT = 4

# Kod editorlerinin Enter sonrasi ekledigi otomatik girintiyi temizle.
CLEAR_AUTO_INDENT_DEFAULT = True

# Ilerleme bildirimi en fazla bu siklikta UI'ya gonderilir; yuksek hizda her
# karakterde sinyal yollamak UI thread'ini bosuna mesgul eder.
PROGRESS_EMIT_INTERVAL_SECONDS = 0.05

# Durdur icin global kisayol (WM_HOTKEY). Durdur'a fare ile basmak icin uygulama
# penceresine tiklamak gerekir; o an on pencere degisir ve kalan karakterler kendi
# metin kutumuza yazilir. Bu yuzden kisayol sart.
HOTKEY_ID_STOP = 2
VK_F10 = 0x79
HOTKEY_STOP_LABEL = "F10"
