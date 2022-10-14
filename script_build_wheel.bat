call .venv\Scripts\activate.bat
python setup.py build_ext --inplace
python setup.py sdist bdist_wheel
pause
