"""
Evolución del ranking ATP — Sinner vs Fonseca (primeros 2 años)
Fuente: data/matches_combined.csv  |  Ejecutar desde la raíz del proyecto.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np

# ── Paleta ───────────────────────────────────────────────────────────────────
C_AMARILLO  = "#D9EF00"
C_VERDE_OSC = "#00342B"
C_VERDE_MED = "#03664F"
C_CREMA     = "#FFFDEE"

# ── Datos ────────────────────────────────────────────────────────────────────
df = pd.read_csv("data/matches_combined.csv", low_memory=False)
df["Date"] = pd.to_datetime(df["Date"])

def get_ranking_series(player_name, months=24):
    """
    Devuelve un DataFrame con un punto por torneo:
    months_since_debut, ranking, tournament, series, won_title.
    Debut = primer partido a nivel Challenger o superior.
    """
    mask = (df["Player_1"] == player_name) | (df["Player_2"] == player_name)
    sub = df[mask].copy().sort_values("Date").reset_index(drop=True)
    # Debut desde el primer Challenger (no ITF ni previos)
    chall_mask = sub["Series"] == "Challenger"
    debut = sub[chall_mask].iloc[0]["Date"]
    cutoff = debut + pd.DateOffset(months=months)
    sub = sub[(sub["Date"] >= debut) & (sub["Date"] <= cutoff)].copy()

    sub["my_rank"] = sub.apply(
        lambda r: r["Rank_1"] if r["Player_1"] == player_name else r["Rank_2"], axis=1
    )
    sub["won"] = sub["Winner"] == player_name
    sub["months"] = (sub["Date"] - debut).dt.days / 30.44

    # Un punto por torneo: tomar la última fila (= partido más profundo jugado)
    last_per_tourn = (
        sub.sort_values(["Tournament", "Date", "Round"])
        .groupby("Tournament", sort=False)
        .last()
        .reset_index()
        .sort_values("months")
    )

    # Título = ganó "The Final"
    titles = sub[(sub["Round"] == "The Final") & sub["won"]][["Tournament"]].drop_duplicates()
    last_per_tourn["is_title"] = last_per_tourn["Tournament"].isin(titles["Tournament"].values)

    return last_per_tourn, debut

sinner_data,  s_debut = get_ranking_series("Sinner J.")
fonseca_data, f_debut = get_ranking_series("Fonseca J.")

# ── Figura ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 8))
fig.patch.set_facecolor(C_CREMA)
ax.set_facecolor(C_CREMA)

# ── Líneas principales ────────────────────────────────────────────────────────
for data, color, label, marker, zorder in [
    (sinner_data,  C_AMARILLO,  "Sinner  (feb 2019 – feb 2021)",  "o", 4),
    (fonseca_data, C_VERDE_MED, "Fonseca (feb 2023 – feb 2025)", "s", 3),
]:
    ax.plot(
        data["months"], data["my_rank"],
        color=color, linewidth=2.4, zorder=zorder,
        solid_capstyle="round", solid_joinstyle="round",
    )
    # Puntos: distinguir títulos
    normal = data[~data["is_title"]]
    titulo = data[ data["is_title"]]

    ax.scatter(normal["months"], normal["my_rank"],
               color=color, s=40, zorder=zorder + 1,
               edgecolors=C_VERDE_OSC, linewidths=0.5)
    ax.scatter(titulo["months"], titulo["my_rank"],
               color=color, s=130, zorder=zorder + 2, marker="*",
               edgecolors=C_VERDE_OSC, linewidths=0.6)

    ax.fill_between(data["months"], data["my_rank"], 900,
                    alpha=0.07, color=color, zorder=1)

# ── Helper de anotación ───────────────────────────────────────────────────────
def hito(ax, m, rank, text, color, text_xy, arrowstyle="->"):
    """
    Dibuja texto en text_xy con flecha apuntando a (m, rank).
    text_xy = (tx, ty) en coordenadas de datos.
    La flecha NO pasa por los puntos de la línea.
    """
    ax.annotate(
        text,
        xy=(m, rank),
        xytext=text_xy,
        xycoords="data", textcoords="data",
        fontsize=8.2, color=color, fontweight="bold",
        ha="center", va="center",
        arrowprops=dict(
            arrowstyle=arrowstyle,
            color=color,
            lw=1.2,
            shrinkA=6,    # espacio entre texto y flecha
            shrinkB=5,    # espacio entre flecha y punto
        ),
        bbox=dict(
            boxstyle="round,pad=0.35",
            facecolor=C_CREMA,
            edgecolor=color,
            linewidth=1.1,
            alpha=0.92,
        ),
        zorder=10,
    )

# ── Hitos Sinner ─────────────────────────────────────────────────────────────
# 1er título Challenger: Bergamo CH
s_bergamo = sinner_data[sinner_data["Tournament"] == "Bergamo CH"].iloc[0]
hito(ax, s_bergamo["months"], s_bergamo["my_rank"],
     "1er título CH\nBergamo #546",
     C_AMARILLO, text_xy=(3.5, 380))

# 1er título CH en EEUU: Lexington CH
s_lex = sinner_data[sinner_data["Tournament"] == "Lexington CH"].iloc[0]
hito(ax, s_lex["months"], s_lex["my_rank"],
     "Lexington CH\n#194",
     C_AMARILLO, text_xy=(7.5, 280))

# Ortisei CH (3er CH, sub-100 por primera vez)
s_orti = sinner_data[sinner_data["Tournament"] == "Ortisei CH"].iloc[0]
hito(ax, s_orti["months"], s_orti["my_rank"],
     "Ortisei CH\n#96",
     C_AMARILLO, text_xy=(11.2, 200))

# Roland Garros QF 2020
s_rg = sinner_data[sinner_data["Tournament"] == "French Open"].iloc[0]
hito(ax, s_rg["months"], s_rg["my_rank"],
     "Roland Garros\nQF  #75",
     C_AMARILLO, text_xy=(14.0, 38))

# Sofia Open: 1er título ATP
s_sofia = sinner_data[sinner_data["Tournament"] == "Sofia Open"].iloc[0]
hito(ax, s_sofia["months"], s_sofia["my_rank"],
     "1er título ATP\nSofia Open  #44",
     C_AMARILLO, text_xy=(17.5, 20))

# Great Ocean Road: 2do título ATP
s_gor = sinner_data[sinner_data["Tournament"] == "Great Ocean Road Open"].iloc[0]
hito(ax, s_gor["months"], s_gor["my_rank"],
     "2do título ATP\nGreat Ocean Road  #36",
     C_AMARILLO, text_xy=(21.0, 8))

# ── Hitos Fonseca ─────────────────────────────────────────────────────────────
# Lexington CH: 1er título Challenger
f_lex = fonseca_data[fonseca_data["Tournament"] == "Lexington CH"].iloc[0]
hito(ax, f_lex["months"], f_lex["my_rank"],
     "1er título CH\nLexington  #214",
     C_VERDE_MED, text_xy=(12.5, 370))

# Australian Open 2025: 2R (venció Rublev #9)
f_ao = fonseca_data[fonseca_data["Tournament"] == "Australian Open"].iloc[0]
hito(ax, f_ao["months"], f_ao["my_rank"],
     "AO — vence Rublev #9\n2da ronda  #112",
     C_VERDE_MED, text_xy=(17.5, 270))

# Argentina Open: 1er título ATP
f_arg = fonseca_data[fonseca_data["Tournament"] == "Argentina Open"].iloc[0]
hito(ax, f_arg["months"], f_arg["my_rank"],
     "1er título ATP\nArgentina Open  #99",
     C_VERDE_MED, text_xy=(19.0, 420))

# Miami Open: Masters 1000 3R, ranking #60
f_miami = fonseca_data[fonseca_data["Tournament"] == "Miami Open"].iloc[0]
hito(ax, f_miami["months"], f_miami["my_rank"],
     "Miami Open\n3ra ronda  #60",
     C_VERDE_MED, text_xy=(21.0, 320))

# ── Ejes y estilo ─────────────────────────────────────────────────────────────
ax.invert_yaxis()
ax.set_xlim(-0.5, 25.5)
ax.set_ylim(920, -10)

ax.spines[["top", "right"]].set_visible(False)
ax.spines["bottom"].set_color(C_VERDE_MED)
ax.spines["left"].set_color(C_VERDE_MED)
ax.tick_params(colors=C_VERDE_OSC)
ax.grid(color=C_VERDE_MED, alpha=0.18, linestyle="--", zorder=0)
ax.set_axisbelow(True)

# Eje X: cada 3 meses con etiqueta
ax.set_xticks(range(0, 25, 3))
ax.set_xticklabels([f"M{m}" for m in range(0, 25, 3)], fontsize=9, color=C_VERDE_OSC)
ax.set_xlabel("Meses desde el debut ATP / Challenger", fontsize=11, color=C_VERDE_OSC, labelpad=8)

# Eje Y: ranking formateado
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"#{int(x)}"))
ax.set_ylabel("Ranking ATP  ↑ mejor", fontsize=11, color=C_VERDE_OSC, labelpad=8)

# Líneas de referencia horizontales
for rank, label in [(100, "Top 100"), (50, "Top 50"), (200, "Top 200")]:
    ax.axhline(rank, color=C_VERDE_MED, alpha=0.35, linewidth=0.9, linestyle=":")
    ax.text(25.3, rank, label, fontsize=7.5, color=C_VERDE_MED, va="center")

# ── Leyenda ───────────────────────────────────────────────────────────────────
star_s = ax.scatter([], [], color=C_AMARILLO, s=130, marker="*",
                    edgecolors=C_VERDE_OSC, linewidths=0.6, label="Título (Sinner)")
dot_s  = ax.scatter([], [], color=C_AMARILLO, s=40,
                    edgecolors=C_VERDE_OSC, linewidths=0.5, label="Partido (Sinner)")
star_f = ax.scatter([], [], color=C_VERDE_MED, s=130, marker="*",
                    edgecolors=C_VERDE_OSC, linewidths=0.6, label="Título (Fonseca)")
dot_f  = ax.scatter([], [], color=C_VERDE_MED, s=40,
                    edgecolors=C_VERDE_OSC, linewidths=0.5, label="Partido (Fonseca)")
line_s = mpatches.Patch(color=C_AMARILLO,  label="Sinner  (feb 2019 – feb 2021)  #546 → #32")
line_f = mpatches.Patch(color=C_VERDE_MED, label="Fonseca (abr 2023 – abr 2025)  #839 → #60")

ax.legend(
    handles=[line_s, dot_s, star_s, line_f, dot_f, star_f],
    fontsize=8.5, frameon=True, framealpha=0.95,
    facecolor=C_CREMA, edgecolor=C_VERDE_MED,
    labelcolor=C_VERDE_OSC,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.18),
    ncol=3,
)

# ── Título ────────────────────────────────────────────────────────────────────
ax.set_title(
    "Evolución del ranking ATP  ·  Sinner vs Fonseca  ·  Primeros 2 años de carrera",
    fontsize=14, fontweight="bold", color=C_VERDE_OSC,
    loc="left", pad=14,
)

fig.text(
    0.01, 0.01,
    "Fuente: data/matches_combined.csv  (ATP + Challenger)  |  ★ = título ganado  "
    "|  Debut contado desde el primer partido Challenger  |  Ranking al momento del primer partido de cada torneo",
    fontsize=7.5, color=C_VERDE_MED, style="italic",
)

plt.tight_layout(rect=[0, 0.10, 1, 1])
plt.savefig("graficos/sinner_vs_fonseca_ranking.png", dpi=160, bbox_inches="tight",
            facecolor=C_CREMA)
print("Grafico guardado en graficos/sinner_vs_fonseca_ranking.png")
