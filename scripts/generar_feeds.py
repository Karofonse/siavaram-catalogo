#!/usr/bin/env python3
"""Genera feeds de catálogo de Siavaran para Meta Commerce Manager y Google Merchant Center.

Uso (desde la raíz del repo):
    python3 scripts/generar_feeds.py

Lee:
    - data/catalogo.json
    - scripts/productos_permitidos.json

Genera en feeds/:
    - feeds/meta-catalogo.csv
    - feeds/google-merchant.tsv
    - feeds/README.txt
"""
from datetime import date
from pathlib import Path
from urllib.parse import quote
import csv
import json
import re
import sys
import unicodedata

RAIZ = Path(__file__).resolve().parent.parent
SITIO = "https://siavaran.com"
MARCA = "Siavaran"
MAX_TITULO = 150
# Solo se usa la foto principal (la que se revisó a mano); las demás no se auditaron.
MAX_FOTOS_ADICIONALES = 0

ENVIO_TXT = (
    "Envíos a toda Colombia; el costo y el tiempo dependen de tu ciudad "
    "y te los confirmamos por WhatsApp"
)

META_CAMPOS = [
    "id",
    "title",
    "description",
    "availability",
    "condition",
    "price",
    "link",
    "image_link",
    "brand",
    "additional_image_link",
    "google_product_category",
    "product_type",
    "gender",
    "age_group",
]

GOOGLE_CAMPOS = [
    "id",
    "title",
    "description",
    "link",
    "image_link",
    "additional_image_link",
    "availability",
    "price",
    "brand",
    "condition",
    "identifier_exists",
    "google_product_category",
    "product_type",
    "gender",
    "age_group",
    "item_group_id",
]

# Taxonomía oficial de Google Product Category (en-US).
CAT_GOOGLE_POR_CATEGORIA = {
    "Bermuda": "Apparel & Accessories > Clothing > Shorts",
    "Blusa": "Apparel & Accessories > Clothing > Shirts & Tops",
    "Body": "Apparel & Accessories > Clothing",
    "Bolso": "Apparel & Accessories > Handbags, Wallets & Cases > Handbags",
    "Calentador": "Apparel & Accessories > Clothing > Activewear",
    "Camibuso": "Apparel & Accessories > Clothing > Shirts & Tops",
    "Camisa": "Apparel & Accessories > Clothing > Shirts & Tops",
    "Camiseta": "Apparel & Accessories > Clothing > Shirts & Tops",
    "Camisilla": "Apparel & Accessories > Clothing > Shirts & Tops",
    "Chaqueta": "Apparel & Accessories > Clothing > Outerwear > Coats & Jackets",
    "Conjunto": "Apparel & Accessories > Clothing > Outfit Sets",
    "Enterizo": "Apparel & Accessories > Clothing > One-Pieces",
    "Gorra": "Apparel & Accessories > Clothing Accessories > Hats",
    "Jean": "Apparel & Accessories > Clothing > Pants",
    "Leggins": "Apparel & Accessories > Clothing > Pants",
    "Medias": "Apparel & Accessories > Clothing > Underwear & Socks > Socks",
    "Pantaloneta": "Apparel & Accessories > Clothing > Shorts",
    "Pantalón cargo": "Apparel & Accessories > Clothing > Pants",
    "Pijama": "Apparel & Accessories > Clothing > Sleepwear & Loungewear > Pajamas",
    "Sudadera": "Apparel & Accessories > Clothing > Activewear",
}

CAT_GOOGLE_POR_SECCION = {
    "Perfumes": "Health & Beauty > Personal Care > Cosmetics > Perfume & Cologne",
    "Ropa": "Apparel & Accessories > Clothing",
    "Zapatos": "Apparel & Accessories > Shoes",
}

MARCAS_AJENAS = (
    "adidas",
    "armani",
    "asics",
    "balenciaga",
    "bath & body works",
    "calvin klein",
    "carolina herrera",
    "chanel",
    "converse",
    "crocs",
    "diesel",
    "dior",
    "dolce",
    "fila",
    "gucci",
    "hoka",
    "hugo boss",
    "jean paul gaultier",
    "jordan",
    "karl lagerfeld",
    "lacoste",
    "lattafa",
    "louis vuitton",
    "new balance",
    "nike",
    "off-white",
    "onitsuka",
    "paco rabanne",
    "prada",
    "puma",
    "reebok",
    "salomon",
    "shein",
    "skechers",
    "timberland",
    "tommy hilfiger",
    "under armour",
    "valentino",
    "vans",
    "versace",
    "victoria secret",
    "victoria's secret",
    "zara",
)

