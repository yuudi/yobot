# -*- mode: python ; coding: utf-8 -*-
"""
打包文件说明（一般不建议对 python 项目打包）

pip 安装 `pyinstaller` 后，使用 `pyinstaller main.spec`，对项目打包。
"""

import os
import site

sitepackages = site.getsitepackages()


def sitepackages_location(package_name):
    for sp in sitepackages:
        if os.path.exists(os.path.join(sp, package_name)):
            return sp
    raise RuntimeError(f"{package_name} not found")


block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ("packedfiles", "packedfiles"),
        ("public", "public"),
        (f"{sitepackages_location('opencc')}/opencc/config", "opencc/config"),
        (f"{sitepackages_location('opencc')}/opencc/dictionary", "opencc/dictionary"),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='yobot',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          icon='./logo.ico',
          )
