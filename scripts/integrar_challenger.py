"""
Integración de datos Challenger (Jeff Sackmann) con el dataset existente.

Genera 3 archivos en data/:
  1. matches_atp.csv          — dataset original (intacto, no se toca)
  2. matches_challenger.csv — datos Sackmann concatenados (formato original, intacto)
  3. matches_challenger_atp.csv   — unión de matches_atp.csv + challenger convertido al mismo formato

Ejecutar desde la raíz del proyecto.
"""

import pandas as pd
import os

YEARS = list(range(2000, 2025))  # 2000–2024 (2025 aún no disponible en Sackmann)
DATA_DIR = "data"

# ─────────────────────────────────────────────────────────────────────────────
# PASO 1: Concatenar los archivos descargados en un solo matches_challenger.csv
#         (formato Sackmann original, intacto)
# ─────────────────────────────────────────────────────────────────────────────
print("Paso 1: Concatenando archivos Sackmann...")
frames = []
for year in YEARS:
    path = os.path.join(DATA_DIR, f"sackmann_chall_{year}.csv")
    df_y = pd.read_csv(path, low_memory=False)
    df_y["source_year"] = year
    frames.append(df_y)
    print(f"  {year}: {len(df_y):>5} filas")

challenger_raw = pd.concat(frames, ignore_index=True)
challenger_raw.to_csv(os.path.join(DATA_DIR, "matches_challenger.csv"), index=False)
print(f"  -> matches_challenger.csv guardado ({len(challenger_raw)} filas)\n")

# ─────────────────────────────────────────────────────────────────────────────
# PASO 2: Convertir datos Sackmann al formato de matches.csv y combinar
# ─────────────────────────────────────────────────────────────────────────────
print("Paso 2: Convirtiendo al formato del proyecto...")

# ── Mappings ──────────────────────────────────────────────────────────────────

LEVEL_MAP = {
    "G": "Grand Slam",
    "M": "Masters 1000",
    "C": "Challenger",
    # 'A' se resuelve por draw_size abajo
}

ROUND_MAP = {
    "F":   "The Final",
    "SF":  "Semifinals",
    "QF":  "Quarterfinals",
    "R16": "4th Round",
    "R32": "3rd Round",
    "R64": "2nd Round",
    "R128":"1st Round",
    "RR":  "Round Robin",
    "Q1":  "Qualifying 1st Round",
    "Q2":  "Qualifying 2nd Round",
    "Q3":  "Qualifying 3rd Round",
    "BR":  "Bronze Match",
}

def map_series(level, draw_size):
    if level in LEVEL_MAP:
        return LEVEL_MAP[level]
    if level == "A":
        # ATP500 suelen tener 48/56 jugadores, ATP250 tienen 28/32
        try:
            ds = int(draw_size)
            return "ATP500" if ds >= 48 else "ATP250"
        except (ValueError, TypeError):
            return "ATP250"
    return level  # fallback

def to_last_initial(full_name):
    """'Jannik Sinner' → 'Sinner J.'   |   'Jo-Wilfried Tsonga' → 'Tsonga J.'"""
    parts = str(full_name).strip().split()
    if len(parts) == 0:
        return str(full_name)
    if len(parts) == 1:
        return parts[0]
    last    = parts[-1]
    initials = ".".join(p[0] for p in parts[:-1] if p) + "."
    return f"{last} {initials}"

def parse_date(tourney_date):
    """'20240101' → '2024-01-01'"""
    d = str(int(tourney_date))
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}"

# ── Transformar ───────────────────────────────────────────────────────────────
df_chall = challenger_raw.copy()

