import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Paleta
C_AMARILLO  = "#D9EF00"
C_VERDE_OSC = "#00342B"
C_VERDE_MED = "#03664F"
C_CREMA     = "#FFFDEE"

# ── Datos ──────────────────────────────────────────────────────────────────
df = pd.read_csv("data/matches_atp.csv", low_memory=False)

IW_NAMES = ["Indian Wells TMS", "Pacific Life Open", "BNP Paribas Open"]
iw = df[df["Tournament"].isin(IW_NAMES)].copy()

ARG_NAMES = [
    "Acasuso", "Baez", "Berlocq", "Calleri", "Cerundolo",
    "Chela", "Coria", "Del Potro", "Delbonis", "Etcheverry",
    "Gaudio", "Mayer", "Monaco", "Nalbandian", "Navone",
    "Pella", "Puerta", "Schwank", "Schwartzman", "Zeballos",
]

def is_arg(name):
    return any(n in str(name) for n in ARG_NAMES)

# Normalizar nombres con espacios/variantes
NAME_MAP = {
    "Del Potro J. M.": "Del Potro J.M.",
    "Etcheverry T. M.": "Etcheverry T.M.",
    "Mayer L. ": "Mayer L.",
    "Monaco J. ": "Monaco J.",
    "Zeballos H. ": "Zeballos H.",
    "Chela J.": "Chela J.I.",
}

def normalize(name):
    return NAME_MAP.get(str(name).strip(), str(name).strip())

# Construir tabla de victorias / derrotas por jugador argentino
records = []
for _, row in iw.iterrows():
    p1, p2, winner = normalize(row["Player_1"]), normalize(row["Player_2"]), normalize(row["Winner"])
    if is_arg(p1):
        records.append({"player": p1, "win": p1 == winner})
    if is_arg(p2):
        records.append({"player": p2, "win": p2 == winner})

stats = pd.DataFrame(records)
stats = stats.groupby("player")["win"].agg(
    wins=lambda x: x.sum(),
    losses=lambda x: (~x).sum(),
).reset_index()
stats["total"] = stats["wins"] + stats["losses"]
stats["win_pct"] = stats["wins"] / stats["total"] * 100

# Etiqueta: Apellido + inicial para distinguir hermanos/homónimos
def make_label(name):
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return parts[0]

stats["label"] = stats["player"].apply(make_label)

# Ordenar por total de partidos jugados
stats = stats.sort_values("total", ascending=True).reset_index(drop=True)

# ── Figura ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor(C_CREMA)
ax.set_facecolor(C_CREMA)

y = np.arange(len(stats))
bar_h = 0.55

# Barras de victorias y derrotas (apiladas horizontalmente)
bars_l = ax.barh(y, stats["losses"], height=bar_h, color=C_VERDE_OSC, zorder=3)
bars_w = ax.barh(y, stats["wins"],   height=bar_h, left=stats["losses"], color=C_AMARILLO, zorder=3)

# Línea vertical en cada barra: total de partidos
for i, row in stats.iterrows():
    ax.plot([row["total"], row["total"]], [i - bar_h/2, i + bar_h/2],
            color=C_CREMA, lw=1.2, zorder=4)

# % de victorias al final de la barra
for i, row in stats.iterrows():
    ax.text(row["total"] + 0.4, i, f'{row["win_pct"]:.0f}%',
            va="center", ha="left", fontsize=8.5, color=C_VERDE_OSC,
            fontweight="bold")

# Etiquetas eje Y
ax.set_yticks(y)
ax.set_yticklabels(stats["label"], fontsize=10, color=C_VERDE_OSC)

# Grilla suave
ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
ax.grid(axis="x", color=C_VERDE_MED, alpha=0.25, linestyle="--", zorder=0)
ax.set_axisbelow(True)

# Ejes
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color(C_VERDE_MED)
ax.tick_params(axis="x", colors=C_VERDE_OSC)
ax.tick_params(axis="y", length=0)
ax.set_xlabel("Partidos jugados", color=C_VERDE_OSC, fontsize=10, labelpad=8)

# Título
ax.set_title(
    "Argentinos en Indian Wells  ·  BNP Paribas Open  (2000–2025)",
    fontsize=14, fontweight="bold", color=C_VERDE_OSC,
    pad=16, loc="left",
)

# Leyenda
patch_l = mpatches.Patch(color=C_VERDE_OSC, label="Derrotas")
patch_w = mpatches.Patch(color=C_AMARILLO, label="Victorias")
ax.legend(
    handles=[patch_w, patch_l],
    loc="lower right", frameon=False,
    labelcolor=C_VERDE_OSC, fontsize=9,
)

plt.tight_layout()
plt.savefig("graficos/iw_argentinos_performance.png", dpi=160, bbox_inches="tight",
            facecolor=C_CREMA)
print("Gráfico guardado en graficos/iw_argentinos_performance.png")
