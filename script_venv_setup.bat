python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install wheel
python -m pip install cython>=0.25.2 numpy==1.21.*
python -m pip install -e ../gwhat
python -m pip install spyder-kernels==2.4.*
pause
