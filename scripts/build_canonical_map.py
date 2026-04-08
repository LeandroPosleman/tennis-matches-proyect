"""
Construye data/player_names_map.csv definitivo combinando:
  1. Duplicados internos ATP (puntuacion/capitalización)
  2. Mismatches ATP vs Sackmann (fuzzy + validacion)

El mapa tiene formato: variant -> canonical
El canonical siempre es el nombre con mas partidos (mas datos).

Ejecutar desde raiz del proyecto.
"""

import pandas as pd
from rapidfuzz import fuzz, process
import re

DATA = "data/matches_challenger_atp.csv"
OUT_MAP  = "data/player_names_map.csv"
OUT_REVIEW = "data/player_names_review.csv"  # casos que necesitan revision manual

print("Cargando datos...")
df = pd.read_csv(DATA, low_memory=False)
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Year"] = df["Date"].dt.year
df = df[(df["Year"] >= 2000) & (df["Year"] <= 2024)]

p1 = df[["Player_1","Rank_1","Year","source"]].rename(columns={"Player_1":"player","Rank_1":"rank"})
p2 = df[["Player_2","Rank_2","Year","source"]].rename(columns={"Player_2":"player","Rank_2":"rank"})
obs = pd.concat([p1, p2], ignore_index=True)
obs["player"] = obs["player"].str.strip()
obs = obs[obs["player"].notna() & (obs["rank"] > 0)]

stats = obs.groupby(["player","source"]).agg(
    best_rank=("rank","min"),
    year_min=("Year","min"),
    year_max=("Year","max"),
    n_matches=("rank","count"),
).reset_index()

def canonical_of_pair(a, b, stats_idx):
    """Retorna (canonical, variant): el canonical es el que tiene más partidos."""
    try:
        na = stats_idx.loc[a, "n_matches"] if a in stats_idx.index else 0
    except:
        na = 0
    try:
        nb = stats_idx.loc[b, "n_matches"] if b in stats_idx.index else 0
    except:
        nb = 0
    if na >= nb:
        return a, b
    return b, a

def normalize(name):
    """Quita puntos, espacios extra, convierte a minuscula."""
    return re.sub(r'[.\s\-]', '', name).lower()

def first_initial(name):
    parts = str(name).strip().split()
    return parts[-1][0].upper() if len(parts) >= 2 and parts[-1] else ""

# ─────────────────────────────────────────────────────────────────────────────
# PARTE 1: Duplicados internos ATP (solo diferencia de puntuacion/capitalización)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== PARTE 1: Duplicados internos ATP ===")

atp_stats = stats[stats["source"] == "atp_original"].copy()
atp_stats["initial"] = atp_stats["player"].apply(first_initial)
atp_stats["norm"] = atp_stats["player"].apply(normalize)
stats_n_idx = atp_stats.set_index("player")["n_matches"]

# Casos donde normalize() produce el mismo string → misma persona sin duda
norm_groups = atp_stats.groupby("norm")["player"].apply(list)
auto_merge_atp = []
for norm_val, names in norm_groups.items():
    if len(names) > 1:
        # Elegir canonical: el que tiene mas partidos
        best = max(names, key=lambda n: stats_n_idx.get(n, 0))
        for variant in names:
            if variant != best:
                auto_merge_atp.append({
                    "variant": variant,
                    "canonical": best,
                    "reason": "normalize_identical",
                    "source_type": "atp_internal",
                })

print(f"Auto-merge por normalizacion identica: {len(auto_merge_atp)}")
for m in auto_merge_atp:
    print(f"  '{m['variant']}' -> '{m['canonical']}'")

# ─────────────────────────────────────────────────────────────────────────────
# PARTE 2: Fuzzy dentro de ATP (apellido similar, misma inicial, misma epoca)
# Revisión manual necesaria
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== PARTE 2: Candidatos fuzzy internos ATP (para revision) ===")

