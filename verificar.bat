@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"

echo Verificando estilo com Ruff...
%PYTHON% -m ruff check .
if errorlevel 1 goto falha

echo Executando testes com pytest...
%PYTHON% -m pytest
if errorlevel 1 goto falha

echo.
echo Verificacoes concluidas com sucesso.
exit /b 0

:falha
set "CODIGO_SAIDA=%ERRORLEVEL%"
echo.
echo Verificacao falhou. Release cancelado.
exit /b %CODIGO_SAIDA%
