#!/usr/bin/env python3
"""Genera las páginas de búsqueda (SEO programático) de siavaran.com desde data/catalogo.json.

Uso (desde la raíz del repo):  python3 scripts/generar_paginas_busqueda.py

Reglas que respeta el script:
- Solo salen productos de la lista BLANCA (PERMITIDOS): fotos revisadas a mano, sin logos
  ni nombres de marca visibles. Tenis y prendas con marca NO entran.
- Nombres, precios, tallas y fotos salen del catálogo. Nada se inventa.
- Escribe buscar/<slug>/index.html, buscar/index.html (hub) y actualiza sitemap.xml.
"""
import html, json, re, shutil, sys
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent.parent
SITIO = "https://siavaran.com"
WA = "https://wa.me/573106935192"
HOY = "2026-11-21"

# --- Lista blanca: códigos del catálogo con foto sin marca visible (revisión visual) ---
MUJER_ROPA = ["BODY-004", "BODY-005", "BODY-006", "BODY-007", "BODY-008", "BERMUDA-016",
              "JEAN-003", "JEAN-004", "JEAN-005", "JEAN-006", "SUDADERA-010", "PIJAMA-002",
              "CONJUNTO-072", "CONJUNTO-076"]
PERFUME_COMBO = ["COMBO-024", "COMBO-035", "COMBO-036", "COMBO-040", "COMBO-042"]
PERMITIDOS = set(MUJER_ROPA + PERFUME_COMBO)

