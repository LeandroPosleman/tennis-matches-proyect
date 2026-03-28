Crea un gráfico de Python siguiendo estas reglas obligatorias:

## Librería
Usar **seaborn** y/o **matplotlib**. Nunca plotly ni otra librería salvo que el usuario lo pida explícitamente.

## Paleta de colores (siempre esta, sin excepciones)
```python
C_AMARILLO  = "#D9EF00"  # destacados, victorias, barras principales
C_VERDE_OSC = "#00342B"  # texto, ejes, spines, derrotas
C_VERDE_MED = "#03664F"  # grilla, acentos secundarios
C_CREMA     = "#FFFDEE"  # fondo de figura y axes
```
- `fig.patch.set_facecolor(C_CREMA)` y `ax.set_facecolor(C_CREMA)`
- Texto y spines en `C_VERDE_OSC`
- Grilla en `C_VERDE_MED` con alpha bajo

## Dónde guardar
- El script: `scripts/grafico_<nombre_descriptivo>.py`
- La imagen: `graficos/<nombre_descriptivo>.png`, dpi=160, bbox_inches="tight"

## Qué hacer
Analiza el pedido del usuario, explorá los datos si hace falta, y generá el script completo y la imagen final.