PATRONES_PROHIBIDOS = [
    ("envío gratis", re.compile(r"\benvio\s+gratis\b")),
    ("gratis", re.compile(r"\bgratis\b")),
    ("rango de días", re.compile(r"\b\d+\s*(?:a|-|–)\s*\d+\s*dias?\b")),
    ("2 a 5", re.compile(r"\b2\s*a\s*5\b")),
    ("plazo en días/horas", re.compile(r"\b\d+\s*(?:dias?|horas?)\b")),
    ("original", re.compile(r"\boriginal(?:es)?\b")),
    ("réplica", re.compile(r"\breplicas?\b")),
    ("imitación/clon/AAA", re.compile(r"\b(?:imitacion(?:es)?|clon(?:es)?|triple\s+a|aaa)\b")),
    ("talla única", re.compile(r"\btalla\s+unica\b")),
    (
        "marca ajena",
        re.compile(r"\b(?:" + "|".join(re.escape(m) for m in MARCAS_AJENAS) + r")\b"),
    ),
]


def normalizar(texto):
    n = unicodedata.normalize("NFKD", str(texto or ""))
    n = "".join(c for c in n if not unicodedata.combining(c))
    return " ".join(n.lower().split())


def limpiar_linea(texto):
    return " ".join(str(texto or "").replace("\t", " ").split())


def es_talla_unica(val):
    n = normalizar(val)
    return n in {"u", "unica", "talla unica", "talla u"} or "talla unica" in n


def tallas_visibles(prod):
    txt = limpiar_linea(prod.get("tallas_txt") or "")
    if not txt:
        lista = prod.get("tallas") or []
        if isinstance(lista, list) and lista:
            txt = ", ".join(limpiar_linea(t) for t in lista if str(t).strip())
    if not txt or es_talla_unica(txt):
        return ""
    partes = [p.strip() for p in re.split(r"\s*[·,|/]\s*", txt) if p.strip()]
    if any(es_talla_unica(p) for p in partes):
        return ""
    return ", ".join(partes)


def titulo(prod):
    """Título del catálogo (máx 150 chars), usando la lógica de nombre() de ref para ropa de mujer."""
    n = limpiar_linea(prod.get("nombre") or "")
    if not n:
        sys.exit(f"Error: el producto {prod['codigo']} no tiene nombre.")
    seccion = limpiar_linea(prod.get("seccion") or "")
    genero = normalizar(prod.get("genero") or "")
    codigo = prod["codigo"]

    es_perfume = seccion == "Perfumes" or codigo.startswith(("COMBO", "PERFUME", "SET"))
    es_otro_genero = genero in {"hombre", "nino", "unisex"} or bool(
        re.search(r"\b(hombre|caballero|nino|nina|unisex)\b", normalizar(n))
    )
    ya_dice_mujer = bool(re.search(r"\b(mujer|dama)\b", normalizar(n)))

    if not es_perfume and not es_otro_genero and not ya_dice_mujer and seccion == "Ropa":
        n = f"{n} para mujer"

    if len(n) > MAX_TITULO:
        recortado = n[:MAX_TITULO].rsplit(" ", 1)[0].rstrip(" ,;:-")
        n = recortado if len(recortado) >= 40 else n[:MAX_TITULO].rstrip()
    return n


def genero_y_edad(prod):
    """Devuelve (gender, age_group) SOLO si el nombre o campo genero del catálogo lo dice."""
    texto = normalizar(f"{prod.get('nombre') or ''} {prod.get('genero') or ''}")
    if re.search(r"\b(mujer|dama)\b", texto):
        return "female", "adult"
    if re.search(r"\b(hombre|caballero)\b", texto):
        return "male", "adult"
    return "", ""


def google_product_category(prod):
    seccion = limpiar_linea(prod.get("seccion") or "")
    cat = limpiar_linea(prod.get("categoria") or "")
    if seccion == "Perfumes":
        return CAT_GOOGLE_POR_SECCION["Perfumes"]
    if cat in CAT_GOOGLE_POR_CATEGORIA:
        return CAT_GOOGLE_POR_CATEGORIA[cat]
    if seccion in CAT_GOOGLE_POR_SECCION:
        return CAT_GOOGLE_POR_SECCION[seccion]
    return "Apparel & Accessories > Clothing"


def product_type(prod):
    seccion = limpiar_linea(prod.get("seccion") or "")
    cat = limpiar_linea(prod.get("categoria") or "")
    if seccion and cat:
        return f"{seccion} > {cat}"
    return cat or seccion or "Catálogo"


def descripcion(prod, tit):
    cat = limpiar_linea(prod.get("categoria") or "")
    tallas = tallas_visibles(prod)
    if tallas:
        primera = (
            f"{tit}, categoría {cat}, disponible en tallas {tallas}."
            if cat
            else f"{tit}, disponible en tallas {tallas}."
        )
    else:
        primera = (
            f"{tit}, categoría {cat}, disponible en {MARCA}."
            if cat
            else f"{tit}, disponible en {MARCA}."
        )
    return limpiar_linea(f"{primera} {ENVIO_TXT}.")