# --- Páginas ---
# slug, categoria (para el hub), title, h1, description, intro (lista de párrafos),
# consejos (lista de bullets), productos
PAGINAS = [
 dict(slug="ropa-de-mujer-con-envio-a-bogota", grupo="Ropa de mujer",
  title="Ropa de mujer con envío a Bogotá | Siavaran",
  h1="Ropa de mujer con envío a Bogotá",
  desc="Bodys, jeans, conjuntos y pijama para mujer con envío a Bogotá. Mira fotos y precios y pide por WhatsApp; te confirmamos el tiempo y el costo según tu ciudad.",
  intro=["Si vives en Bogotá y quieres ropa de mujer sin salir a recorrer centros comerciales, aquí tienes una selección de nuestro catálogo: bodys, jeans, un conjunto de manga larga y una pijama.",
         "Tú eliges por foto, nos escribes por WhatsApp con tu talla y coordinamos el pago por Nequi o transferencia. Al pedirlo te confirmamos el tiempo y el costo de envío según tu ciudad."],
  consejos=["Para las capas de una ciudad de clima cambiante, el conjunto de manga larga y los jeans combinan fácil con un body básico.",
            "Escríbenos con tu talla habitual o tus medidas y te ayudamos a escoger."],
  prods=["BODY-006","JEAN-003","CONJUNTO-076","BODY-004","JEAN-005","SUDADERA-010","BODY-007","PIJAMA-002"]),
 dict(slug="ropa-de-mujer-con-envio-a-medellin", grupo="Ropa de mujer",
  title="Ropa de mujer con envío a Medellín | Siavaran",
  h1="Ropa de mujer con envío a Medellín",
  desc="Ropa de mujer para Medellín: bodys, jeans, shorts de jean y conjuntos. Pide fácil por WhatsApp; te confirmamos el tiempo y el costo de envío según tu ciudad.",
  intro=["¿Buscas ropa de mujer y estás en Medellín? Reunimos prendas de nuestro catálogo que puedes pedir desde el celular: bodys, jeans, un short de jean y conjuntos cómodos.",
         "Escribes por WhatsApp, confirmamos disponibilidad y pagas por Nequi o transferencia. Al pedirlo te confirmamos el tiempo y el costo de envío según tu ciudad. Si no te queda la talla, puedes pedir el cambio por el mismo chat."],
  consejos=["Cada prenda muestra su referencia: mándanos la que te guste y te confirmamos tallas disponibles.",
            "Pagas por Nequi o transferencia, sin pasarelas ni registros."],
  prods=["BODY-005","JEAN-004","CONJUNTO-072","BODY-008","BERMUDA-016","JEAN-006","CONJUNTO-076","BODY-007"]),
 dict(slug="ropa-de-mujer-con-envio-a-cali", grupo="Ropa de mujer",
  title="Ropa de mujer con envío a Cali | Siavaran",
  h1="Ropa de mujer con envío a Cali",
  desc="Compra ropa de mujer desde Cali: short de jean, bodys, jeans y pijama. Pide por WhatsApp; te confirmamos el tiempo y el costo de envío según tu ciudad.",
  intro=["Para quienes compran desde Cali: prendas de mujer de nuestro catálogo, con fotos reales y precio visible, para que decidas sin vueltas.",
         "Cuando elijas, tocas el botón de WhatsApp y te respondemos con disponibilidad, forma de pago, y el tiempo y el costo de envío según tu ciudad."],
  consejos=["En una ciudad calurosa como Cali, el short de jean, los bodys y la pijama son las opciones más frescas de esta lista.",
            "Si tienes dudas con la talla, te asesoramos por WhatsApp antes de que pagues."],
  prods=["BERMUDA-016","BODY-004","JEAN-006","PIJAMA-002","BODY-006","CONJUNTO-072","JEAN-003","SUDADERA-010"]),
 dict(slug="ropa-de-mujer-con-envio-a-barranquilla", grupo="Ropa de mujer",
  title="Ropa de mujer con envío a Barranquilla | Siavaran",
  h1="Ropa de mujer con envío a Barranquilla",
  desc="Ropa de mujer con envío a Barranquilla: short de jean, bodys, jeans y conjuntos. Pide por WhatsApp; te confirmamos el tiempo y el costo según tu ciudad.",
  intro=["Si estás en Barranquilla y quieres renovar tu clóset, mira esta selección de ropa de mujer de nuestro catálogo, con foto y precio de cada prenda.",
         "Escribes por WhatsApp, confirmamos disponibilidad y pagas por Nequi o transferencia. Al pedirlo te confirmamos el tiempo y el costo de envío según tu ciudad."],
  consejos=["Para el calor de la costa, mira el short de jean, los bodys y la pijama.",
            "Los jeans y el conjunto de manga larga son buenos para salir de noche o para viajar."],
  prods=["BERMUDA-016","BODY-008","JEAN-005","BODY-005","PIJAMA-002","BODY-004","JEAN-004","CONJUNTO-076"]),
 dict(slug="ropa-de-mujer-con-envio-a-toda-colombia", grupo="Ropa de mujer",
  title="Ropa de mujer con envío a toda Colombia | Siavaran",
  h1="Ropa de mujer con envío a toda Colombia",
  desc="Ropa de mujer con envío a todo el país: bodys, jeans, short de jean, conjuntos y pijama. Fotos reales, precios claros y pedido por WhatsApp.",
  intro=["Toda la ropa de mujer de esta página se envía a cualquier ciudad de Colombia. Al pedirlo te confirmamos el tiempo y el costo según tu ciudad.",
         "Ves la foto y el precio, nos escribes por WhatsApp y pagas por Nequi o transferencia. Así de simple."],
  consejos=["Tienes cambios por talla: escríbenos por WhatsApp y lo coordinamos (mira la política de cambios abajo).",
            "Todos los precios están en pesos colombianos (COP)."],
  prods=MUJER_ROPA),
 dict(slug="jeans-para-mujer", grupo="Ropa de mujer",
  title="Jeans para mujer: precios y envío a Colombia | Siavaran",
  h1="Jeans para mujer",
  desc="Jeans y short de jean para mujer con precio y foto reales. Envío a toda Colombia; te confirmamos el tiempo y el costo según tu ciudad. Pide por WhatsApp.",
  intro=["Jeans de nuestro catálogo: dos ajustados, dos baggy (uno negro y otro con rasgados) y un short de jean rasgado. Cada uno con su foto, su referencia y su precio.",
         "Pide por WhatsApp con tu talla habitual o tus medidas, y te decimos qué tallas hay."],
  consejos=["Para jeans, lo más fiable es que nos des tus medidas de cintura y cadera: así evitamos cambios.",
            "Al pedirlo te confirmamos el tiempo y el costo de envío según tu ciudad."],
  prods=["JEAN-003","JEAN-004","JEAN-005","JEAN-006","BERMUDA-016"]),
 dict(slug="bodys-para-mujer", grupo="Ropa de mujer",
  title="Bodys para mujer: negro, de malla y más | Siavaran",
  h1="Bodys para mujer",
  desc="Bodys para mujer: básico negro, de malla, halter y más. Fotos reales, precio visible y envío a toda Colombia. Pide por WhatsApp.",
  intro=["Un body es de las prendas más fáciles de combinar: con jeans, con falda o con un pantalón de vestir. Estos son los bodys que tenemos ahora en el catálogo.",
         "Hay uno básico negro, uno de malla, uno con espalda abierta y otros con detalles. Algunos vienen en talla única; en los demás te confirmamos tallas por WhatsApp."],
  consejos=["Mira la talla indicada en cada tarjeta: si dice talla única, se adapta a varias medidas.",
            "Te confirmamos el tiempo y el costo de envío según tu ciudad. Cambios por talla, escribiéndonos por WhatsApp."],
  prods=["BODY-007","BODY-006","BODY-005","BODY-004","BODY-008"]),
 dict(slug="ropa-comoda-para-mujer", grupo="Ropa de mujer",
  title="Ropa cómoda para mujer: conjuntos, sudadera y pijama | Siavaran",
  h1="Ropa cómoda para mujer",
  desc="Conjuntos de manga larga y de pantalón de lunares, sudadera ancha y pijama para mujer. Envío a toda Colombia; te confirmamos el tiempo y el costo según tu ciudad. Pide por WhatsApp.",
  intro=["Para estar en casa, viajar o ir a la universidad sin sentirte incómoda: un conjunto de manga larga, un conjunto con pantalón de lunares y camiseta estampada, una sudadera de corte ancho y una pijama.",
         "Todo con foto real y precio visible. Pides por WhatsApp y te lo enviamos a tu casa; te confirmamos el tiempo y el costo según tu ciudad."],
  consejos=["El conjunto de manga larga y la pijama vienen en talla única; en los demás te confirmamos tallas por WhatsApp.",
            "Si dudas entre dos opciones, mándanos las fotos por WhatsApp y te ayudamos a decidir."],
  prods=["CONJUNTO-076","CONJUNTO-072","SUDADERA-010","PIJAMA-002"]),
 dict(slug="perfume-para-regalo", grupo="Perfumes y regalos",
  title="Perfume para regalo: combos con envío a Colombia | Siavaran",
  h1="Perfume para regalo",
  desc="Combos de perfume con cuidado corporal listos para regalar: caja, bolsa o moño. Precio visible y envío a toda Colombia. Pide por WhatsApp.",
  intro=["Un combo de perfume con body splash o crema es un regalo que casi nunca falla. Estos vienen en caja o en bolsa de regalo con moño, listos para entregar.",
         "Elige el que prefieras, escríbenos por WhatsApp y te contamos qué incluye cada combo y si está disponible."],
  consejos=["Si es para otra persona, cuéntanos cómo es y te recomendamos uno.",
            "Al pedirlo te confirmamos el tiempo y el costo de envío según tu ciudad."],
  prods=["COMBO-024","COMBO-035","COMBO-036","COMBO-040","COMBO-042"]),
 dict(slug="perfume-para-regalo-en-bogota", grupo="Perfumes y regalos",
  title="Perfume para regalo con envío a Bogotá | Siavaran",
  h1="Perfume para regalo con envío a Bogotá",
  desc="Combos de perfume y body splash para regalar en Bogotá. Te confirmamos el tiempo y el costo de envío según tu ciudad. Precio visible y pedido por WhatsApp.",
  intro=["¿Necesitas un regalo en Bogotá y no quieres complicarte? Mira estos combos de perfume con cuidado corporal, con su empaque de regalo.",
         "Te lo enviamos a Bogotá; al pedirlo te confirmamos el tiempo y el costo según tu ciudad. Puedes pedir que llegue directamente a la persona que va a recibirlo."],
  consejos=["Dinos la dirección de entrega al escribirnos por WhatsApp.",
            "Pide con unos días de anticipación si es para una fecha puntual."],
  prods=["COMBO-024","COMBO-035","COMBO-036","COMBO-042"]),
 dict(slug="perfume-para-regalo-en-medellin", grupo="Perfumes y regalos",
  title="Perfume para regalo con envío a Medellín | Siavaran",
  h1="Perfume para regalo con envío a Medellín",
  desc="Combos de perfume y cuidado corporal para regalar en Medellín. Te confirmamos el tiempo y el costo de envío según tu ciudad. Pide por WhatsApp.",
  intro=["Si el regalo es para alguien en Medellín, estos combos de perfume con body splash o crema son una opción práctica: ya vienen empacados.",
         "Al pedirlo te confirmamos el tiempo y el costo de envío según tu ciudad."],
  consejos=["Escríbenos por WhatsApp y confirmamos qué trae cada combo.",
            "Pagas por Nequi o transferencia."],
  prods=["COMBO-036","COMBO-040","COMBO-042","COMBO-035"]),
 dict(slug="combos-de-perfume-y-body-splash", grupo="Perfumes y regalos",
  title="Combos de perfume y body splash | Siavaran",
  h1="Combos de perfume y body splash",
  desc="Combos de perfume con body splash o crema corporal: el set completo en una caja o bolsa. Precio visible y envío a Colombia.",
  intro=["En vez de comprar el perfume y el body splash por separado, un combo te da ambos en un solo pedido, y se ve bien al regalarlo.",
         "Los precios están a la vista. Si quieres saber qué incluye cada uno, escríbenos por WhatsApp."],
  consejos=["Cada tarjeta muestra la referencia del combo.",
            "Al pedirlo te confirmamos el tiempo y el costo de envío según tu ciudad."],
  prods=["COMBO-042","COMBO-040","COMBO-036","COMBO-035"]),
 dict(slug="regalos-para-mujer", grupo="Perfumes y regalos",
  title="Regalos para mujer: perfumes, bodys y pijama | Siavaran",
  h1="Regalos para mujer",
  desc="Ideas de regalo para mujer: combos de perfume, bodys y pijama, con foto, precio y envío a toda Colombia. Pide por WhatsApp.",
  intro=["Si no sabes qué regalar, aquí hay dos opciones seguras: un combo de perfume con cuidado corporal, o una prenda bonita como un body o una pijama.",
         "Todo tiene precio visible. Escríbenos por WhatsApp, cuéntanos para quién es y te ayudamos a elegir."],
  consejos=["Para ropa necesitamos la talla; para los combos de perfume no.",
            "Al pedirlo te confirmamos el tiempo y el costo de envío según tu ciudad."],
  prods=["COMBO-024","BODY-005","COMBO-035","PIJAMA-002","COMBO-042","BODY-006"]),
 dict(slug="regalos-de-navidad-para-mujer", grupo="Perfumes y regalos",
  title="Regalos de Navidad para mujer | Siavaran",
  h1="Regalos de Navidad para mujer",
  desc="Ideas de regalo de Navidad para mujer: combos de perfume, pijama, bodys y conjuntos. Envío a Colombia; te confirmamos el tiempo y el costo según tu ciudad.",
  intro=["Si estás armando tu lista de Navidad, esta selección te adelanta el trabajo: combos de perfume en empaque de regalo, una pijama y prendas para estrenar.",
         "Pide con tiempo: al escribirnos te confirmamos el tiempo de envío según tu ciudad, y así evitas el afán de última hora."],
  consejos=["Escríbenos por WhatsApp con la dirección y la fecha en que la necesitas.",
            "Si el regalo es ropa, ten la talla a la mano; si no la sabes, los combos de perfume no la necesitan."],
  prods=["COMBO-036","COMBO-024","PIJAMA-002","BODY-006","COMBO-040","CONJUNTO-076"]),
]

