# -*- mode: python -*-
import shutil
import os
from gwhat import __version__

block_cipher = None

added_files = [('C:/Users/jsgosselin/GWHAT/gwhat/ressources/splash.png', 'ressources'),
               ('C:/Users/jsgosselin/GWHAT/gwhat/ressources/WHAT_banner_750px.png', 'ressources'),
               ('C:/Users/jsgosselin/GWHAT/gwhat/ressources/icons_png/*.png', 'ressources/icons_png')
               ]

a = Analysis(['C:\\Users\\jsgosselin\\GWHAT\\gwhat\\mainwindow.py'],
             pathex=['C:\\Python36', 'C:\\Users\\jsgosselin\\GWHAT\\releases'],
             binaries=[],
             datas=added_files ,
             hiddenimports=['h5py.defs', 'h5py.utils', 'h5py.h5ac', 'h5py._proxy', 'scipy.stats'],
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

shutil.copyfile("GNU-GPLv3.pdf", "dist/GNU-GPLv3.pdf")
shutil.copytree("Projects", "dist/Projects")
os.rename('dist', 'gwhat_'+__version__+'_win_amd64')
