# Tennis Matches

Dataset y análisis de partidos de tenis masculino profesional (ATP) desde el año 2000 hasta la actualidad.

## Estructura

```
tennis-matches-proyect/
├── data/
│   └── matches.csv       # Dataset principal (~67.000 partidos)
├── graficos/             # Imágenes generadas
├── notebooks/            # Exploración interactiva
└── scripts/              # Scripts para generar gráficos y análisis
```

## Dataset

El archivo `data/matches.csv` contiene ~67.196 partidos de singles masculino ATP entre 2000-01-03 y 2026-02-28.

| Columna    | Descripción                                              |
|------------|----------------------------------------------------------|
| Tournament | Nombre del torneo                                        |
| Date       | Fecha del partido (YYYY-MM-DD)                           |
| Series     | Categoría: Grand Slam, Masters 1000, ATP500, ATP250...   |
| Court      | Tipo de cancha: Outdoor / Indoor                         |
| Surface    | Superficie: Hard, Clay, Grass, Carpet                    |
| Round      | Ronda: 1st Round, Quarterfinals, Semifinals, The Final…  |
| Best of    | Formato: 3 o 5 sets                                      |
| Player_1   | Jugador 1 (formato: Apellido I.)                         |
| Player_2   | Jugador 2 (formato: Apellido I.)                         |
| Winner     | Nombre del ganador                                       |
| Rank_1     | Ranking ATP de Player_1                                  |
| Rank_2     | Ranking ATP de Player_2                                  |
| Pts_1      | Puntos ATP de Player_1 (-1 = no disponible)              |
| Pts_2      | Puntos ATP de Player_2 (-1 = no disponible)              |
| Odd_1      | Cuota de apuesta Player_1 (-1.0 = no disponible)         |
| Odd_2      | Cuota de apuesta Player_2 (-1.0 = no disponible)         |
| Score      | Resultado por sets (ej: 6-4 3-6 7-5)                    |

## Gráficos generados

| Archivo | Descripción |
|---------|-------------|
| `graficos/iw_argentinos_performance.png` | Victorias y derrotas de jugadores argentinos en Indian Wells (2000–2025) |