# Hardcoded: casos confirmados manualmente del output anterior
# Formato: (variant, canonical)  <- el canonical es el correcto/mas datos
ATP_MANUAL_CONFIRMED = [
    # Mismo jugador, diferente formato de iniciales
    ("Ferrero J.",      "Ferrero J.C."),    # Juan Carlos Ferrero
    ("Mathieu P.",      "Mathieu P.H."),    # Paul-Henri Mathieu
    ("Lisnard J.",      "Lisnard J.R."),    # Julien-Romain Lisnard
    ("Chela J.",        "Chela J.I."),      # Juan Ignacio Chela
    ("Herbert P.H",     "Herbert P.H."),    # Pierre-Hugues Herbert (sin punto final)
    ("Herbert P-H.",    "Herbert P.H."),    # Pierre-Hugues Herbert (guion en inicial)
    ("Andersen J.",     "Andersen J.F."),   # Jan-Frode Andersen
    ("Scherrer J.",     "Scherrer J.C."),   # Jean-Claude Scherrer
    ("Guzman J.",       "Guzman J.P."),     # Juan Pablo Guzman
    ("Wang Y.",         "Wang Y.T."),       # Wang Yeu-Tzuoo
    ("Lu Y.",           "Lu Y.H."),         # Lu Yen-Hsun
    ("Van D. Merwe I.", "Van Der Merwe I."),# Rik de Voest alternativo / Izak van der Merwe
    ("Dutra Da Silva R.", "Dutra Silva R."),# Rogerio Dutra Silva
    ("Munoz De La Nava D.", "Munoz-De La Nava D."),  # Daniel Munoz-De La Nava
    ("Munoz de La Nava D.", "Munoz-De La Nava D."),
    ("Qureshi A.",      "Qureshi A.U.H."),  # Aisam-Ul-Haq Qureshi
    ("Viola M.",        "Viola Mat."),      # Matteo Viola
    ("Silva F.",        "Silva F.F."),      # Frederico Silva (si son misma epoca)
    ("Aragone JC",      "Aragone J.C."),    # JC Aragone
    ("Aragone J.",      "Aragone J.C."),    # JC Aragone
    ("van Lottum J.",   "Van Lottum J."),   # Johan van Lottum (capitalización)
    ("Sousa J.",        "Souza J."),        # Joao Sousa (spelling alternativo)
    # Kuznetsov Al. (Alex, americano) y Kuznetsov A. (Andrey, ruso) son DISTINTOS -> NO mergear
    # Vacek J. / Vanek J. -> NO, son distintos jugadores
    # Baker B. / Becker B. -> NO, son distintos jugadores
    # Casos de apellidos compuestos con "De/Van/Di" — Sackmann toma ultima palabra como apellido
    ("Minaur A.D.",      "De Minaur A."),  # Alex De Minaur (Sackmann: "Alex De Minaur" -> "Minaur A.D.")
    ("Assche L.V.",      "Van Assche L."), # Luca Van Assche
    ("Scheppingen D.V.", "van Scheppingen D."), # Dick van Scheppingen
    ("Oconnell C.",      "O'Connell C."),  # Chris O'Connell (apostrofe)
    ("Galan D.E.",       "Galan D."),      # Daniel Elahi Galan
    ("Querrey S.",       "Querry S."),     # Sam Querrey (typo en ATP, Querrey es el correcto)
    # Fish A. (Mardy Fish, 2006) != Fils A. (Arthur Fils, 2021+) -> NO mergear
    # Wang Y.T. != Wang Y.J. -> NO mergear (iniciales distintas)
    # Zhang Ze != Zhang Z. (Zhizhen) -> NO mergear
]

manual_atp = []
for variant, canonical in ATP_MANUAL_CONFIRMED:
    if variant != canonical:
        manual_atp.append({
            "variant": variant,
            "canonical": canonical,
            "reason": "manual_confirmed",
            "source_type": "atp_internal",
        })

print(f"Manual confirmados internos ATP: {len(manual_atp)}")

# ─────────────────────────────────────────────────────────────────────────────
# PARTE 3: Mismatches ATP vs Sackmann
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== PARTE 3: Mismatches ATP vs Sackmann ===")

atp_names  = set(stats[stats["source"] == "atp_original"]["player"].str.strip().unique())
sack_names = set(stats[stats["source"] == "sackmann"]["player"].str.strip().unique())
atp_only   = sorted(atp_names - sack_names)
sack_list  = sorted(sack_names)

stats_src_idx = stats.set_index(["player","source"])

def get_stat(player, source, field):
    try:
        return stats_src_idx.loc[(player, source), field]
    except KeyError:
        return -1

# Nombres sackmann que ya tienen match exacto con ATP — no deben usarse como variante
sack_exact_matches = atp_names & sack_names

cross_candidates = []
for atp_name in atp_only:
    results = process.extract(
        atp_name, sack_list,
        scorer=fuzz.token_sort_ratio,
        limit=3,
        score_cutoff=80,
    )
    for sack_name, score, _ in results:
        # Si sack_name ya tiene match exacto con otro nombre ATP, no tocar
        if sack_name in sack_exact_matches:
            continue
        atp_init  = first_initial(atp_name)
        sack_init = first_initial(sack_name)
        if atp_init != sack_init:
            continue

        atp_ymin  = get_stat(atp_name,  "atp_original", "year_min")
        atp_ymax  = get_stat(atp_name,  "atp_original", "year_max")
        sack_ymin = get_stat(sack_name, "sackmann",     "year_min")
        sack_ymax = get_stat(sack_name, "sackmann",     "year_max")

        year_overlap = not (atp_ymax < sack_ymin - 2 or sack_ymax < atp_ymin - 2)

        atp_rank  = get_stat(atp_name,  "atp_original", "best_rank")
        sack_rank = get_stat(sack_name, "sackmann",     "best_rank")
        rank_similar = abs(atp_rank - sack_rank) <= 60 if atp_rank > 0 and sack_rank > 0 else False

        cross_candidates.append({
            "atp_name":   atp_name,
            "sack_name":  sack_name,
            "score":      score,
            "year_overlap": year_overlap,
            "rank_similar": rank_similar,
            "atp_rank":   atp_rank,
            "sack_rank":  sack_rank,
            "atp_years":  f"{atp_ymin}-{atp_ymax}",
            "sack_years": f"{sack_ymin}-{sack_ymax}",
        })

