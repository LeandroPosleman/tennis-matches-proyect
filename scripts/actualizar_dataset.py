"""
Descarga la versión más reciente del dataset de Kaggle y reemplaza data/matches_atp.csv.

Uso:
    python scripts/actualizar_dataset.py

Requisitos:
    pip install kaggle
    Tener ~/.kaggle/kaggle.json con las credenciales de la API de Kaggle.
"""

import os
import shutil
import zipfile
from pathlib import Path

DATASET_SLUG = "dissfya/atp-tennis-2000-2023daily-pull"
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEST_FILE = DATA_DIR / "matches_atp.csv"
TMP_DIR = DATA_DIR / "_tmp_kaggle"


def descargar():
    import kaggle  # noqa: F401 — valida que kaggle esté instalado y configurado

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Descargando dataset: {DATASET_SLUG} ...")
    from kaggle import KaggleApi
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(DATASET_SLUG, path=str(TMP_DIR), unzip=True)

    # Buscar el CSV descargado
    csvs = list(TMP_DIR.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No se encontró ningún CSV en {TMP_DIR}")
    if len(csvs) > 1:
        print(f"Múltiples CSVs encontrados: {[f.name for f in csvs]}")
        # Tomar el más grande (suele ser el dataset principal)
        csvs.sort(key=lambda f: f.stat().st_size, reverse=True)

    origen = csvs[0]
    print(f"CSV encontrado: {origen.name} ({origen.stat().st_size / 1_000_000:.1f} MB)")

    shutil.move(str(origen), str(DEST_FILE))
    print(f"Dataset actualizado en: {DEST_FILE}")


def limpiar():
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)


if __name__ == "__main__":
    try:
        descargar()
    finally:
        limpiar()
