import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── Paleta ────────────────────────────────────────────────────────────────────
C_AMARILLO  = "#D9EF00"
C_VERDE_OSC = "#00342B"
C_VERDE_MED = "#03664F"
C_CREMA     = "#FFFDEE"

# ── Carga ──────────────────────────────────────────────────────────────────────
df = pd.read_csv("data/matches.csv", parse_dates=["Date"])

# ── Filtros base ───────────────────────────────────────────────────────────────
df = df[df["Date"].dt.year >= 2010].copy()
df = df[df["Rank_1"].notna() & df["Rank_2"].notna()]
df = df[(df["Rank_1"] > 0) & (df["Rank_2"] > 0)]

# ── Pesos por categoría ────────────────────────────────────────────────────────
PESOS = {
    "Grand Slam":    4,
    "Masters":       3,
    "Masters Cup":   3,
    "Masters 1000":  3,
    "ATP500":        2,
    "International Gold": 2,
    "ATP250":        1,
    "International": 1,
}
df["peso"] = df["Series"].map(PESOS).fillna(1)

# ── Identificar ganador/perdedor y sus rankings ────────────────────────────────
mask_p1 = df["Winner"] == df["Player_1"]
df["rank_winner"] = np.where(mask_p1, df["Rank_1"], df["Rank_2"])
df["rank_loser"]  = np.where(mask_p1, df["Rank_2"], df["Rank_1"])

# ── Calcular upset score por partido ──────────────────────────────────────────
# Solo es upset cuando el ganador tiene peor ranking (número mayor)
df["diff"] = df["rank_winner"] - df["rank_loser"]
df["upset_score"] = np.where(df["diff"] > 0, df["diff"] * df["peso"], 0)

# ── Jugadores que alguna vez estuvieron en el top 100 ─────────────────────────
top100_p1 = set(df.loc[df["Rank_1"] <= 100, "Player_1"].unique())
top100_p2 = set(df.loc[df["Rank_2"] <= 100, "Player_2"].unique())
ever_top100 = top100_p1 | top100_p2

# ── Agregar por ganador ────────────────────────────────────────────────────────
stats = (
    df.groupby("Winner")
    .agg(
        total_victorias=("upset_score", "count"),
        upset_wins=("diff", lambda x: (x > 0).sum()),
        total_upset_score=("upset_score", "sum"),
        median_upset_score=("upset_score", "median"),
    )
    .reset_index()
)

stats["avg_upset_score"] = stats["total_upset_score"] / stats["total_victorias"]
stats["upset_rate"]      = stats["upset_wins"] / stats["total_victorias"]

# ── Filtros finales ────────────────────────────────────────────────────────────
stats = stats[stats["Winner"].isin(ever_top100)]
stats = stats[stats["total_victorias"] >= 50]
stats = stats.sort_values("median_upset_score", ascending=False)

# ── Ranking mínimo histórico por jugador ──────────────────────────────────────
rank_min_p1 = df.groupby("Player_1")["Rank_1"].min().rename("rank_min")
rank_min_p2 = df.groupby("Player_2")["Rank_2"].min().rename("rank_min")
rank_min = pd.concat([rank_min_p1, rank_min_p2]).groupby(level=0).min()

stats["rank_min"] = stats["Winner"].map(rank_min).astype(int)

top10 = stats.head(10).sort_values("median_upset_score", ascending=True)

# ── Gráfico ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 12))
fig.patch.set_facecolor(C_CREMA)
ax.set_facecolor(C_CREMA)

bars = ax.barh(
    top10["Winner"],
    top10["median_upset_score"],
    color=C_VERDE_MED,
    edgecolor=C_VERDE_OSC,
    linewidth=0.5,
    height=0.55,
)

# Barra del #1 en amarillo
bars[-1].set_color(C_AMARILLO)
bars[-1].set_edgecolor(C_VERDE_OSC)

# Etiquetas: score + % victorias vs mejor rankeado + mejor ranking
for bar, (_, row) in zip(bars, top10.iterrows()):
    x = bar.get_width()
    label = f"  {x:.0f} pts  |  {row['upset_rate']*100:.0f}% vs mejor rankeado  |  best #{int(row['rank_min'])}"
    ax.text(
        x + 0.5, bar.get_y() + bar.get_height() / 2,
        label,
        va="center", ha="left",
        fontsize=9, color=C_VERDE_OSC,
    )

ax.set_xlim(0, top10["median_upset_score"].max() * 1.55)
ax.set_xlabel("Mediana por partido", color=C_VERDE_OSC, fontsize=10)
ax.set_title(
    "Jugadores mas ilogicos del tenis ATP (2010-2026)",
    color=C_VERDE_OSC, fontsize=16, fontweight="bold", pad=15,
)
ax.tick_params(colors=C_VERDE_OSC, labelsize=11)
ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
ax.grid(axis="x", color=C_VERDE_MED, alpha=0.3, linewidth=0.7)

for spine in ax.spines.values():
    spine.set_edgecolor(C_VERDE_OSC)
    spine.set_linewidth(0.8)

subtitle = (
    "Jugadores que alguna vez estuvieron en el top 100 · min. 50 victorias\n"
    "Score = mediana(diferencia de ranking x peso torneo) · solo victorias vs mejor rankeado"
)
fig.text(0.5, 0.01, subtitle, ha="center", fontsize=8, color=C_VERDE_MED)

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig("graficos/jugador_mas_ilogico.png", dpi=200, bbox_inches="tight")
plt.show()
print("Guardado en graficos/jugador_mas_ilogico.png")

# ── Preview en consola ─────────────────────────────────────────────────────────
print("\nTop 10 por MEDIANA:")
print(top10.sort_values("median_upset_score", ascending=False)[["Winner","median_upset_score","upset_rate","total_victorias","rank_min"]].to_string(index=False))