def validar_prohibidas(codigo, campo, texto):
    norm = normalizar(texto)
    for etiqueta, patron in PATRONES_PROHIBIDOS:
        m = patron.search(norm)
        if m:
            sys.exit(
                f"Error: {campo} de {codigo} contiene término prohibido "
                f"({etiqueta}: «{m.group(0)}»): {texto}"
            )


def formatear_precio(prod):
    codigo = prod["codigo"]
    val = prod.get("precio_venta")
    if isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0:
        sys.exit(f"Error: el producto {codigo} no tiene precio_venta válido ({val!r}).")
    entero = int(val)
    if entero != val:
        sys.exit(f"Error: precio_venta de {codigo} debe ser un número entero ({val!r}).")
    return f"{entero} COP"


def resolver_fotos(prod):
    codigo = prod["codigo"]
    imgs = prod.get("imagenes")
    if not isinstance(imgs, list) or not imgs:
        sys.exit(f"Error: el producto {codigo} no tiene imágenes en el catálogo.")

    primera_rel = str(imgs[0]).lstrip("/")
    if not primera_rel or not (RAIZ / primera_rel).is_file():
        sys.exit(f"Error: falta la foto principal en disco de {codigo}: {primera_rel}")
    principal = f"{SITIO}/{quote(primera_rel, safe='/')}"
    # Meta/Google aceptan mejor JPG que WebP: si existe feeds/img/<codigo>.jpg (misma foto principal), se usa.
    if (RAIZ / "feeds" / "img" / f"{codigo}.jpg").is_file():
        principal = f"{SITIO}/feeds/img/{quote(codigo)}.jpg"

    adicionales = []
    vistas = {primera_rel}
    for raw in imgs[1:1 + MAX_FOTOS_ADICIONALES]:
        rel = str(raw).lstrip("/")
        if not rel or rel in vistas:
            continue
        if (RAIZ / rel).is_file():
            vistas.add(rel)
            adicionales.append(f"{SITIO}/{quote(rel, safe='/')}")
            if len(adicionales) == MAX_FOTOS_ADICIONALES:
                break
    return principal, ",".join(adicionales)


def cargar_entradas():
    cat_path = RAIZ / "data" / "catalogo.json"
    perm_path = RAIZ / "scripts" / "productos_permitidos.json"
    if not cat_path.is_file():
        sys.exit(f"Error: no se encontró {cat_path}")
    if not perm_path.is_file():
        sys.exit(f"Error: no se encontró {perm_path}")

    catalogo = json.loads(cat_path.read_text(encoding="utf-8"))
    permitidos = json.loads(perm_path.read_text(encoding="utf-8"))

    if not isinstance(catalogo, list):
        sys.exit("Error: data/catalogo.json debe ser una lista JSON de productos.")
    if not isinstance(permitidos, list) or not permitidos or not all(
        isinstance(c, str) and c.strip() for c in permitidos
    ):
        sys.exit("Error: scripts/productos_permitidos.json debe ser una lista no vacía de códigos.")
    if len(set(permitidos)) != len(permitidos):
        sys.exit("Error: scripts/productos_permitidos.json contiene códigos duplicados.")

    por_codigo = {p["codigo"]: p for p in catalogo if isinstance(p, dict) and p.get("codigo")}
    seleccion = []
    for codigo in permitidos:
        prod = por_codigo.get(codigo)
        if not prod:
            sys.exit(f"Error: el código {codigo} no existe en data/catalogo.json.")
        seleccion.append(prod)
    return seleccion


def construir_registro(prod):
    codigo = prod["codigo"]
    tit = titulo(prod)
    desc = descripcion(prod, tit)
    validar_prohibidas(codigo, "title", tit)
    validar_prohibidas(codigo, "description", desc)

    precio = formatear_precio(prod)
    image_link, additional_image_link = resolver_fotos(prod)
    gender, age_group = genero_y_edad(prod)
    gpc = google_product_category(prod)
    ptype = product_type(prod)
    link = f"{SITIO}/producto/{quote(codigo, safe='')}/"

    base = {
        "id": codigo,
        "title": tit,
        "description": desc,
        "condition": "new",
        "price": precio,
        "link": link,
        "image_link": image_link,
        "brand": MARCA,
        "additional_image_link": additional_image_link,
        "google_product_category": gpc,
        "product_type": ptype,
        "gender": gender,
        "age_group": age_group,
    }
    for k, v in base.items():
        if any(ch in v for ch in ("\t", "\r", "\n")):
            sys.exit(f"Error: campo {k} de {codigo} contiene tab o salto de línea.")
    return base


