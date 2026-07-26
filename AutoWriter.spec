# -*- mode: python ; coding: utf-8 -*-

# collect_all('PySide6') KULLANMA: tum Qt'yi (WebEngine, 3D, Charts...) iceri alir.
# PyInstaller'in PySide6 hook'u zaten sadece import edilen modulleri toplar.
# PySide6.* modullerini tek tek exclude ETME: QtWidgets.pyd'nin bagimli oldugu
# Qt DLL'leri de silinir ve exe "DLL load failed" ile aciliyor gibi yapip cokuyor.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'pydoc', 'doctest', 'sqlite3',
        'lib2to3', 'pdb', 'difflib', 'numpy', 'PIL',
    ],
    noarchive=False,
    optimize=2,
)

# Qt ceviri dosyalari ve gereksiz eklentiler
a.datas = [d for d in a.datas if not d[0].startswith('PySide6/translations')]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Auto Writer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
