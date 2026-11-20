# Surum: her yayinda burayi artirin (MAJOR.MINOR.PATCH). Arayuzde gosterilir.
APP_VERSION = "1.1.0"

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


# Hiz karakter/saniye olarak ifade edilir; ust sinir moda gore degisir.
TYPE_CPS_MIN = 5

TYPING_PROFILES: dict[str, TypingProfile] = {
    # Eski davranis: tarayici (HTML5) RDP'de en guvenilir.
    "safe": TypingProfile(
        key="safe",
        label="Güvenli",
        cps_max=40,
        cps_default=25,
        key_hold_seconds=0.012,
        line_break_extra_seconds=0.15,
        burst_size=0,
        burst_pause_seconds=0.0,
    ),
    # Normal RDP (mstsc) icin: kisa tus basimi + periyodik mola.
    "fast": TypingProfile(
        key="fast",
        label="Hızlı",
        cps_max=150,
        cps_default=80,
        key_hold_seconds=0.002,
        line_break_extra_seconds=0.04,
        burst_size=100,
        burst_pause_seconds=0.08,
    ),
    # RDPPaste benzeri: bas/birak arasi bekleme yok, sik ama kisa molalar.
    "turbo": TypingProfile(
        key="turbo",
        label="Turbo",
        cps_max=400,
        cps_default=200,
        key_hold_seconds=0.0,
        line_break_extra_seconds=0.015,
        burst_size=200,
        burst_pause_seconds=0.15,
    ),
}
TYPING_PROFILE_DEFAULT = "safe"

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
