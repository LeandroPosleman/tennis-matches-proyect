# Tennis Matches Project

## Descripcion del proyecto

Dataset de partidos de tenis masculino profesional (ATP) con datos historicos desde el año 2000 hasta la actualidad (2026).

El objetivo principal es analizar y procesar datos de partidos para extraer estadisticas, entrenar modelos predictivos, o explorar tendencias del tenis profesional.

## Estructura del proyecto

```
tennis-matches-proyect/
├── CLAUDE.md
├── README.md
├── data/
│   └── matches.csv     # Dataset principal (~67.000 partidos, 8.5MB)
├── graficos/           # Imágenes generadas (.png)
├── notebooks/          # Exploración interactiva (.ipynb)
└── scripts/            # Scripts Python para gráficos y procesamiento
```

## Dataset: data/matches.csv

### Columnas

| Columna    | Tipo    | Descripcion                                              |
|------------|---------|----------------------------------------------------------|
| Tournament | string  | Nombre del torneo                                        |
| Date       | date    | Fecha del partido (YYYY-MM-DD)                           |
| Series     | string  | Categoria del torneo (ver abajo)                         |
| Court      | string  | Tipo de cancha: `Outdoor` / `Indoor`                     |
| Surface    | string  | Superficie: `Hard`, `Clay`, `Grass`, `Carpet`            |
| Round      | string  | Ronda: `1st Round`, `2nd Round`, `Quarterfinals`, `Semifinals`, `The Final`, etc. |
| Best of    | int     | Formato: `3` o `5` sets                                  |
| Player_1   | string  | Nombre del jugador 1 (Apellido I.)                       |
| Player_2   | string  | Nombre del jugador 2 (Apellido I.)                       |
| Winner     | string  | Jugador ganador                                          |
| Rank_1     | int     | Ranking ATP de Player_1                                  |
| Rank_2     | int     | Ranking ATP de Player_2                                  |
| Pts_1      | int     | Puntos ATP de Player_1 (`-1` = no disponible)            |
| Pts_2      | int     | Puntos ATP de Player_2 (`-1` = no disponible)            |
| Odd_1      | float   | Cuota de apuesta para Player_1 (`-1.0` = no disponible)  |
| Odd_2      | float   | Cuota de apuesta para Player_2 (`-1.0` = no disponible)  |
| Score      | string  | Resultado por sets (ej: `6-4 3-6 7-5`)                  |

### Categorias de torneos (Series)

- `Grand Slam` — Australian Open, Roland Garros, Wimbledon, US Open
- `Masters` / `Masters 1000` — torneos masters (Indian Wells, Miami, Roma, etc.)
- `Masters Cup` — ATP Finals (fin de año)
- `ATP500` — torneos de 500 puntos
- `ATP250` — torneos de 250 puntos
- `International Gold` — categoria historica equivalente a ATP500
- `International` — categoria historica equivalente a ATP250

### Notas importantes

- Los partidos mas antiguos (circa 2000-2005) tienen `Pts_1`, `Pts_2`, `Odd_1`, `Odd_2` en `-1` por falta de datos.
- El campo `Score` puede contener resultados con tie-breaks, retiros (`RET`) o walkover.
- Los nombres de jugadores usan formato `Apellido I.` (ej: `Federer R.`, `Nadal R.`).
- El dataset cubre partidos de singles masculino ATP unicamente.

### Rango de datos

- **Desde:** 2000-01-03
- **Hasta:** 2026-03-15 (ultima entrada registrada)
- **Total de partidos:** ~67.289 filas

## Paleta de colores (todos los gráficos)

Usar siempre esta paleta en visualizaciones del proyecto:

```python
C_AMARILLO  = "#D9EF00"  # amarillo-verde vibrante → victorias, destacados
C_VERDE_OSC = "#00342B"  # verde muy oscuro        → derrotas, texto, ejes
C_VERDE_MED = "#03664F"  # verde medio             → grilla, acentos
C_CREMA     = "#FFFDEE"  # crema claro             → fondo de figura y ejes
```

- Fondo de figura y axes: `C_CREMA`
- Color de texto principal y spines: `C_VERDE_OSC`
- Grilla: `C_VERDE_MED` con alpha bajo

## Notas de desarrollo

- Usar Python con `pandas` para manipular el CSV dado su tamaño (8.5MB).
- Al filtrar por ganador, comparar con `Player_1` o `Player_2` directamente (columna `Winner` contiene el nombre exacto del ganador).
- Para modelos predictivos, las cuotas de apuesta (`Odd_1`, `Odd_2`) son un buen proxy de probabilidad de victoria pre-partido.
