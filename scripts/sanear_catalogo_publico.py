#!/usr/bin/env python3
"""Quita datos internos del JSON embebido en index.html.

Deja solo el precio de venta y los campos públicos del catálogo.
Elimina, si reaparecen: costo del proveedor, margen, nombre o teléfono
del proveedor, texto original (suele llevar el costo) y la referencia interna.

Uso (desde la raíz del repo):

    python3 scripts/sanear_catalogo_publico.py
    python3 scripts/sanear_catalogo_publico.py ruta/al/index.html

Idempotente. No reescribe el historial de git.

La vista interna no debe vivir en este repo (GitHub Pages publica todo):
generarla en didactic-octo-eureka con

    python3 datalake.py unificar datalake/gold --salida tienda

y abrir tienda/index.html en local. El HTML de clientes se genera con
`--cliente` (whatsapp_catalogo.sanear_para_cliente). Este sitio ya tiene
diseño propio: después de pegar productos nuevos aquí, vuelve a correr
este script antes de publicar.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CAMPOS_PUBLICOS = (
    "codigo",
    "marca",
    "modelo",
    "categoria",
    "seccion",
    "genero",
    "tallas",
    "talla_min",
    "talla_max",
    "sistema_tallas",
    "imagenes",
    "videos",
    "moneda",
    "precio_venta",
    "coleccion",
    "fecha",
    "en_oferta",
)

CAMPOS_PROHIBIDOS = (
    "precio",
    "precio_anterior",
    "proveedor",
    "remitente",
    "descripcion_original",
    "referencia",
    "ganancia",
    "margen",
)

# Rastros de las vistas internas o de la fórmula de margen que no deben
# volver a publicarse. No se listan teléfonos ni nombres de proveedores.
LEAK_PATTERNS = [
    (r"precioVentaFormula", "fórmula de margen"),
    (r"ENVIO_PAUTA", "constante de margen"),
    (r"getProfit\s*=", "cálculo de ganancia"),
    (r"\?modo=interno", "vista interna por URL"),
    (r"\?modo=mayorista", "vista mayorista por URL"),
    (r"id=\"calc-costo\"", "calculadora de costos"),
    (r"id=\"filtro-proveedor\"", "filtro de proveedor"),
    (r"id=\"filtro-ganancia\"", "filtro de ganancia"),
    (r"Texto original del proveedor", "texto del proveedor en el modal"),
]


def _extract_productos(text: str) -> tuple[int, int, list]:
    m = re.search(r"const PRODUCTOS = ", text)
    if not m:
        raise SystemExit("No se encontró 'const PRODUCTOS = ' en el HTML")
    i = text.find("[", m.start())
    depth = 0
    in_str = False
    esc = False
    quote = None
    end = None
    for j, ch in enumerate(text[i:], start=i):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue
        if ch in ('"', "'"):
            in_str = True
            quote = ch
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = j
                break
    if end is None:
        raise SystemExit("No se pudo cerrar el array PRODUCTOS")
    return i, end, json.loads(text[i : end + 1])


def sanear_productos(productos: list[dict]) -> list[dict]:
    limpios = []
    for p in productos:
        limpio = {k: p[k] for k in CAMPOS_PUBLICOS if k in p}
        venta = p.get("precio_venta")
        # Catálogo ya saneado al estilo del generador: precio == venta, sin costo.
        if venta is None and p.get("precio") is not None and not p.get("proveedor") and not p.get("descripcion_original"):
            venta = p.get("precio")
        if venta is not None:
            limpio["precio_venta"] = venta
        limpios.append(limpio)
    return limpios


def verificar(text: str, productos: list[dict]) -> None:
    errores = []
    keys = set()
    for p in productos:
        keys.update(p.keys())
    prohibidos = keys.intersection(CAMPOS_PROHIBIDOS)
    if prohibidos:
        errores.append(f"campos prohibidos en PRODUCTOS: {sorted(prohibidos)}")
    for pat, label in LEAK_PATTERNS:
        if re.search(pat, text):
            errores.append(f"queda '{label}' en el archivo publicado")
    # Teléfonos +57 distintos al WhatsApp público de la tienda
    tienda = "573106935192"
    for m in re.finditer(r"\+57[\s\-]*\d[\d\s\-]{7,}", text):
        digits = re.sub(r"\D", "", m.group())
        if digits != tienda:
            errores.append(f"teléfono que no es el de la tienda: {m.group()!r}")
    if "wa.me/573106935192" not in text:
        errores.append("faltó el WhatsApp público de la tienda")
    if "const PRODUCTOS = " not in text:
        errores.append("faltó PRODUCTOS")
    if "function openWhatsAppOrder" not in text:
        errores.append("faltó openWhatsAppOrder")
    if "function toggleFavorite" not in text:
        errores.append("faltó favoritos")
    if "cro-faq-box" not in text:
        errores.append("faltó el FAQ")
    if "getSalePrice" not in text:
        errores.append("faltó getSalePrice")
    if errores:
        raise SystemExit("Verificación fallida:\n- " + "\n- ".join(errores))
    print(f"OK: {len(productos)} productos, campos {sorted(keys)}")


def main() -> int:
    ruta = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
    if not ruta.is_absolute():
        cand = Path(__file__).resolve().parent.parent / ruta
        if cand.exists():
            ruta = cand
        else:
            ruta = Path.cwd() / ruta
    text = ruta.read_text(encoding="utf-8")
    start, end, productos = _extract_productos(text)
    print(f"Leídos {len(productos)} productos de {ruta}")
    limpios = sanear_productos(productos)
    datos_js = json.dumps(limpios, ensure_ascii=False, separators=(", ", ": ")).replace("</", "<\\/")
    text = text[:start] + datos_js + text[end + 1 :]
    _, _, otra_vez = _extract_productos(text)
    verificar(text, otra_vez)
    ruta.write_text(text, encoding="utf-8")
    print(f"Escrito {ruta} ({len(text):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