def cop(n):
    return "$ " + f"{int(n):,}".replace(",", ".")

def esc(s):
    return html.escape(s, quote=True)

def cargar():
    datos = {x["codigo"]: x for x in json.load(open(RAIZ / "data/catalogo.json", encoding="utf-8"))}
    cat = {}
    for c in PERMITIDOS:
        x = datos.get(c)
        if not x or not x.get("precio_venta") or not x.get("imagenes"):
            sys.exit(f"Producto no válido en el catálogo: {c}")
        if not (RAIZ / x["imagenes"][0]).exists():
            sys.exit(f"Falta la foto de {c}")
        cat[c] = x
    return cat

def nombre(x):
    n = x["nombre"]
    if x["codigo"].startswith(("COMBO",)):
        return n
    if re.search(r"mujer|dama", n, re.I):
        return n
    return n + " para mujer"

def tallas(x):
    if x.get("tallas_txt"):
        return x["tallas_txt"]
    return ""

def wa_producto(x):
    t = tallas(x)
    msg = f"Hola, quiero pedir:\n*{nombre(x)}* (Ref: {x['codigo']})\n"
    if t:
        msg += f"Tallas: {t}\n"
    msg += f"Precio: *{cop(x['precio_venta'])} COP*\n\n¿Está disponible?"
    return f"{WA}?text={quote(msg, safe='')}"

