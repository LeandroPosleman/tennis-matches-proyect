@echo off
cd /d "%~dp0"
python scripts\actualizar_dataset.py >> logs\actualizar_dataset.log 2>&1
