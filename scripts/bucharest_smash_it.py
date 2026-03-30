"""
Bucharest ATP 250 — Optimizador de equipo Smash It
Construye Elo en arcilla, simula el torneo N veces y encuentra la mejor combinación
de 6 jugadores dentro de 30 créditos.

Ejecutar desde la raíz del proyecto:
    python scripts/bucharest_smash_it.py
"""

import pandas as pd
import numpy as np
from collections import defaultdict
from itertools import combinations

# ─── Configuración ────────────────────────────────────────────────────────────
N_SIMS         = 10_000
BUDGET         = 30.0
TEAM_SIZE      = 6
LOOKBACK_YEARS = 4
ELO_K          = 32
ELO_DEFAULT    = 1500
ELO_QUAL       = 1400   # calificadores: ranking ~130-180
ELO_WC_LOCAL   = 1350   # wildcards rumanos: muy bajo ranking
P_STRAIGHT     = 0.50   # probabilidad de ganar en 2 sets (en arcilla)
np.random.seed(42)

# ─── Mapeo de nombres (formato cuadro → formato dataset) ──────────────────────
NAME_MAP = {
    'Bautista Agut R.': 'Bautista R.',
}

# ─── Créditos Smash It (solo jugadores en cuadro principal) ──────────────────
CREDITS = {
    'Diallo G.':              5.0,
    'Arnaldi M.':             2.4,
    'Moller E.':              1.0,
    'O\'Connell C.':           1.6,
    'Navone M.':              2.4,
    'Borges N.':              5.1,
    'Dzumhur D.':             2.0,
    'Shevchenko A.':          1.3,
    'Maestrelli F.':          1.0,
    'Van De Zandschulp B.':   3.1,
    'Altmaier D.':            3.0,
    'Martinez P.':            1.0,
    'Prizmic D.':             1.2,
    'Choinski J.':            1.0,
    'Marozsan F.':            4.2,
    'Baez S.':                4.4,
    'Gaubas V.':              1.3,
    'Bautista Agut R.':       1.4,
    'Droguet T.':             1.0,
    'Virtanen O.':             1.0,
    'Mannarino A.':           2.6,
    # Wildcards rumanos (en cuadro pero no seleccionables)
    'Boitan G.':              1.0,
    'Jianu F.':               1.0,
    'Turcanu R.':             1.0,
}

# Jugadores seleccionables en Smash It
WC_LOCALS    = {'Boitan G.', 'Jianu F.', 'Turcanu R.'}
SELECTABLE   = [p for p in CREDITS if p not in WC_LOCALS]

# ─── Cuadro principal ─────────────────────────────────────────────────────────
# None = BYE (avanza automáticamente)
# QUAL_x = calificador (desconocido)
DRAW = [
    # Quarter 1 — Diallo [1]
    [('Diallo G.',          None             ),
     ('QUAL_A',             'Arnaldi M.'     ),
     ('Boitan G.',          'Moller E.'      ),
     ('O\'Connell C.',       'Navone M.'      )],

    # Quarter 2 — Borges [4]
    [('Borges N.',          None             ),
     ('Dzumhur D.',         'Jianu F.'       ),
     ('Shevchenko A.',      'Turcanu R.'     ),
     ('Maestrelli F.',      'Van De Zandschulp B.')],

    # Quarter 3 — Marozsan [3]
    [('Altmaier D.',        'Martinez P.'    ),
     ('QUAL_B',             'Prizmic D.'     ),
     ('QUAL_C',             'Choinski J.'    ),
     (None,                 'Marozsan F.'    )],

    # Quarter 4 — Mannarino [2]
    [('Baez S.',            'Gaubas V.'      ),
     ('Bautista Agut R.',   'Droguet T.'     ),
     ('Virtanen O.',         'QUAL_D'         ),
     (None,                 'Mannarino A.'   )],
]