def wa_pagina(p):
    return f"{WA}?text={quote('Hola Siavaran, vi la página «' + p['h1'] + '» y quiero ver más opciones.', safe='')}"

def pixel_bloque():
    t = (RAIZ / "index.html").read_text(encoding="utf-8")
    m = re.search(r"<!-- Meta Pixel.*?</script>", t, re.S)
    if not m:
        sys.exit("No encontré el bloque del Pixel en index.html")
    return m.group(0)

WA_SVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/></svg>'

CSS = """
  :root { --bg:#ffffff; --surf:#f5f5f0; --bord:#e8e4de; --txt:#1a1209; --txt2:#4a3f30; --muted:#7a6e5f; --pri:#ff5420; --pri-h:#e0451a; --precio:#059669; }
  @media (prefers-color-scheme: dark) { :root { --bg:#0c0b09; --surf:#161512; --bord:#2a2722; --txt:#f5f1ea; --txt2:#d5cdc0; --muted:#9a9082; --precio:#34d399; } }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--txt); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; line-height:1.6; }
  header { border-bottom:1px solid var(--bord); }
  .bar { max-width:1100px; margin:0 auto; padding:12px 16px; display:flex; align-items:center; gap:10px; }
  .bar img { width:40px; height:40px; object-fit:contain; display:block; }
  .bar a.marca { color:var(--txt); font-weight:800; text-decoration:none; font-size:18px; }
  .bar a.volver { margin-left:auto; color:var(--pri); font-weight:700; text-decoration:none; font-size:14px; text-align:right; }
  main { max-width:1100px; margin:0 auto; padding:20px 16px 48px; }
  .migas { font-size:13px; color:var(--muted); margin:0 0 10px; }
  .migas a { color:var(--muted); }
  h1 { font-size:clamp(24px,5vw,36px); line-height:1.15; margin:0 0 12px; }
  h2 { font-size:20px; margin:32px 0 10px; }
  p, li { color:var(--txt2); font-size:16px; }
  .intro { max-width:720px; }
  .intro p { margin:0 0 10px; }
  .envio { display:inline-block; background:var(--surf); border:1px solid var(--bord); border-radius:999px; padding:6px 14px; font-size:13px; font-weight:700; color:var(--txt); margin:4px 0 14px; }
  a { color:var(--pri); }
  .btn { display:inline-flex; align-items:center; justify-content:center; gap:8px; background:var(--pri); color:#fff; padding:12px 22px; min-height:44px; border-radius:10px; font-weight:700; text-decoration:none; }
  .btn:hover { background:var(--pri-h); }
  .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin:18px 0 8px; padding:0; list-style:none; }
  @media (min-width:700px) { .grid { grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; } }
  @media (min-width:1000px) { .grid { grid-template-columns:repeat(4,minmax(0,1fr)); } }
  .card { background:var(--surf); border:1px solid var(--bord); border-radius:14px; overflow:hidden; display:flex; flex-direction:column; height:100%; }
  .card img { width:100%; height:auto; aspect-ratio:3/4; object-fit:cover; object-position:center 20%; display:block; background:var(--bord); }
  .card .cuerpo { padding:10px 12px 12px; display:flex; flex-direction:column; gap:4px; flex:1; }
  .card h3 { font-size:14px; line-height:1.3; margin:0; color:var(--txt); font-weight:600; }
  .card .ref { font-size:12px; color:var(--muted); }
  .card .tallas { font-size:12px; color:var(--muted); }
  .card .precio { font-size:18px; font-weight:800; color:var(--precio); margin-top:2px; }
  .card .btn { margin-top:auto; padding:9px 10px; min-height:42px; font-size:13px; border-radius:8px; }
  .caja { background:var(--surf); border:1px solid var(--bord); border-radius:12px; padding:14px 18px; margin:22px 0; max-width:720px; }
  .caja ul { margin:6px 0 0; padding-left:20px; }
  .caja li { margin:4px 0; }
  .pasos { max-width:720px; padding-left:22px; }
  .pasos li { margin:6px 0; }
  .relacionadas { display:flex; flex-wrap:wrap; gap:8px 14px; padding:0; list-style:none; }
  .relacionadas a { font-weight:600; }
  footer { border-top:1px solid var(--bord); }
  footer .bar { flex-wrap:wrap; gap:8px 18px; font-size:14px; color:var(--muted); }
  footer a { color:var(--muted); }
"""

