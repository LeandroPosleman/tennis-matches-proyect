"""
Aplica player_names_map.csv al combined dataset.
Agrega columna player_canonical a matches_challenger_atp.csv.
Tambien re-ejecuta el analisis de duracion Top 100 con nombres canonicos.

Ejecutar desde raiz del proyecto.
"""

import pandas as pd

DATA    = "data/matches_challenger_atp.csv"
MAP     = "data/player_names_map.csv"

print("Cargando datos...")
df  = pd.read_csv(DATA, low_memory=False)
nmap = pd.read_csv(MAP)

mapping = dict(zip(nmap["variant"].str.strip(), nmap["canonical"].str.strip()))

def apply_map(name):
    name = str(name).strip()
    return mapping.get(name, name)

print(f"Entradas en el mapa: {len(mapping)}")

df["Player_1"] = df["Player_1"].apply(apply_map)
df["Player_2"] = df["Player_2"].apply(apply_map)
df["Winner"]   = df["Winner"].apply(apply_map)

df.to_csv(DATA, index=False)
print(f"Combined actualizado: {len(df)} filas")

# ─────────────────────────────────────────────────────────────────────────────
# Re-analizar duracion Top 100
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== ANALISIS DURACION TOP 100 (nombres canonicos) ===")

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Year"] = df["Date"].dt.year
df = df[(df["Year"] >= 2000) & (df["Year"] <= 2024)]

p1 = df[["Player_1","Rank_1","Year"]].rename(columns={"Player_1":"player","Rank_1":"rank"})
p2 = df[["Player_2","Rank_2","Year"]].rename(columns={"Player_2":"player","Rank_2":"rank"})
obs = pd.concat([p1, p2], ignore_index=True)
obs = obs[obs["rank"] > 0]

best = obs.groupby(["player","Year"])["rank"].min().reset_index()
top100_yr = best[best["rank"] <= 100].groupby("player")["Year"].nunique()

print(f"Total jugadores Top 100: {len(top100_yr)}")
print(f"Media:   {top100_yr.mean():.2f} anos")
print(f"Mediana: {top100_yr.median():.1f} anos")
print(f"Max: {top100_yr.max()} | Min: {top100_yr.min()}")
print()

solo_1   = (top100_yr == 1).sum()
dos_tres = ((top100_yr >= 2) & (top100_yr <= 3)).sum()
cuatro_9 = ((top100_yr >= 4) & (top100_yr <= 9)).sum()
diez_mas = (top100_yr >= 10).sum()
total    = len(top100_yr)

print("Grupos:")
print(f"  Solo 1 ano:  {solo_1} ({solo_1/total*100:.0f}%)")
print(f"  2-3 anos:    {dos_tres} ({dos_tres/total*100:.0f}%)")
print(f"  4-9 anos:    {cuatro_9} ({cuatro_9/total*100:.0f}%)")
print(f"  10+ anos:    {diez_mas} ({diez_mas/total*100:.0f}%)")

print()
top20 = top100_yr.sort_values(ascending=False).head(20)
print("Top 20 por anos en Top 100:")
for player, yrs in top20.items():
    print(f"  {player:<28} {yrs} anos")
