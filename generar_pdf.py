"""Genera INFORME.pdf a partir de INFORME.md.

Requiere: pip install -r requirements-pdf.txt

- Las imágenes `![descripción](archivo.png)` se muestran como figuras con su
  descripción; si el archivo no existe se dibuja un recuadro de reserva.
- La numeración de páginas y el índice con páginas se resuelven con CSS
  (informe.css).
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import markdown
from weasyprint import HTML

RAIZ = Path(__file__).resolve().parent
ENTRADA = RAIZ / "INFORME.md"
SALIDA = RAIZ / "INFORME.pdf"
ESTILO = RAIZ / "informe.css"
SALTO_DE_PAGINA = "<!-- pagebreak -->"
PATRON_IMAGEN = re.compile(r"^!\[(?P<descripcion>.*)\]\((?P<archivo>[^)]+)\)\s*$", re.MULTILINE)


def identificador(texto: str, separador: str) -> str:
    """Mismo criterio de anclas que GitHub, para que los enlaces del índice funcionen."""
    limpio = re.sub(r"[^\w\- ]", "", texto.lower()).strip()
    return limpio.replace(" ", separador)


def figura(coincidencia: re.Match) -> str:
    descripcion = html.escape(coincidencia["descripcion"])
    archivo = coincidencia["archivo"]
    if (RAIZ / archivo).is_file():
        contenido = f'<img src="{archivo}" alt="{descripcion}">'
    else:
        contenido = f'<div class="reserva">[Insertar captura: {html.escape(archivo)}]</div>'
    return f"<figure>{contenido}<figcaption>{descripcion}</figcaption></figure>"


def construir_html(texto: str) -> str:
    texto = texto.replace(SALTO_DE_PAGINA, '<div class="salto"></div>')
    texto = PATRON_IMAGEN.sub(figura, texto)
    cuerpo = markdown.markdown(
        texto,
        extensions=["tables", "fenced_code", "toc"],
        extension_configs={"toc": {"slugify": identificador}},
    )
    return f'<html lang="es"><head><meta charset="utf-8"></head><body>{cuerpo}</body></html>'


def main() -> int:
    if not ENTRADA.is_file():
        print(f"No se encontró {ENTRADA}", file=sys.stderr)
        return 1
    documento = HTML(string=construir_html(ENTRADA.read_text(encoding="utf-8")), base_url=str(RAIZ))
    documento.write_pdf(SALIDA, stylesheets=[str(ESTILO)])
    print(f"PDF generado: {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
