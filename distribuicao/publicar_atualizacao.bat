@echo off
rem Gera o release da versao atual (APP_VERSION em config.py) e coloca em "atualizacoes".
rem A atualizacao e aplicada na proxima vez que o MainERP for aberto.
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 criar_release.py --instalar %*
) else (
    python criar_release.py --instalar %*
)
echo.
pause
