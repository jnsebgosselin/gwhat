# -*- mode: python -*-
import shutil
import os
from gwhat import __version__

block_cipher = None

added_files = [('../gwhat/ressources/splash.png', 'ressources'),
               ('../gwhat/ressources/WHAT_banner_750px.png', 'ressources'),
               ('../gwhat/ressources/icons_png/*.png', 'ressources/icons_png')
               ]

a = Analysis(['../gwhat/mainwindow.py'],
             pathex=[],
             binaries=[],
             datas=added_files ,
             hiddenimports=['h5py.defs', 'h5py.utils', 'h5py.h5ac', 'h5py._proxy', 'scipy.stats._continuous_distns', 'scipy._lib.messagestream'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['PySide', 'PyQt4'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='gwhat',
          debug=False,
          strip=False,
          upx=True,
          console=True , icon='gwhat.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='GWHAT')

shutil.copyfile("../LICENSE", "dist/LICENSE")
shutil.copytree("Projects", "dist/Projects")
os.rename('dist', 'gwhat_'+__version__+'_win_amd64')