def cabecera(titulo, desc, canon, og_img, extra_ld, pixel):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<link rel="icon" href="/logos/logo-siavaran.webp" type="image/webp">
<meta property="og:type" content="website">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{og_img}">
<meta property="og:locale" content="es_CO">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(titulo)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{og_img}">
{pixel}
<script type="application/ld+json">
{json.dumps(extra_ld, ensure_ascii=False, indent=2)}
</script>
<style>{CSS}</style>
</head>
<body>
<header><div class="bar">
  <img src="/logos/logo-siavaran.webp" alt="Siavaran" width="40" height="40">
  <a class="marca" href="/">Siavaran</a>
  <a class="volver" href="/">Ver toda la tienda →</a>
</div></header>
"""

PIE = """<footer><div class="bar">
  <span>© Siavaran · Envío a toda Colombia</span>
  <a href="/buscar/">Guías de compra</a>
  <a href="/privacidad.html">Privacidad</a>
  <a href="/terminos.html">Términos y condiciones</a>
  <a href="/cambios.html">Cambios y devoluciones</a>
</div></footer>
</body>
</html>
"""

def pagina(p, cat, pixel, todas):
    url = f"{SITIO}/buscar/{p['slug']}/"
    prods = [cat[c] for c in p["prods"]]
    ld_items = []
    for i, x in enumerate(prods, 1):
        ld_items.append({
            "@type": "ListItem", "position": i,
            "item": {
                "@type": "Product", "name": nombre(x), "sku": x["codigo"],
                "image": f"{SITIO}/{x['imagenes'][0]}",
                "url": f"{url}#{x['codigo']}",
                "offers": {"@type": "Offer", "price": str(int(x["precio_venta"])), "priceCurrency": "COP",
                           "url": f"{url}#{x['codigo']}",
                           "seller": {"@type": "Organization", "name": "Siavaran"}},
            }})
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": url, "url": url, "name": p["h1"], "description": p["desc"],
         "inLanguage": "es-CO", "isPartOf": {"@type": "WebSite", "name": "Siavaran", "url": SITIO + "/"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Siavaran", "item": SITIO + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guías de compra", "item": SITIO + "/buscar/"},
            {"@type": "ListItem", "position": 3, "name": p["h1"], "item": url}]},
        {"@type": "ItemList", "name": p["h1"], "numberOfItems": len(ld_items), "itemListElement": ld_items},
    ]}
    og = f"{SITIO}/{prods[0]['imagenes'][0]}"
    out = cabecera(p["title"], p["desc"], url, og, ld, pixel)
    out += '<main>\n'
    out += f'<p class="migas"><a href="/">Inicio</a> › <a href="/buscar/">Guías de compra</a> › {esc(p["h1"])}</p>\n'
    out += f'<h1>{esc(p["h1"])}</h1>\n<div class="intro">\n'
    for par in p["intro"]:
        out += f'  <p>{esc(par)}</p>\n'
    out += '</div>\n<span class="envio">Te confirmamos el tiempo y el costo de envío según tu ciudad</span>\n'
    out += '<ul class="grid">\n'
    for i, x in enumerate(prods):
        t = tallas(x)
        lazy = 'eager' if i < 2 else 'lazy'
        out += f'''<li class="card" id="{x['codigo']}">
  <img src="/{x['imagenes'][0]}" alt="{esc(nombre(x))}" width="675" height="900" loading="{lazy}" decoding="async">
  <div class="cuerpo">
    <h3>{esc(nombre(x))}</h3>
    <span class="ref">Ref. {x['codigo']}</span>
    {f'<span class="tallas">Talla: {esc(t)}</span>' if t else ''}
    <span class="precio">{cop(x['precio_venta'])}</span>
    <a class="btn" href="{wa_producto(x)}" target="_blank" rel="noopener noreferrer" data-lead="{x['codigo']}">{WA_SVG}<span>Pedir por WhatsApp</span></a>
  </div>
</li>
'''
    out += '</ul>\n'
    out += '<p><a class="btn" href="' + wa_pagina(p) + '" target="_blank" rel="noopener noreferrer" data-lead="busqueda-' + p["slug"] + '">' + WA_SVG + '<span>Escríbenos por WhatsApp</span></a></p>\n'
    out += '<div class="caja"><strong>Para tener en cuenta</strong><ul>\n'
    for c in p["consejos"]:
        out += f'  <li>{esc(c)}</li>\n'
    out += '</ul></div>\n'
    out += '<h2>Cómo pedir</h2>\n<ol class="pasos">\n  <li>Elige la prenda y toca «Pedir por WhatsApp»: el mensaje ya sale con la referencia y el precio.</li>\n  <li>Te confirmamos disponibilidad y talla.</li>\n  <li>Pagas por Nequi o transferencia. Al escribirnos te confirmamos el tiempo y el costo de envío según tu ciudad.</li>\n</ol>\n'
    out += '<p>¿Algo no te queda? Lee nuestra política de <a href="/cambios.html">cambios y devoluciones</a>. Los precios son en pesos colombianos (COP).</p>\n'
    rel = [q for q in todas if q["slug"] != p["slug"] and q["grupo"] == p["grupo"]][:6]
    out += '<h2>Más guías</h2>\n<ul class="relacionadas">\n'
    for q in rel:
        out += f'  <li><a href="/buscar/{q["slug"]}/">{esc(q["h1"])}</a></li>\n'
    out += '  <li><a href="/buscar/">Ver todas las guías</a></li>\n</ul>\n</main>\n'
    return out + PIE

def hub(cat, pixel):
    url = f"{SITIO}/buscar/"
    titulo = "Guías de compra: ropa de mujer y regalos | Siavaran"
    desc = "Guías de compra de Siavaran: ropa de mujer por ciudad, jeans, bodys, perfumes y regalos con precio y envío a toda Colombia."
    items = [{"@type": "ListItem", "position": i, "url": f"{SITIO}/buscar/{p['slug']}/", "name": p["h1"]}
             for i, p in enumerate(PAGINAS, 1)]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": url, "url": url, "name": titulo, "description": desc, "inLanguage": "es-CO"},
        {"@type": "ItemList", "name": "Guías de compra", "numberOfItems": len(items), "itemListElement": items}]}
    out = cabecera(titulo, desc, url, f"{SITIO}/assets/editorial/og-portada.jpg", ld, pixel)
    out += '<main>\n<p class="migas"><a href="/">Inicio</a> › Guías de compra</p>\n<h1>Guías de compra</h1>\n'
    out += '<div class="intro"><p>Estas guías reúnen productos reales de nuestro catálogo según lo que más buscan nuestras clientas: ropa de mujer en tu ciudad, jeans, bodys, perfumes y regalos.</p><p>Todo con foto, precio visible y envío a toda Colombia. Al pedirlo te confirmamos el tiempo y el costo según tu ciudad. Pides por WhatsApp y pagas por Nequi o transferencia.</p></div>\n'
    for g in ["Ropa de mujer", "Perfumes y regalos"]:
        out += f'<h2>{g}</h2>\n<ul class="relacionadas" style="flex-direction:column">\n'
        for p in PAGINAS:
            if p["grupo"] == g:
                out += f'  <li><a href="/buscar/{p["slug"]}/">{esc(p["h1"])}</a> <span class="ref" style="color:var(--muted);font-size:13px">· {len(p["prods"])} productos</span></li>\n'
        out += '</ul>\n'
    out += '<p style="margin-top:24px"><a class="btn" href="/">Ver toda la tienda</a></p>\n</main>\n'
    return out + PIE


SLUG_ANTIGUO = "ropa-de-mujer-envio-gratis-colombia"
SLUG_NUEVO = "ropa-de-mujer-con-envio-a-toda-colombia"

def escribir_redireccion(destino):
    """Mantiene la URL vieja (con 'gratis') y la manda a la página nueva."""
    destino_url = f"/buscar/{SLUG_NUEVO}/"
    canon = f"{SITIO}{destino_url}"
    d = destino / SLUG_ANTIGUO
    d.mkdir(parents=True)
    (d / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Redirigiendo… | Siavaran</title>
<link rel="canonical" href="{canon}">
<meta name="robots" content="noindex, follow">
<meta http-equiv="refresh" content="0;url={destino_url}">
<script>location.replace({destino_url!r});</script>
</head>
<body>
<p>Esta página se mudó. <a href="{destino_url}">Ir a Ropa de mujer con envío a toda Colombia</a>.</p>
</body>
</html>
""", encoding="utf-8")

