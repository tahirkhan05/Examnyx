@echo off
echo ========================================
echo Starting ExamNyx Frontend
echo ========================================
echo.

cd /d "c:\Users\mdkta\OneDrive\Desktop\datanyx\project\frontend"

echo.
echo Starting frontend development server...
echo Server will run on http://localhost:8080
echo.
echo Press Ctrl+C to stop the server
echo.

call npm run dev

pause