df_chall["Tournament"] = df_chall["tourney_name"]
df_chall["Date"]       = df_chall["tourney_date"].apply(parse_date)
df_chall["Series"]     = df_chall.apply(
    lambda r: map_series(r["tourney_level"], r["draw_size"]), axis=1
)
df_chall["Court"]      = ""          # no disponible en Sackmann
df_chall["Surface"]    = df_chall["surface"]
df_chall["Round"]      = df_chall["round"].map(ROUND_MAP).fillna(df_chall["round"])
df_chall["Best of"]    = df_chall["best_of"]
df_chall["Player_1"]   = df_chall["winner_name"].apply(to_last_initial)
df_chall["Player_2"]   = df_chall["loser_name"].apply(to_last_initial)
df_chall["Winner"]     = df_chall["Player_1"]   # en Sackmann winner siempre va primero
df_chall["Rank_1"]     = pd.to_numeric(df_chall["winner_rank"], errors="coerce").fillna(-1).astype(int)
df_chall["Rank_2"]     = pd.to_numeric(df_chall["loser_rank"],  errors="coerce").fillna(-1).astype(int)
df_chall["Pts_1"]      = pd.to_numeric(df_chall["winner_rank_points"], errors="coerce").fillna(-1).astype(int)
df_chall["Pts_2"]      = pd.to_numeric(df_chall["loser_rank_points"],  errors="coerce").fillna(-1).astype(int)
df_chall["Odd_1"]      = -1.0
df_chall["Odd_2"]      = -1.0
df_chall["Score"]      = df_chall["score"]

COLS = ["Tournament","Date","Series","Court","Surface","Round","Best of",
        "Player_1","Player_2","Winner","Rank_1","Rank_2",
        "Pts_1","Pts_2","Odd_1","Odd_2","Score"]

df_chall_fmt = df_chall[COLS].copy()

# ── Leer dataset original ─────────────────────────────────────────────────────
df_orig = pd.read_csv(os.path.join(DATA_DIR, "matches_atp.csv"), low_memory=False)
df_orig["source"] = "atp_original"
df_chall_fmt["source"] = "sackmann"

# ── Combinar y ordenar ────────────────────────────────────────────────────────
df_combined = pd.concat([df_orig, df_chall_fmt], ignore_index=True)
df_combined["Date"] = pd.to_datetime(df_combined["Date"], errors="coerce")
df_combined = df_combined.sort_values("Date").reset_index(drop=True)
df_combined["Date"] = df_combined["Date"].dt.strftime("%Y-%m-%d")

# ── Aplicar mapa de nombres canónicos ────────────────────────────────────────
map_path = os.path.join(DATA_DIR, "player_names_map.csv")
if os.path.exists(map_path):
    name_map = pd.read_csv(map_path)
    mapping = dict(zip(name_map["variant"].str.strip(), name_map["canonical"].str.strip()))
    def apply_map(name):
        name = str(name).strip()
        return mapping.get(name, name)
    df_combined["Player_1"] = df_combined["Player_1"].apply(apply_map)
    df_combined["Player_2"] = df_combined["Player_2"].apply(apply_map)
    df_combined["Winner"]   = df_combined["Winner"].apply(apply_map)
    print(f"  Mapa de nombres aplicado ({len(mapping)} entradas)")
else:
    print("  AVISO: data/player_names_map.csv no encontrado, nombres sin normalizar")

out_path = os.path.join(DATA_DIR, "matches_challenger_atp.csv")
df_combined.to_csv(out_path, index=False)

print(f"  Filas en matches_atp.csv original:       {len(df_orig):>7}")
print(f"  Filas en matches_challenger.csv:         {len(challenger_raw):>7}")
print(f"  Filas en matches_challenger_atp.csv:     {len(df_combined):>7}")
print(f"\n  -> matches_challenger_atp.csv guardado")

# ── Verificación: Sinner y Fonseca en combined ────────────────────────────────
print("\nVerificación — partidos en matches_challenger_atp.csv:")
for player in ["Sinner J.", "Fonseca J."]:
    mask = (df_combined["Player_1"] == player) | (df_combined["Player_2"] == player)
    sub  = df_combined[mask]
    debut = pd.to_datetime(sub["Date"]).min()
    sub2y = sub[pd.to_datetime(sub["Date"]) <= debut + pd.DateOffset(months=24)]
    print(f"  {player}: {len(sub)} partidos totales | {len(sub2y)} en primeros 2 años")

print("\nListo. Los 3 archivos en data/:")
print("  data/matches_atp.csv             (original intacto)")
print("  data/matches_challenger.csv      (Sackmann, formato original)")
print("  data/matches_challenger_atp.csv  (combinado, formato del proyecto)")
