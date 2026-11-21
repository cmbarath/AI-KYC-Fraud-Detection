@echo off
echo ========================================================
echo   AI-Based Identity Verification & Fraud Detection
echo   Internship AI Project Launcher
echo ========================================================
echo.
echo [1/2] Launching FastAPI Backend Server...
start "FastAPI Backend" cmd /k "python run_backend.py"

echo [2/2] Launching Streamlit Dark Dashboard...
start "Streamlit Frontend" cmd /k "python -m streamlit run frontend/app.py --server.port 8501"

echo.
echo Both servers started!
echo - API Documentation: http://127.0.0.1:8000/docs
echo - Streamlit Dashboard: http://localhost:8501
echo.
pause
