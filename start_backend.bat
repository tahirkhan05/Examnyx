@echo off
echo ========================================
echo Starting ExamNyx Blockchain Backend
echo ========================================
echo.

cd /d "c:\Users\mdkta\OneDrive\Desktop\datanyx\project\blockchain_part"

echo Stopping any existing Python processes...
taskkill /F /IM python.exe /T 2>nul

echo.
echo Starting blockchain backend server...
echo Server will run on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py

pause
