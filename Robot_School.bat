@echo off
:: Lệnh này tự động chuyển hướng về thư mục chứa file này 
:: (Tức là C:\Users\Administrator\Documents\GitHub\robot_school)
cd /d "%~dp0"

echo Dang khoi dong Robot School...
echo --------------------------------

:: Gọi Python từ thư mục .venv nằm ngay bên cạnh
:: Lệnh này sửa lỗi "ModuleNotFoundError: No module named 'kivy'"
".venv\Scripts\python.exe" main.py

:: Giữ màn hình lại để xem nếu có lỗi
echo.
pause