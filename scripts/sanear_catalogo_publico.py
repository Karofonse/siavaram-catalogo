#!/usr/bin/env python3
"""Genera data/catalogo.json: el catálogo público de Siavaran, sin datos internos.

Entrada: un JSON de productos (el del datalake, con costo/proveedor/marca, o el
data/catalogo.json ya limpio). Salida: data/catalogo.json con solo campos públicos.

Qué hace:
  * Quita costo del proveedor, margen, nombre y teléfono del proveedor, texto
    original (lleva el costo), referencia interna, marca y modelo.
  * Crea `nombre` visible sin marcas de terceros (p. ej. "Tenis urbano hombre N.º 524").
  * Reclasifica combos y sets (venían como "Ropa") a la sección Perfumes.
  * Deja solo el precio de venta (`precio_venta`).

Uso (desde la raíz del repo):

    python3 scripts/sanear_catalogo_publico.py                      # re-sanea data/catalogo.json
    python3 scripts/sanear_catalogo_publico.py ruta/catalogo.json   # nuevo catálogo del datalake

Idempotente. No reescribe el historial de git. La vista interna (costos, calculadora)
no vive en este repo: se genera en local en didactic-octo-eureka.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "catalogo.json"

CAMPOS_PUBLICOS = (
    "codigo", "nombre", "categoria", "seccion", "genero",
    "tallas", "talla_min", "talla_max", "sistema_tallas", "tallas_txt",
    "imagenes", "videos", "moneda", "precio_venta", "fecha", "en_oferta",
)
CAMPOS_PROHIBIDOS = (
    "precio", "precio_anterior", "proveedor", "remitente", "descripcion_original",
    "referencia", "ganancia", "margen", "marca", "modelo", "coleccion",
)

# Categoría pública (genérica, sin marcas) a partir de la del datalake.
CATEGORIA_PUBLICA = {
    "Crocs": "Zuecos", "Sueco": "Zuecos", "Bota": "Botas", "Chancla": "Chancletas",
    "Guayo": "Guayos", "Sandalia": "Sandalias", "Ropa": "Prenda", "Cargo": "Pantalón cargo",
}
# Cómo se llama cada tipo en el nombre visible.
TIPO_NOMBRE = {
    "Tenis": "Tenis urbano", "Zuecos": "Zuecos", "Botas": "Botas", "Chancletas": "Chancletas",
    "Guayos": "Guayos", "Sandalias": "Sandalias", "Calzado": "Calzado", "Perfume": "Perfume importado",
    "Combo": "Combo de perfume y cuidado corporal", "Set": "Set de fragancias", "Prenda": "Prenda",
    "Bolso": "Bolso", "Leggins": "Leggins", "Pantaloneta": "Pantaloneta", "Pantalón cargo": "Pantalón cargo",
}
GENERO_TXT = {"Dama": "mujer", "Hombre": "hombre", "Niño": "niño", "Unisex": "unisex"}

# Nombres y tallas escritos a mano para los destacados de la portada (sin marcas).
NOMBRES_MANUALES = {
    "CONJUNTO-064": ("Conjunto deportivo de licra mujer", "Talla única"),
    "CONJUNTO-065": ("Conjunto deportivo 3 piezas mujer", "Talla única"),
    "CONJUNTO-063": ("Conjunto jogger beige mujer", "Talla única"),
    "CONJUNTO-061": ("Conjunto deportivo blusa y sudadera mujer", "M · L · XL"),
    "CONJUNTO-070": ("Conjunto deportivo blusa y sudadera mujer", "M · L"),
    "CONJUNTO-076": ("Conjunto manga larga mujer", "Talla única"),
    "CONJUNTO-067": ("Conjunto deportivo top y legging mujer", "S · M · L"),
    "JEAN-003": ("Jean stretch skinny mujer", "3 · 5 · 7 · 9 · 11 · 13"),
    "JEAN-005": ("Jean baggy negro mujer", "3 · 5 · 7 · 9 · 11"),
    "BODY-006": ("Body de malla mujer", "Talla única"),
    "BODY-007": ("Body básico negro mujer", "Talla única"),
    "OVERSIZE-002": ("Camiseta oversize estampada mujer", "S · M · L · XL"),
    "PIJAMA-002": ("Pijama en tela rib mujer", "Talla única"),
    # Perfumes y sets de regalo destacados (descripción tomada de su ficha, sin marca).
    "COMBO-024": ("Combo de regalo: perfume, body splash y caja", ""),
    "COMBO-035": ("Combo de regalo: perfume, body splash y caja con moño", ""),
    "COMBO-031": ("Combo de regalo: perfume, mantequilla corporal y caja", ""),
    "COMBO-033": ("Set de regalo de cuidado corporal en caja", ""),
    "COMBO-036": ("Combo de perfume y body splash con bolsa de regalo", ""),
    "COMBO-037": ("Combo de perfume y body splash con bolsa de regalo y moño", ""),
    # Perfumes con descriptor propio (tomado de su ficha, sin marca).
    "AL-004": ("Perfume dulce y frutal", ""),
    "BIANCO-002": ("Perfume dulce y cremoso", ""),
    "ECLAIRE-002": ("Perfume dulce y seductor mujer", ""),
    "ISLAND-002": ("Perfume fresco y tropical", ""),
    "MOSCHINO-003": ("Perfume fresco y divertido mujer", ""),
    "THANK-002": ("Perfume dulce y juvenil", ""),
    "VICTORIA-002": ("Perfume cálido y envolvente", ""),
    "CLIVE-003": ("Perfume intenso y sofisticado", ""),
    "CLIVE-004": ("Perfume intenso, elegante y dulce", ""),
}


CATEGORIA_MANUAL = {"OVERSIZE-002": "Camiseta"}


def _num(codigo: str) -> int:
    m = re.search(r"(\d+)$", codigo or "")
    return int(m.group(1)) if m else 0


def _es_perfume(p: dict) -> bool:
    # Los "Combo" y "Set" del datalake son siempre de perfume (+ crema, splash o caja de regalo).
    return (p.get("seccion") == "Perfumes" or p.get("categoria") in ("Perfume", "Combo", "Set"))


def sanear_producto(p: dict) -> dict:
    codigo = p["codigo"]
    categoria = p.get("categoria") or ""
    pub = {k: p[k] for k in CAMPOS_PUBLICOS if k in p}
    seccion = p.get("seccion") or "Zapatos"
    if _es_perfume(p):
        seccion = "Perfumes"
        pub["categoria"] = "Perfume" if categoria not in ("Combo", "Set") else categoria
    else:
        pub["categoria"] = CATEGORIA_PUBLICA.get(categoria, categoria)
    pub["seccion"] = seccion
    if codigo in CATEGORIA_MANUAL:
        pub["categoria"] = CATEGORIA_MANUAL[codigo]

    venta = p.get("precio_venta")
    if venta is None and p.get("precio") is not None and not p.get("proveedor") and not p.get("descripcion_original"):
        venta = p.get("precio")   # catálogo ya saneado al estilo del generador
    if venta is not None:
        pub["precio_venta"] = venta

    if codigo in NOMBRES_MANUALES:
        pub["nombre"], tt = NOMBRES_MANUALES[codigo]
        if tt:
            pub["tallas_txt"] = tt
    elif not p.get("nombre"):
        tipo = TIPO_NOMBRE.get(pub["categoria"], pub["categoria"])
        g = GENERO_TXT.get(p.get("genero") or "", "")
        pub["nombre"] = f"{tipo}{' ' + g if g else ''} N.º {_num(codigo)}"
    return pub


def verificar(datos: list[dict]) -> None:
    claves = set().union(*(p.keys() for p in datos))
    malos = claves.intersection(CAMPOS_PROHIBIDOS)
    if malos:
        raise SystemExit(f"campos prohibidos en el catálogo público: {sorted(malos)}")
    texto = json.dumps(datos, ensure_ascii=False)
    for pat in (r"\+57[\s\d]{8,}", r"Anita"):
        if re.search(pat, texto):
            raise SystemExit(f"rastro del proveedor en el catálogo público: {pat}")
    print(f"OK: {len(datos)} productos, campos {sorted(claves)}")


def main() -> int:
    entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else SALIDA
    datos = json.loads(entrada.read_text(encoding="utf-8"))
    limpios = [sanear_producto(p) for p in datos]
    verificar(limpios)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(limpios, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Escrito {SALIDA} ({SALIDA.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