def escribir_meta_csv(destino, registros):
    with destino.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(META_CAMPOS)
        for reg in registros:
            fila = dict(reg, availability="in stock")
            writer.writerow([fila[c] for c in META_CAMPOS])


def escribir_google_tsv(destino, registros):
    lineas = ["\t".join(GOOGLE_CAMPOS)]
    for reg in registros:
        fila = dict(reg, availability="in_stock", identifier_exists="no", item_group_id="")
        valores = [fila[c] for c in GOOGLE_CAMPOS]
        if any("\t" in v or "\n" in v or "\r" in v for v in valores):
            sys.exit(f"Error: carácter no permitido en TSV para {reg['id']}.")
        lineas.append("\t".join(valores))
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def escribir_readme(destino, registros):
    hoy = date.today().isoformat()
    total = len(registros)
    conteo_sec = {}
    for r in registros:
        sec = r["product_type"].split(" > ")[0]
        conteo_sec[sec] = conteo_sec.get(sec, 0) + 1
    resumen_sec = ", ".join(f"{sec}: {n}" for sec, n in sorted(conteo_sec.items()))

    texto = f"""FEEDS DE CATÁLOGO — SIAVARAN (siavaran.com)
===========================================
Fecha de generación: {hoy}
Total de productos:  {total} ({resumen_sec})

ARCHIVOS GENERADOS
------------------
1. meta-catalogo.csv ({total} productos)
   - Formato: CSV (UTF-8) compatible con Meta Commerce Manager / Instagram Shop.
   - URL esperada al publicar el sitio: {SITIO}/feeds/meta-catalogo.csv
   - Columnas: {", ".join(META_CAMPOS)}

2. google-merchant.tsv ({total} productos)
   - Formato: TSV (UTF-8, separado por tabuladores) para Google Merchant Center.
   - URL esperada al publicar el sitio: {SITIO}/feeds/google-merchant.tsv
   - Columnas: {", ".join(GOOGLE_CAMPOS)}

REQUISITO PREVIO ANTES DE CONECTAR
----------------------------------
Verifica que el sitio publicado responda HTTP 200 en:
- Las páginas de producto: {SITIO}/producto/<codigo>/
- Las fotos del catálogo:  {SITIO}/fotos/<archivo>.webp
- Los dos archivos en:     {SITIO}/feeds/

PASOS MANUALES PARA CONECTAR EN META COMMERCE MANAGER (INSTAGRAM SHOP)
----------------------------------------------------------------------
1. Entra a https://business.facebook.com/commerce/ y selecciona el catálogo de Siavaran
   (o crea uno nuevo de tipo Comercio electrónico).
2. Ve a Catálogo -> Orígenes de datos -> Agregar artículos -> Lista de datos (Data feed).
3. Elige «Usar una URL» (lista programada) y pega:
   {SITIO}/feeds/meta-catalogo.csv
4. Configura la moneda predeterminada en COP (Peso colombiano) y programación diaria.
5. Inicia la carga y revisa la pestaña «Problemas» / diagnósticos para confirmar que
   los {total} productos queden activos sin errores.

PASOS MANUALES PARA CONECTAR EN GOOGLE MERCHANT CENTER
------------------------------------------------------
1. Entra a https://merchants.google.com/ con la cuenta de Siavaran (dominio siavaran.com
   verificado y reclamado).
2. Ve a Productos -> Fuentes de datos -> Agregar fuente de producto.
3. Selecciona «Agregar productos desde un archivo» -> «Introducir un vínculo a tu archivo»
   y pega:
   {SITIO}/feeds/google-merchant.tsv
4. Selecciona país de destino Colombia, idioma Español, moneda COP y programación diaria.
5. Guarda, ejecuta la primera obtención («Actualizar ahora») y revisa Diagnósticos para
   confirmar que los {total} productos se procesen correctamente.

ACTUALIZACIÓN DE LOS FEEDS
--------------------------
Cuando cambie data/catalogo.json o scripts/productos_permitidos.json, corre desde la raíz
del repositorio:
    python3 scripts/generar_feeds.py
y publica la carpeta feeds/ actualizada.
"""
    destino.write_text(texto, encoding="utf-8")


def main():
    productos = cargar_entradas()
    registros = [construir_registro(p) for p in productos]

    feeds_dir = RAIZ / "feeds"
    feeds_dir.mkdir(parents=True, exist_ok=True)

    escribir_meta_csv(feeds_dir / "meta-catalogo.csv", registros)
    escribir_google_tsv(feeds_dir / "google-merchant.tsv", registros)
    escribir_readme(feeds_dir / "README.txt", registros)

    print(
        f"OK: {len(registros)} productos generados en "
        f"feeds/meta-catalogo.csv, feeds/google-merchant.tsv y feeds/README.txt"
    )


if __name__ == "__main__":
    main()
