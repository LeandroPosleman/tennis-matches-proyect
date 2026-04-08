"""
Busca duplicados de nombres DENTRO de atp_original.
Casos como "Bautista R." vs "Bautista Agut R." -> mismo jugador.

Estrategia:
  - Mismo first initial
  - Un nombre es sufijo/prefijo del otro, O fuzzy score >= 85
  - Epoch overlap (+/- 2 años)
  - Si hay match: el canonical es el que tiene mas partidos (mas datos)

Output: data/atp_internal_duplicates.csv para revision + auto-aprobados directamente.
"""

import pandas as pd
from rapidfuzz import fuzz

DATA = "data/matches_challenger_atp.csv"
OUT  = "data/atp_internal_duplicates.csv"

print("Cargando datos...")
df = pd.read_csv(DATA, low_memory=False)
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Year"] = df["Date"].dt.year
df = df[(df["Year"] >= 2000) & (df["Year"] <= 2024) & (df["source"] == "atp_original")]

p1 = df[["Player_1","Rank_1","Year"]].rename(columns={"Player_1":"player","Rank_1":"rank"})
p2 = df[["Player_2","Rank_2","Year"]].rename(columns={"Player_2":"player","Rank_2":"rank"})
obs = pd.concat([p1, p2], ignore_index=True)
obs["player"] = obs["player"].str.strip()
obs = obs[obs["player"].notna() & (obs["rank"] > 0)]

stats = obs.groupby("player").agg(
    best_rank=("rank","min"),
    year_min=("Year","min"),
    year_max=("Year","max"),
    n_matches=("rank","count"),
).reset_index()

print(f"Jugadores unicos en atp_original: {len(stats)}")

# Para cada par de jugadores, chequear si son duplicados
def first_initial(name):
    parts = str(name).strip().split()
    return parts[-1][0].upper() if len(parts) >= 2 and parts[-1] else ""

stats["initial"] = stats["player"].apply(first_initial)

candidates = []
players = stats.to_dict("records")

for i, a in enumerate(players):
    for j, b in enumerate(players):
        if j <= i:
            continue
        # Misma inicial
        if a["initial"] != b["initial"] or not a["initial"]:
            continue
        # Epoch overlap
        if a["year_max"] < b["year_min"] - 2 or b["year_max"] < a["year_min"] - 2:
            continue
        # Ranking similar (dentro de 60 puestos)
        if abs(a["best_rank"] - b["best_rank"]) > 60:
            continue

        score = fuzz.token_sort_ratio(a["player"], b["player"])
        if score < 82:
            continue

        # Determinar canonical: el que tiene mas partidos
        if a["n_matches"] >= b["n_matches"]:
            canonical, variant = a["player"], b["player"]
        else:
            canonical, variant = b["player"], a["player"]

        candidates.append({
            "player_a": a["player"],
            "player_b": b["player"],
            "score": score,
            "canonical": canonical,
            "variant": variant,
            "a_best_rank": a["best_rank"],
            "b_best_rank": b["best_rank"],
            "a_years": f"{a['year_min']}-{a['year_max']}",
            "b_years": f"{b['year_min']}-{b['year_max']}",
            "a_matches": a["n_matches"],
            "b_matches": b["n_matches"],
        })

cdf = pd.DataFrame(candidates).sort_values("score", ascending=False)
cdf.to_csv(OUT, index=False)
print(f"Pares candidatos: {len(cdf)} guardados en {OUT}")
print()
print("Top 40 candidatos a duplicado interno en ATP:")
print(cdf[["player_a","player_b","score","a_best_rank","b_best_rank","a_years","b_years","a_matches","b_matches"]].head(40).to_string(index=False))