# ─── 1. Construir Elo en arcilla ──────────────────────────────────────────────
def build_clay_elo(df):
    cutoff = df['Date'].max() - pd.DateOffset(years=LOOKBACK_YEARS)
    clay = df[(df['Surface'] == 'Clay') & (df['Date'] >= cutoff)].sort_values('Date')

    elo = defaultdict(lambda: ELO_DEFAULT)

    for _, row in clay.iterrows():
        p1, p2, winner = row['Player_1'], row['Player_2'], row['Winner']
        e1, e2 = elo[p1], elo[p2]
        exp1 = 1 / (1 + 10 ** ((e2 - e1) / 400))

        if winner == p1:
            elo[p1] = e1 + ELO_K * (1 - exp1)
            elo[p2] = e2 + ELO_K * (0 - (1 - exp1))
        else:
            elo[p1] = e1 + ELO_K * (0 - exp1)
            elo[p2] = e2 + ELO_K * (1 - (1 - exp1))

    return dict(elo)


def get_elo(player, elo_ratings):
    ds_name = NAME_MAP.get(player, player)
    if player.startswith('QUAL'):
        return ELO_QUAL
    if player in WC_LOCALS:
        return ELO_WC_LOCAL
    return elo_ratings.get(ds_name, ELO_DEFAULT)


# ─── 2. Simular partido ───────────────────────────────────────────────────────
def simulate_match(p1, p2, elo_ratings, rng):
    """
    Devuelve (ganador, perdedor, pts_ganador, pts_perdedor).
    Puntos Smash It: resultado (odds) + juegos + bonus sets corridos.
    """
    e1 = get_elo(p1, elo_ratings)
    e2 = get_elo(p2, elo_ratings)
    p_win = 1 / (1 + 10 ** ((e2 - e1) / 400))

    p1_wins = rng.random() < p_win
    winner, loser = (p1, p2) if p1_wins else (p2, p1)
    p_w = p_win if p1_wins else 1 - p_win

    # Odds implícitas (con pequeño margen de bookmaker)
    margin  = 1.05
    odds_w  = margin / p_w
    odds_l  = margin / (1 - p_w)

    # Puntos de resultado
    res_w =  5 * odds_w
    res_l = -2 * odds_l

    # Puntos de juegos + bonus
    if rng.random() < P_STRAIGHT:
        games_w, games_l, bonus = 30 * 0.63, 30 * 0.37, 2.0
    else:
        games_w, games_l, bonus = 30 * 0.54, 30 * 0.46, 0.0

    pts_w = res_w + games_w + bonus
    pts_l = res_l + games_l

    return winner, loser, pts_w, pts_l


# ─── 3. Simular quarter (R1 + R2 + QF) ───────────────────────────────────────
def simulate_quarter(matches, elo_ratings, rng):
    results = []
    r2 = []

    for p1, p2 in matches:
        if p1 is None:
            r2.append(p2)
        elif p2 is None:
            r2.append(p1)
        else:
            w, l, pw, pl = simulate_match(p1, p2, elo_ratings, rng)
            results.append((w, l, pw, pl))
            r2.append(w)

    # R2: 2 partidos
    r3 = []
    for i in range(0, 4, 2):
        w, l, pw, pl = simulate_match(r2[i], r2[i+1], elo_ratings, rng)
        results.append((w, l, pw, pl))
        r3.append(w)

    # QF: 1 partido
    w, l, pw, pl = simulate_match(r3[0], r3[1], elo_ratings, rng)
    results.append((w, l, pw, pl))

    return w, results


# ─── 4. Simular torneo completo ───────────────────────────────────────────────
def simulate_tournament(elo_ratings, rng):
    points = defaultdict(float)
    sf_players = []

    for quarter in DRAW:
        qf_winner, results = simulate_quarter(quarter, elo_ratings, rng)
        sf_players.append(qf_winner)
        for w, l, pw, pl in results:
            points[w] += pw
            points[l] += pl

    # SF
    final_players = []
    for i in (0, 2):
        w, l, pw, pl = simulate_match(sf_players[i], sf_players[i+1], elo_ratings, rng)
        points[w] += pw
        points[l] += pl
        final_players.append(w)

    # Final
    w, l, pw, pl = simulate_match(final_players[0], final_players[1], elo_ratings, rng)
    points[w] += pw
    points[l] += pl

    return dict(points)


