# -*- mode: python ; coding: utf-8 -*-

# Comando para criar o EXE: python -m PyInstaller main.spec
# Diretório do programa: dist

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
    ],
    hiddenimports=collect_submodules('reportlab.graphics.barcode'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)


pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MainERP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico',
)


coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='MainERP',
)