def sitemap():
    p = RAIZ / "sitemap.xml"
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"\s*<url><loc>https://siavaran\.com/buscar/.*?</url>", "", t)
    urls = [f"{SITIO}/buscar/"] + [f"{SITIO}/buscar/{q['slug']}/" for q in PAGINAS]
    nuevo = "".join(f"\n  <url><loc>{u}</loc><lastmod>{HOY}</lastmod></url>" for u in urls)
    t = t.replace("\n</urlset>", nuevo + "\n</urlset>")
    p.write_text(t, encoding="utf-8")

def main():
    cat = cargar()
    pixel = pixel_bloque()
    for p in PAGINAS:
        assert set(p["prods"]) <= PERMITIDOS, p["slug"]
        assert 4 <= len(p["prods"]) <= 14, p["slug"]
    destino = RAIZ / "buscar"
    if destino.exists():
        shutil.rmtree(destino)
    for p in PAGINAS:
        d = destino / p["slug"]
        d.mkdir(parents=True)
        (d / "index.html").write_text(pagina(p, cat, pixel, PAGINAS), encoding="utf-8")
    (destino / "index.html").write_text(hub(cat, pixel), encoding="utf-8")
    escribir_redireccion(destino)
    sitemap()
    print(f"{len(PAGINAS)} páginas + hub generados en buscar/")

if __name__ == "__main__":
    main()