# ─── 5. Correr N simulaciones ─────────────────────────────────────────────────
def run_simulations(elo_ratings):
    rng = np.random.default_rng(42)
    total_pts  = defaultdict(float)
    total_sims = defaultdict(int)

    for _ in range(N_SIMS):
        result = simulate_tournament(elo_ratings, rng)
        for player, pts in result.items():
            total_pts[player]  += pts
            total_sims[player] += 1

    expected = {}
    for p in SELECTABLE:
        ds_name = NAME_MAP.get(p, p)
        key = ds_name if ds_name in total_pts else p
        n = total_sims.get(key, 0) or N_SIMS
        expected[p] = total_pts.get(key, 0) / n

    return expected


# ─── 6. Optimizar equipo ──────────────────────────────────────────────────────
def optimize_team(expected_pts, top_n=5):
    players  = list(expected_pts.keys())
    rankings = []

    for team in combinations(players, TEAM_SIZE):
        cost = sum(CREDITS[p] for p in team)
        if cost <= BUDGET:
            pts = sum(expected_pts[p] for p in team)
            rankings.append((list(team), pts, cost))

    rankings.sort(key=lambda x: -x[1])
    return rankings[:top_n]


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Cargando datos...")
    df = pd.read_csv('data/matches_atp.csv', parse_dates=['Date'], low_memory=False)

    print(f"Construyendo Elo en arcilla (últimos {LOOKBACK_YEARS} años)...")
    elo_ratings = build_clay_elo(df)

    # Mostrar Elo de jugadores del cuadro
    print("\n── Elo en arcilla por jugador ──────────────────────────────")
    elo_table = []
    for p in SELECTABLE:
        ds = NAME_MAP.get(p, p)
        elo_val = get_elo(p, elo_ratings)
        elo_table.append((p, CREDITS[p], elo_val))
    elo_table.sort(key=lambda x: -x[2])
    print(f"{'Jugador':<28} {'Créditos':>9} {'Elo arcilla':>12}")
    print("─" * 52)
    for p, cr, elo in elo_table:
        print(f"{p:<28} {cr:>9.1f} {elo:>12.0f}")

    print(f"\nSimulando torneo {N_SIMS:,} veces...")
    expected = run_simulations(elo_ratings)

    # Tabla de puntos esperados y valor
    print("\n── Puntos esperados por jugador ────────────────────────────")
    rows = []
    for p in SELECTABLE:
        cr  = CREDITS[p]
        pts = expected[p]
        val = pts / cr if cr > 0 else 0
        rows.append((p, cr, pts, val))
    rows.sort(key=lambda x: -x[2])
    print(f"{'Jugador':<28} {'Créditos':>9} {'Pts esp.':>9} {'Pts/crédito':>12}")
    print("─" * 62)
    for p, cr, pts, val in rows:
        print(f"{p:<28} {cr:>9.1f} {pts:>9.1f} {val:>12.2f}")

    # Top 5 equipos
    print(f"\nOptimizando equipo ({TEAM_SIZE} jugadores, presupuesto {BUDGET} créditos)...")
    top_teams = optimize_team(expected)

    for rank, (team, total, cost) in enumerate(top_teams, 1):
        print(f"\n── Equipo #{rank} — {total:.1f} pts esperados ({cost:.1f} créditos usados) ──")
        print(f"{'Jugador':<28} {'Créditos':>9} {'Pts esp.':>9}")
        print("─" * 50)
        for p in sorted(team, key=lambda x: -expected[x]):
            print(f"{p:<28} {CREDITS[p]:>9.1f} {expected[p]:>9.1f}")
        print("─" * 50)
        print(f"{'TOTAL':<28} {cost:>9.1f} {total:>9.1f}")
