#!/usr/bin/env python3
"""Rellena en index.html las secciones destacadas de la portada (ropa de mujer y perfumes).

Lee data/catalogo.json (ya saneado) y escribe tarjetas HTML estáticas entre los
marcadores <!-- PORTADA:ROPA:INICIO --> ... <!-- PORTADA:ROPA:FIN --> (y PERFUMES).
Así la portada se ve sin esperar al JS y los precios salen del mismo catálogo.

Uso:  python3 scripts/generar_portada.py
Para cambiar los destacados, edita las dos listas de códigos de abajo.
"""
from __future__ import annotations

import html
import json
import re
import urllib.parse
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WA = "573106935192"

DESTACADOS_ROPA = [
    "CONJUNTO-064", "CONJUNTO-065", "JEAN-003", "JEAN-005", "BODY-006", "OVERSIZE-002",
    "CONJUNTO-061", "CONJUNTO-070", "PIJAMA-002", "CONJUNTO-076", "BODY-007", "CONJUNTO-067",
]
DESTACADOS_PERFUMES = [
    "COMBO-024", "COMBO-035", "COMBO-031", "COMBO-033", "COMBO-036", "COMBO-037",
    "BIANCO-002", "CLIVE-004",
]

ICONO_WA = ('<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M.057 24l1.687-6.163'
            'c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 '
            '8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 '
            '0 1-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 '
            '9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 '
            '1.746 5.634l-.999 3.648 3.742-.981z"/></svg>')


def fmt(n: int) -> str:
    return "$ " + f"{n:,}".replace(",", ".")


def tarjeta(p: dict) -> str:
    nombre = html.escape(p["nombre"])
    precio = fmt(p["precio_venta"])
    talla = p.get("tallas_txt") or ""
    msg = f"Hola, quiero pedir:\n*{p['nombre']}* (Ref: {p['codigo']})\n"
    if talla:
        msg += f"Tallas: {talla}\n"
    msg += f"Precio: *{precio} COP*\n\n¿Está disponible?"
    url = f"https://wa.me/{WA}?text=" + urllib.parse.quote(msg, safe="")
    img = html.escape(p["imagenes"][0])
    cod = html.escape(p["codigo"])
    det = f'\n        <div class="card-details"><span>📏 {html.escape(talla)}</span></div>' if talla else ""
    return f'''    <article class="card card-destacada" data-codigo="{cod}">
      <div class="card-media" onclick="window.abrirProducto&amp;&amp;abrirProducto('{cod}')" style="cursor:pointer">
        <img src="{img}" alt="{nombre}" width="675" height="900" loading="lazy" decoding="async" class="card-main-img card-img">
      </div>
      <div class="card-body">
        <div class="card-title-row"><div class="card-brand">{html.escape(p["categoria"])}</div></div>
        <div class="card-model">{nombre}</div>
        <div class="card-pricing"><div class="price-block sale"><span class="price-value">{precio}</span></div></div>{det}
        <a class="btn-card-wa" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer" data-lead="{cod}">
          {ICONO_WA}
          <span>Pedir por WhatsApp</span>
        </a>
      </div>
    </article>'''


def bloque(codigos: list[str], por_codigo: dict) -> str:
    faltan = [c for c in codigos if c not in por_codigo or not por_codigo[c].get("imagenes") or not por_codigo[c].get("precio_venta")]
    if faltan:
        raise SystemExit(f"destacados sin foto o precio en el catálogo: {faltan}")
    return "\n".join(tarjeta(por_codigo[c]) for c in codigos)


def main() -> int:
    datos = json.loads((RAIZ / "data" / "catalogo.json").read_text(encoding="utf-8"))
    por_codigo = {p["codigo"]: p for p in datos}
    ruta = RAIZ / "index.html"
    t = ruta.read_text(encoding="utf-8")
    for nombre, codigos in (("ROPA", DESTACADOS_ROPA), ("PERFUMES", DESTACADOS_PERFUMES)):
        ini, fin = f"<!-- PORTADA:{nombre}:INICIO -->", f"<!-- PORTADA:{nombre}:FIN -->"
        patron = re.compile(re.escape(ini) + r".*?" + re.escape(fin), re.S)
        if not patron.search(t):
            raise SystemExit(f"faltan los marcadores PORTADA:{nombre} en index.html")
        nuevo = ini + "\n" + bloque(codigos, por_codigo) + "\n    " + fin
        t = patron.sub(lambda m: nuevo, t)
    ruta.write_text(t, encoding="utf-8")
    print(f"Portada actualizada: {len(DESTACADOS_ROPA)} prendas y {len(DESTACADOS_PERFUMES)} perfumes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
