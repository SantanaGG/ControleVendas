@echo off
TITLE Sistema Financeiro - Iniciando...
COLOR 0A

echo =================================================
echo      INICIANDO SISTEMA DE GESTAO FINANCEIRA
echo =================================================
echo.
echo [1/3] Verificando localizacao...
cd /d "%~dp0"

echo [2/3] Verificando requisitos...
python -m pip install -r requirements.txt > nul 2>&1

echo [3/3] Abrindo o Navegador...
echo.
echo =================================================
echo   O sistema abrira no seu navegador padrao.
echo   Caso nao abra, acesse: http://localhost:8501
echo =================================================
echo.

python -m streamlit run app.py --server.headless false --server.enableCORS false --server.enableXsrfProtection false

pause