cdf = pd.DataFrame(cross_candidates)
cdf["confidence"] = (cdf["year_overlap"].astype(int) + cdf["rank_similar"].astype(int)) * 10 + cdf["score"] / 100
cdf = cdf.sort_values("confidence", ascending=False).drop_duplicates("atp_name")

# Auto-aprobar: score >= 88 + overlap + rank_similar
auto_cross = cdf[
    (cdf["score"] >= 88) &
    cdf["year_overlap"] &
    cdf["rank_similar"]
].copy()

print(f"Auto-aprobados cross-source: {len(auto_cross)}")

cross_map = []
for _, row in auto_cross.iterrows():
    cross_map.append({
        "variant":     row["sack_name"],
        "canonical":   row["atp_name"],
        "reason":      f"fuzzy_{row['score']:.0f}",
        "source_type": "cross_source",
    })

# Entradas cross-source confirmadas manualmente
# (variant, canonical) — canonical es el nombre correcto/preferido
CROSS_MANUAL_CONFIRMED = [
    # Apellidos compuestos: Sackmann toma ultima palabra como apellido
    ("Minaur A.D.",      "De Minaur A."),       # Alex De Minaur
    ("Assche L.V.",      "Van Assche L."),       # Luca Van Assche
    ("Scheppingen D.V.", "van Scheppingen D."),  # Dick van Scheppingen
    ("Oconnell C.",      "O'Connell C."),        # Chris O'Connell
    # Typos
    ("Querry S.",        "Querrey S."),          # Sam Querrey (typo en ATP)
    # Inicial extra en Sackmann
    ("Galan D.E.",       "Galan D."),            # Daniel Elahi Galan
    ("Hantschk M.",      "Hantschek M."),        # typo
    # Chekhov/Chekov
    ("Chekhov P.",       "Chekov P."),           # Pavel Chekhov
]

for variant, canonical in CROSS_MANUAL_CONFIRMED:
    cross_map.append({
        "variant":     variant,
        "canonical":   canonical,
        "reason":      "manual_confirmed",
        "source_type": "cross_source",
    })

# Para revision: score >= 82 pero no auto-aprobados
review = cdf[
    (cdf["score"] >= 82) &
    ~((cdf["score"] >= 88) & cdf["year_overlap"] & cdf["rank_similar"])
].copy()
review.to_csv(OUT_REVIEW, index=False)
print(f"Para revision manual: {len(review)} pares guardados en {OUT_REVIEW}")

# ─────────────────────────────────────────────────────────────────────────────
# COMBINAR Y GUARDAR MAPA
# ─────────────────────────────────────────────────────────────────────────────
all_mappings = auto_merge_atp + manual_atp + cross_map
map_df = pd.DataFrame(all_mappings).drop_duplicates("variant")
map_df.to_csv(OUT_MAP, index=False)

print(f"\n=== MAPA FINAL ===")
print(f"Total entradas en {OUT_MAP}: {len(map_df)}")
print(f"  - ATP interno (normalización): {sum(1 for m in all_mappings if m['source_type']=='atp_internal' and m['reason']=='normalize_identical')}")
print(f"  - ATP interno (manual):        {sum(1 for m in all_mappings if m['source_type']=='atp_internal' and m['reason']=='manual_confirmed')}")
print(f"  - Cross-source (auto):         {sum(1 for m in all_mappings if m['source_type']=='cross_source')}")

# ─────────────────────────────────────────────────────────────────────────────
# VERIFICACION: cuantos jugadores unicos quedan despues del mapa
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== VERIFICACION ===")
mapping = dict(zip(map_df["variant"], map_df["canonical"]))

all_players = set(obs["player"].unique())
resolved = {mapping.get(p, p) for p in all_players}
print(f"Jugadores antes del mapa: {len(all_players)}")
print(f"Jugadores despues del mapa: {len(resolved)}")
print(f"Reduccion: {len(all_players) - len(resolved)} entradas eliminadas")

print("\nListo.")
