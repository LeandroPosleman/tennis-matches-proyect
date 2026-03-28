"""
Primeros 2 años en el circuito ATP: Sinner J. vs Fonseca J.
Datos: data/matches.csv  |  Ejecutar desde la raíz del proyecto.

Nota: el dataset contiene solo partidos ATP (no Challengers).
Fonseca disputó muchos Challengers en su primer año que no figuran aquí.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

# ── Paleta del proyecto ─────────────────────────────────────────────────────
C_AMARILLO  = "#D9EF00"   # Sinner
C_VERDE_OSC = "#00342B"   # texto, spines, derrotas
C_VERDE_MED = "#03664F"   # Fonseca / grilla
C_CREMA     = "#FFFDEE"   # fondo

# ── Carga del dataset ───────────────────────────────────────────────────────
df = pd.read_csv("data/matches.csv", low_memory=False)
df["Date"] = pd.to_datetime(df["Date"])

# ── Función: extraer partidos de un jugador en sus primeros N meses ─────────
ROUND_ORDER = {
    "1st Round": 1, "2nd Round": 2, "3rd Round": 3, "4th Round": 4,
    "Quarterfinals": 5, "Semifinals": 6, "The Final": 7,
}

def get_player_data(player_name, months=24):
    mask = (df["Player_1"] == player_name) | (df["Player_2"] == player_name)
    sub = df[mask].copy().sort_values("Date").reset_index(drop=True)
    debut = sub.iloc[0]["Date"]
    cutoff = debut + pd.DateOffset(months=months)
    sub = sub[sub["Date"] <= cutoff].copy()

    sub["won"]     = sub["Winner"] == player_name
    sub["months"]  = (sub["Date"] - debut).dt.days / 30.44
    sub["my_rank"] = sub.apply(
        lambda r: r["Rank_1"] if r["Player_1"] == player_name else r["Rank_2"], axis=1
    )
    sub["round_val"] = sub["Round"].map(ROUND_ORDER).fillna(0)
    # Si ganó la final → campeón (valor 8)
    sub.loc[(sub["Round"] == "The Final") & sub["won"], "round_val"] = 8

    sub["debut"] = debut
    return sub

sinner  = get_player_data("Sinner J.")
fonseca = get_player_data("Fonseca J.")

# ── Helpers ─────────────────────────────────────────────────────────────────
def win_loss(sub):
    w = sub["won"].sum()
    l = (~sub["won"]).sum()
    return int(w), int(l)

def series_wl(sub):
    result = {}
    for s in ["Grand Slam", "Masters 1000", "ATP500", "ATP250"]:
        s_sub = sub[sub["Series"] == s]
        if len(s_sub):
            w = s_sub["won"].sum()
            l = (~s_sub["won"]).sum()
            result[s] = (int(w), int(l))
        else:
            result[s] = (0, 0)
    return result

def titles(sub):
    return sub[(sub["Round"] == "The Final") & sub["won"]]

def best_gs(sub):
    gs = sub[sub["Series"] == "Grand Slam"]
    best = {}
    for tourn, g in gs.groupby("Tournament"):
        best[tourn] = int(g["round_val"].max())
    return best

s_wl     = win_loss(sinner)
f_wl     = win_loss(fonseca)
s_series = series_wl(sinner)
f_series = series_wl(fonseca)
s_titles = titles(sinner)
f_titles = titles(fonseca)

# ── Figura ──────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 13), facecolor=C_CREMA)
fig.suptitle(
    "Primeros 2 años en el circuito ATP  ·  Sinner vs Fonseca",
    fontsize=17, fontweight="bold", color=C_VERDE_OSC, y=0.98,
)

gs_layout = fig.add_gridspec(
    3, 3, hspace=0.50, wspace=0.38,
    left=0.07, right=0.97, top=0.93, bottom=0.07,
)

ax_rank   = fig.add_subplot(gs_layout[0, :])     # fila 1: ranking
ax_wl     = fig.add_subplot(gs_layout[1, 0])     # fila 2: W/L total
ax_series = fig.add_subplot(gs_layout[1, 1:])    # fila 2: W/L por serie
ax_gs     = fig.add_subplot(gs_layout[2, :2])    # fila 3: GS
ax_stats  = fig.add_subplot(gs_layout[2, 2])     # fila 3: resumen

def style_ax(ax):
    ax.set_facecolor(C_CREMA)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["bottom"].set_color(C_VERDE_MED)
    ax.spines["left"].set_color(C_VERDE_MED)
    ax.tick_params(colors=C_VERDE_OSC)
    ax.grid(color=C_VERDE_MED, alpha=0.2, linestyle="--", zorder=0)
    ax.set_axisbelow(True)

for ax in [ax_rank, ax_wl, ax_series, ax_gs, ax_stats]:
    style_ax(ax)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. EVOLUCIÓN DEL RANKING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
for sub, color, label, marker in [
    (sinner,  C_AMARILLO,  "Sinner",  "o"),
    (fonseca, C_VERDE_MED, "Fonseca", "s"),
]:
    ax_rank.plot(
        sub["months"], sub["my_rank"],
        color=color, linewidth=2.2, marker=marker,
        markersize=6, markeredgecolor=C_VERDE_OSC, markeredgewidth=0.6,
        label=label, zorder=3,
    )
    ax_rank.fill_between(
        sub["months"], sub["my_rank"], sub["my_rank"].max() * 1.05,
        alpha=0.07, color=color,
    )

# Hitos
def annotate_hit(ax, m, rk, label, color, dx=0.4, dy=50):
    ax.annotate(
        label, xy=(m, rk),
        xytext=(m + dx, rk + dy),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.1),
        fontsize=7.5, color=color, fontweight="bold",
    )

# Sinner: 1er título (Sofia Open Nov 2020)
sofia = sinner[sinner["Tournament"] == "Sofia Open"].iloc[0]
annotate_hit(ax_rank, sofia["months"], sofia["my_rank"], "1er título\nSofia Open\n#44",
             C_AMARILLO, dx=0.5, dy=120)

# Sinner: French Open 2020 QF
rg20 = sinner[(sinner["Tournament"] == "French Open") & (sinner["Date"].dt.year == 2020)].iloc[-1]
annotate_hit(ax_rank, rg20["months"], rg20["my_rank"], "Roland Garros QF\n#75",
             C_AMARILLO, dx=-7, dy=-120)

# Fonseca: AO 2025 (venció Rublev)
ao25 = fonseca[fonseca["Tournament"] == "Australian Open"].iloc[0]
annotate_hit(ax_rank, ao25["months"], ao25["my_rank"], "AO – vence Rublev\n#112",
             C_VERDE_MED, dx=0.5, dy=100)

# Fonseca: Argentina Open (título)
arg25 = fonseca[fonseca["Tournament"] == "Argentina Open"].iloc[-1]
annotate_hit(ax_rank, arg25["months"], arg25["my_rank"], "1er título\nArgentina Open\n#99",
             C_VERDE_MED, dx=-7, dy=150)

ax_rank.invert_yaxis()
ax_rank.set_xlim(-0.5, 25)
ax_rank.set_xlabel("Meses desde el debut ATP", color=C_VERDE_OSC, fontsize=10)
ax_rank.set_ylabel("Ranking ATP  ↑ mejor", color=C_VERDE_OSC, fontsize=10)
ax_rank.set_title("Evolución del Ranking ATP (partidos ATP únicamente)", fontsize=12,
                  fontweight="bold", color=C_VERDE_OSC, loc="left", pad=10)
ax_rank.legend(fontsize=10, frameon=False, labelcolor=C_VERDE_OSC)
ax_rank.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"#{int(x)}"))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. VICTORIAS / DERROTAS TOTALES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
players  = ["Sinner", "Fonseca"]
wins_arr = [s_wl[0], f_wl[0]]
loss_arr = [s_wl[1], f_wl[1]]
x = np.arange(2)
w = 0.35

bars_w = ax_wl.bar(x, wins_arr, width=w, color=[C_AMARILLO, C_VERDE_MED],
                   label="Victorias", zorder=3, edgecolor=C_VERDE_OSC, linewidth=0.6)
bars_l = ax_wl.bar(x, loss_arr, width=w, bottom=wins_arr,
                   color=C_VERDE_OSC, label="Derrotas", zorder=3,
                   edgecolor=C_VERDE_OSC, linewidth=0.6, alpha=0.75)

# Etiquetas dentro de barras
for i, (w_val, l_val) in enumerate(zip(wins_arr, loss_arr)):
    total = w_val + l_val
    pct   = w_val / total * 100
    ax_wl.text(i, w_val / 2,      f"{w_val}V",   ha="center", va="center",
               fontsize=10, fontweight="bold", color=C_VERDE_OSC)
    ax_wl.text(i, w_val + l_val / 2, f"{l_val}D", ha="center", va="center",
               fontsize=10, fontweight="bold", color=C_CREMA)
    ax_wl.text(i, total + 1.5, f"{pct:.0f}%", ha="center", va="bottom",
               fontsize=11, fontweight="bold",
               color=C_AMARILLO if i == 0 else C_VERDE_MED)

ax_wl.set_xticks(x)
ax_wl.set_xticklabels(players, fontsize=11, color=C_VERDE_OSC, fontweight="bold")
ax_wl.set_ylabel("Partidos ATP", color=C_VERDE_OSC, fontsize=9)
ax_wl.set_title("V/D en primeros 2 años\n(partidos ATP)", fontsize=11,
                fontweight="bold", color=C_VERDE_OSC, loc="left")
ax_wl.tick_params(axis="x", length=0)
p_w = mpatches.Patch(color=C_AMARILLO,  label="Victorias")
p_l = mpatches.Patch(color=C_VERDE_OSC, label="Derrotas")
ax_wl.legend(handles=[p_w, p_l], fontsize=8, frameon=False, labelcolor=C_VERDE_OSC)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. WIN RATE POR CATEGORÍA DE TORNEO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
series_labels = ["Grand Slam", "Masters\n1000", "ATP500", "ATP250"]
series_keys   = ["Grand Slam", "Masters 1000", "ATP500", "ATP250"]
x = np.arange(len(series_labels))
bw = 0.32

def wr_arr(series_dict, keys):
    out = []
    for k in keys:
        w_v, l_v = series_dict[k]
        if w_v + l_v > 0:
            out.append(w_v / (w_v + l_v) * 100)
        else:
            out.append(np.nan)
    return out

s_wr = wr_arr(s_series, series_keys)
f_wr = wr_arr(f_series, series_keys)

bs = ax_series.bar(x - bw / 2, s_wr, width=bw, color=C_AMARILLO, zorder=3,
                   edgecolor=C_VERDE_OSC, linewidth=0.6, label="Sinner")
bf = ax_series.bar(x + bw / 2, f_wr, width=bw, color=C_VERDE_MED, zorder=3,
                   edgecolor=C_VERDE_OSC, linewidth=0.6, label="Fonseca")

# Partidos jugados debajo de cada barra
for i, key in enumerate(series_keys):
    sw, sl = s_series[key]
    fw, fl = f_series[key]
    ax_series.text(i - bw / 2, -8, f"{sw+sl}p", ha="center", fontsize=7.5,
                   color=C_AMARILLO, fontweight="bold")
    ax_series.text(i + bw / 2, -8, f"{fw+fl}p", ha="center", fontsize=7.5,
                   color=C_VERDE_MED, fontweight="bold")

# Etiquetas de porcentaje
for bar_group, color in [(bs, C_AMARILLO), (bf, C_VERDE_MED)]:
    for bar in bar_group:
        h = bar.get_height()
        if not np.isnan(h):
            ax_series.text(
                bar.get_x() + bar.get_width() / 2, h + 1.5,
                f"{h:.0f}%", ha="center", va="bottom", fontsize=8,
                color=color, fontweight="bold",
            )

ax_series.set_xticks(x)
ax_series.set_xticklabels(series_labels, fontsize=10, color=C_VERDE_OSC)
ax_series.set_ylim(-12, 105)
ax_series.set_ylabel("% Victorias", color=C_VERDE_OSC, fontsize=9)
ax_series.set_title("Win rate por categoría de torneo  (n = partidos jugados)",
                    fontsize=11, fontweight="bold", color=C_VERDE_OSC, loc="left")
ax_series.axhline(50, color=C_VERDE_MED, lw=0.8, linestyle=":", alpha=0.6)
ax_series.legend(fontsize=9, frameon=False, labelcolor=C_VERDE_OSC)
ax_series.tick_params(axis="x", length=0)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. MEJOR RONDA EN GRAND SLAMS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
round_labels = {1: "1R", 2: "2R", 3: "3R", 4: "4R", 5: "QF", 6: "SF", 7: "F", 8: ""}

# Recolectar mejor ronda por GS por año
def gs_summary(sub, player_name):
    gs = sub[sub["Series"] == "Grand Slam"].copy()
    gs["year"] = gs["Date"].dt.year
    rows = []
    for (t, y), g in gs.groupby(["Tournament", "year"]):
        best_rv = int(g["round_val"].max())
        best_row = g[g["round_val"] == best_rv].iloc[-1]
        won_it = bool((best_row["Round"] == "The Final") and best_row["won"])
        rows.append({
            "tournament": t, "year": y,
            "round_val": best_rv,
            "label": ("Campeón" if won_it else round_labels.get(best_rv, "?")),
            "debut_months": float(best_row["months"]),
        })
    return pd.DataFrame(rows)

s_gs = gs_summary(sinner, "Sinner J.")
f_gs = gs_summary(fonseca, "Fonseca J.")

# Ordenar GS cronológicamente
all_gs = pd.concat([
    s_gs.assign(player="Sinner"),
    f_gs.assign(player="Fonseca"),
]).sort_values(["debut_months"])

gs_x_positions  = list(range(len(s_gs) + len(f_gs)))  # no, mejor separar

# Barras por GS → agrupar los 5 GS de Sinner y 1 de Fonseca
# X = índice de GS jugado, agrupado por nombre corto de torneo
GS_SHORT = {
    "Australian Open": "AO", "French Open": "RG",
    "Wimbledon": "Wimb", "US Open": "USO",
}

def gs_label(row):
    short = GS_SHORT.get(row["tournament"], row["tournament"])
    return f"{short} {row['year']}"

s_gs["x_label"] = s_gs.apply(gs_label, axis=1)
f_gs["x_label"] = f_gs.apply(gs_label, axis=1)

all_labels = sorted(
    set(s_gs["x_label"].tolist() + f_gs["x_label"].tolist()),
    key=lambda l: (int(l[-4:]), ["AO", "RG", "Wimb", "USO"].index(l[:-5].strip()) if l[:-5].strip() in ["AO", "RG", "Wimb", "USO"] else 9)
)
x_pos = {lbl: i for i, lbl in enumerate(all_labels)}
bw = 0.36

for sub, color, label in [(s_gs, C_AMARILLO, "Sinner"), (f_gs, C_VERDE_MED, "Fonseca")]:
    offset = -bw / 2 if label == "Sinner" else bw / 2
    for _, row in sub.iterrows():
        xi = x_pos[row["x_label"]] + offset
        rv = row["round_val"]
        ax_gs.bar(xi, rv, width=bw, color=color, zorder=3,
                  edgecolor=C_VERDE_OSC, linewidth=0.5)
        ax_gs.text(xi, rv + 0.15, row["label"], ha="center", va="bottom",
                   fontsize=7.5, color=color, fontweight="bold")

ax_gs.set_xticks(list(x_pos.values()))
ax_gs.set_xticklabels(list(x_pos.keys()), fontsize=8.5, color=C_VERDE_OSC, rotation=20, ha="right")
ax_gs.set_yticks(range(1, 9))
ax_gs.set_yticklabels(["1R", "2R", "3R", "4R", "QF", "SF", "F", "Camp."],
                       fontsize=8, color=C_VERDE_OSC)
ax_gs.set_ylim(0, 9.5)
ax_gs.set_title("Mejor ronda alcanzada en Grand Slams", fontsize=11,
                fontweight="bold", color=C_VERDE_OSC, loc="left")
p_s = mpatches.Patch(color=C_AMARILLO,  label="Sinner")
p_f = mpatches.Patch(color=C_VERDE_MED, label="Fonseca")
ax_gs.legend(handles=[p_s, p_f], fontsize=9, frameon=False, labelcolor=C_VERDE_OSC)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. CUADRO RESUMEN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ax_stats.axis("off")

s_debut = sinner["debut"].iloc[0].strftime("%b %Y")
f_debut = fonseca["debut"].iloc[0].strftime("%b %Y")
s_rank_ini = int(sinner["my_rank"].iloc[0])
f_rank_ini = int(fonseca["my_rank"].iloc[0])
s_rank_fin = int(sinner["my_rank"].iloc[-1])
f_rank_fin = int(fonseca["my_rank"].iloc[-1])
s_total    = s_wl[0] + s_wl[1]
f_total    = f_wl[0] + f_wl[1]

col_headers = ["", "Sinner", "Fonseca"]
rows_data = [
    ("Debut ATP",           s_debut,                f_debut),
    ("Rank. inicio",        f"#{s_rank_ini}",       f"#{f_rank_ini}"),
    ("Rank. al 2do año",    f"#{s_rank_fin}",       f"#{f_rank_fin}"),
    ("Partidos ATP",        str(s_total),           str(f_total)),
    ("Victorias",           f"{s_wl[0]} ({s_wl[0]/s_total*100:.0f}%)", f"{f_wl[0]} ({f_wl[0]/f_total*100:.0f}%)"),
    ("Títulos ATP",         str(len(s_titles)),     str(len(f_titles))),
    ("Mejor GS",            "RG 2020 – QF",         "AO 2025 – 2R*"),
    ("GS disputados",       str(len(s_gs)),         str(len(f_gs))),
]

# Dibujamos la tabla manualmente
y_start = 0.97
row_h   = 0.115
for ri, (cat, sv, fv) in enumerate(rows_data):
    yy = y_start - ri * row_h
    bg = C_VERDE_OSC if ri % 2 == 0 else C_CREMA
    ax_stats.add_patch(plt.Rectangle((0, yy - row_h * 0.85), 1, row_h * 0.85,
                                     transform=ax_stats.transAxes, color=bg, alpha=0.10, zorder=0))
    ax_stats.text(0.02, yy - row_h * 0.38, cat,
                  transform=ax_stats.transAxes, fontsize=8.5, color=C_VERDE_OSC,
                  va="center", fontweight="bold")
    ax_stats.text(0.52, yy - row_h * 0.38, sv,
                  transform=ax_stats.transAxes, fontsize=8.5, color=C_AMARILLO,
                  va="center", fontweight="bold", ha="center")
    ax_stats.text(0.82, yy - row_h * 0.38, fv,
                  transform=ax_stats.transAxes, fontsize=8.5, color=C_VERDE_MED,
                  va="center", fontweight="bold", ha="center")

# Cabecera
ax_stats.text(0.52, y_start + 0.01, "Sinner",  transform=ax_stats.transAxes,
              fontsize=10, color=C_AMARILLO, fontweight="bold", ha="center")
ax_stats.text(0.82, y_start + 0.01, "Fonseca", transform=ax_stats.transAxes,
              fontsize=10, color=C_VERDE_MED, fontweight="bold", ha="center")
ax_stats.set_title("Resumen comparativo", fontsize=11, fontweight="bold",
                   color=C_VERDE_OSC, loc="left")

# Nota al pie
fig.text(
    0.5, 0.02,
    "* Solo partidos ATP registrados en el dataset (no incluye Challengers ni ITF). "
    "Sinner tuvo 70 partidos ATP en 2 años; Fonseca 20 (activo principalmente en Challengers en 2023).",
    ha="center", fontsize=7.5, color=C_VERDE_MED, style="italic",
)

# ── Guardar ─────────────────────────────────────────────────────────────────
output = "graficos/sinner_vs_fonseca.png"
plt.savefig(output, dpi=160, bbox_inches="tight", facecolor=C_CREMA)
print(f"Gráfico guardado en {output}")
