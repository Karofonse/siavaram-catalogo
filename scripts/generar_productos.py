#!/usr/bin/env python3
"""Genera una página estática por producto limpio (SEO / catálogo) en producto/<codigo>/index.html.

Uso (desde la raíz del repo):  python3 scripts/generar_productos.py

Reglas que respeta el script:
- Solo genera páginas para los códigos listados en scripts/productos_permitidos.json.
- Falla con mensaje claro si algún código no existe en data/catalogo.json, no tiene precio o no tiene foto en disco.
- Nombres, categorías, precios, tallas y fotos salen del catálogo. Nada se inventa.
- Omite por completo cualquier mención de talla cuando es «Talla única» (o U / única).
- Escribe producto/<codigo>/index.html, producto/_indice.json y actualiza sitemap.xml.
"""
import html, json, re, shutil, sys, unicodedata
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent.parent
SITIO = "https://siavaran.com"
WA = "https://wa.me/573106935192"
HOY = "2026-11-21"
TEXTO_ENVIO = "Envíos a toda Colombia; el costo y el tiempo dependen de tu ciudad y te los confirmamos por WhatsApp"


class _ListaPermitidos(set):
    """Conjunto de códigos permitidos que preserva el orden del JSON y también es invocable como función PERMITIDOS()."""

    def __init__(self, codigos=()):
        lista = list(codigos)
        super().__init__(lista)
        self._lista = lista

    def __iter__(self):
        return iter(self._lista)

    def __getitem__(self, idx):
        return self._lista[idx]

    def __call__(self):
        return _cargar_permitidos()


def _cargar_permitidos():
    ruta = RAIZ / "scripts/productos_permitidos.json"
    if not ruta.exists():
        sys.exit(f"Error: no existe la lista de productos permitidos en {ruta}")
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, list) or not datos:
        sys.exit("Error: scripts/productos_permitidos.json debe ser una lista JSON no vacía de códigos")
    vistos = []
    for c in datos:
        c = str(c).strip()
        if c and c not in vistos:
            vistos.append(c)
    return _ListaPermitidos(vistos)


PERMITIDOS = _ListaPermitidos(
    json.loads((RAIZ / "scripts/productos_permitidos.json").read_text(encoding="utf-8"))
    if (RAIZ / "scripts/productos_permitidos.json").exists()
    else []
)


def url_producto(codigo):
    if isinstance(codigo, dict):
        codigo = codigo["codigo"]
    return f"/producto/{str(codigo).strip()}/"


def cop(n):
    return "$ " + f"{int(n):,}".replace(",", ".")


def esc(s):
    return html.escape(str(s), quote=True)


def nombre(x):
    n = x["nombre"]
    if x["codigo"].startswith(("COMBO",)):
        return n
    if re.search(r"mujer|dama", n, re.I):
        return n
    return n + " para mujer"


def es_talla_unica(val):
    n = unicodedata.normalize("NFKD", str(val or ""))
    n = "".join(c for c in n if not unicodedata.combining(c)).strip().lower()
    n = " ".join(n.split())
    return n in {"u", "unica", "talla unica", "talla u"} or "talla unica" in n


def tallas(x):
    t = (x.get("tallas_txt") or "").strip()
    if not t and x.get("tallas"):
        vals = [str(v).strip() for v in x["tallas"] if str(v).strip() and not es_talla_unica(v)]
        t = " · ".join(vals)
    if not t or es_talla_unica(t):
        return ""
    return t


# Solo se usa la foto principal (la que se revisó a mano); las demás no se auditaron.
MINIATURAS = 0

def imagenes_disco(x):
    imgs = [img for img in (x.get("imagenes") or []) if img and (RAIZ / img).exists()]
    return imgs[:5]


def cargar():
    ruta_cat = RAIZ / "data/catalogo.json"
    if not ruta_cat.exists():
        sys.exit(f"Error: no existe {ruta_cat}")
    datos = {x["codigo"]: x for x in json.loads(ruta_cat.read_text(encoding="utf-8")) if "codigo" in x}
    codigos = PERMITIDOS()
    cat = {}
    for c in codigos:
        x = datos.get(c)
        if not x:
            sys.exit(f"Error: el código {c} no existe en data/catalogo.json")
        precio = x.get("precio_venta")
        if precio is None or precio == "" or int(precio) <= 0:
            sys.exit(f"Error: el código {c} no tiene precio válido en data/catalogo.json")
        imgs = x.get("imagenes") or []
        if not imgs or not (RAIZ / imgs[0]).exists():
            sys.exit(f"Error: el código {c} no tiene foto principal en disco")
        cat[c] = x
    return codigos, cat


def wa_producto(x):
    t = tallas(x)
    msg = f"Hola, quiero pedir:\n*{nombre(x)}* (Ref: {x['codigo']})\n"
    if t:
        msg += f"Tallas: {t}\n"
    msg += f"Precio: *{cop(x['precio_venta'])} COP*\n\n¿Está disponible?"
    return f"{WA}?text={quote(msg, safe='')}"


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
  .migas { font-size:13px; color:var(--muted); margin:0 0 14px; }
  .migas a { color:var(--muted); }
  h1 { font-size:clamp(24px,5vw,34px); line-height:1.15; margin:0 0 8px; }
  h2 { font-size:20px; margin:32px 0 10px; }
  p, li { color:var(--txt2); font-size:16px; }
  a { color:var(--pri); }
  .ficha { display:grid; grid-template-columns:1fr; gap:20px; margin:8px 0 28px; }
  @media (min-width:768px) { .ficha { grid-template-columns:minmax(0,1.05fr) minmax(0,1fr); gap:32px; align-items:start; } }
  .foto-principal { width:100%; height:auto; aspect-ratio:3/4; object-fit:cover; object-position:center 20%; display:block; border-radius:14px; border:1px solid var(--bord); background:var(--surf); }
  .miniaturas { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin-top:10px; }
  .miniaturas img { width:100%; height:auto; aspect-ratio:3/4; object-fit:cover; object-position:center 20%; display:block; border-radius:10px; border:1px solid var(--bord); background:var(--surf); }
  .meta-prod { font-size:14px; color:var(--muted); margin:0 0 10px; }
  .precio-ficha { font-size:28px; font-weight:800; color:var(--precio); margin:8px 0 12px; }
  .precio-ficha .moneda { font-size:16px; font-weight:700; color:var(--muted); }
  .tallas-ficha { font-size:15px; color:var(--txt); font-weight:600; margin:0 0 14px; }
  .envio { display:block; background:var(--surf); border:1px solid var(--bord); border-radius:12px; padding:10px 14px; font-size:14px; font-weight:600; color:var(--txt); margin:16px 0; }
  .btn { display:inline-flex; align-items:center; justify-content:center; gap:8px; background:var(--pri); color:#fff; padding:12px 22px; min-height:44px; border-radius:10px; font-weight:700; text-decoration:none; }
  .btn:hover { background:var(--pri-h); }
  .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin:18px 0 8px; padding:0; list-style:none; }
  @media (min-width:700px) { .grid { grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; } }
  @media (min-width:1000px) { .grid { grid-template-columns:repeat(4,minmax(0,1fr)); } }
  .card { background:var(--surf); border:1px solid var(--bord); border-radius:14px; overflow:hidden; display:flex; flex-direction:column; height:100%; }
  .card a.card-link { color:inherit; text-decoration:none; display:flex; flex-direction:column; height:100%; }
  .card img { width:100%; height:auto; aspect-ratio:3/4; object-fit:cover; object-position:center 20%; display:block; background:var(--bord); }
  .card .cuerpo { padding:10px 12px 12px; display:flex; flex-direction:column; gap:4px; flex:1; }
  .card h3 { font-size:14px; line-height:1.3; margin:0; color:var(--txt); font-weight:600; }
  .card a.card-link:hover h3 { color:var(--pri); }
  .card .ref { font-size:12px; color:var(--muted); }
  .card .tallas { font-size:12px; color:var(--muted); }
  .card .precio { font-size:18px; font-weight:800; color:var(--precio); margin-top:auto; padding-top:4px; }
  .caja { background:var(--surf); border:1px solid var(--bord); border-radius:12px; padding:14px 18px; margin:22px 0; max-width:720px; }
  .pasos { max-width:720px; padding-left:22px; }
  .pasos li { margin:6px 0; }
  .cta-final { margin:28px 0 12px; display:flex; flex-wrap:wrap; align-items:center; gap:14px; }
  footer { border-top:1px solid var(--bord); }
  footer .bar { flex-wrap:wrap; gap:8px 18px; font-size:14px; color:var(--muted); }
  footer a { color:var(--muted); }
"""

PIE = """<footer><div class="bar">
  <span>© Siavaran · Envío a toda Colombia</span>
  <a href="/">Catálogo</a>
  <a href="/buscar/">Guías de compra</a>
  <a href="/privacidad.html">Privacidad</a>
  <a href="/terminos.html">Términos y condiciones</a>
  <a href="/cambios.html">Cambios y devoluciones</a>
</div></footer>
</body>
</html>
"""


def cabecera(titulo, desc, canon, og_img, extra_ld, pixel):
    return f"""<!DOCTYPE html>
<html lang="es-CO">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<link rel="icon" href="/logos/logo-siavaran.webp" type="image/webp">
<meta property="og:type" content="product">
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
  <a class="volver" href="/">Volver al catálogo</a>
</div></header>
"""


def descripcion_producto(x):
    nom = nombre(x)
    cat_txt = (x.get("categoria") or "Producto").strip()
    t = tallas(x)
    partes = [f"{nom} (Ref. {x['codigo']}), categoría {cat_txt.lower()}."]
    if t:
        partes.append(f"Tallas: {t}.")
    partes.append(f"Precio: {cop(x['precio_venta'])} COP.")
    partes.append("Pide por WhatsApp con envío a toda Colombia.")
    return " ".join(partes)


def relacionados(x, codigos, cat):
    c = x["codigo"]
    misma_cat = [cat[k] for k in codigos if k != c and cat[k].get("categoria") == x.get("categoria")]
    misma_sec = [
        cat[k]
        for k in codigos
        if k != c and cat[k].get("categoria") != x.get("categoria") and cat[k].get("seccion") == x.get("seccion")
    ]
    otros = [
        cat[k]
        for k in codigos
        if k != c and cat[k].get("categoria") != x.get("categoria") and cat[k].get("seccion") != x.get("seccion")
    ]
    return (misma_cat + misma_sec + otros)[:4]


def pagina_producto(x, codigos, cat, pixel):
    codigo = x["codigo"]
    nom = nombre(x)
    cat_txt = (x.get("categoria") or "Producto").strip()
    titulo = f"{nom} — {cat_txt} | Siavaran"
    desc = descripcion_producto(x)
    canon = f"{SITIO}{url_producto(codigo)}"
    imgs = imagenes_disco(x)
    principal = imgs[0]
    miniaturas = imgs[1:1 + MINIATURAS]
    og_img = f"{SITIO}/{principal}"
    t = tallas(x)
    wa_url = wa_producto(x)

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Product",
                "name": nom,
                "sku": codigo,
                "image": [f"{SITIO}/{img}" for img in imgs[:1 + MINIATURAS]],
                "description": desc,
                "brand": {"@type": "Brand", "name": "Siavaran"},
                "category": cat_txt,
                "offers": {
                    "@type": "Offer",
                    "price": str(int(x["precio_venta"])),
                    "priceCurrency": "COP",
                    "availability": "https://schema.org/InStock",
                    "itemCondition": "https://schema.org/NewCondition",
                    "url": canon,
                    "seller": {"@type": "Organization", "name": "Siavaran"},
                },
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": f"{SITIO}/"},
                    {"@type": "ListItem", "position": 2, "name": "Guías de compra", "item": f"{SITIO}/buscar/"},
                    {"@type": "ListItem", "position": 3, "name": nom, "item": canon},
                ],
            },
        ],
    }

    out = cabecera(titulo, desc, canon, og_img, ld, pixel)
    out += "<main>\n"
    out += f'<p class="migas"><a href="/">Inicio</a> › <a href="/buscar/">Guías de compra</a> › {esc(nom)}</p>\n'
    out += '<div class="ficha">\n'
    out += '  <div class="galeria">\n'
    out += f'    <img class="foto-principal" src="/{principal}" alt="{esc(nom)} — {esc(cat_txt)} (Ref. {esc(codigo)})" width="675" height="900" decoding="async">\n'
    if miniaturas:
        out += '    <div class="miniaturas">\n'
        for idx, img in enumerate(miniaturas, 2):
            out += f'      <img src="/{img}" alt="{esc(nom)} — foto {idx}" width="675" height="900" loading="lazy" decoding="async">\n'
        out += "    </div>\n"
    out += "  </div>\n"
    out += '  <div class="detalle">\n'
    out += f"    <h1>{esc(nom)}</h1>\n"
    out += f'    <p class="meta-prod">Categoría: {esc(cat_txt)} · Ref. {esc(codigo)}</p>\n'
    out += f'    <p class="precio-ficha"><span class="precio">{cop(x["precio_venta"])}</span> <span class="moneda">COP</span></p>\n'
    if t:
        out += f'    <p class="tallas-ficha">Tallas disponibles: {esc(t)}</p>\n'
    out += f'    <p><a class="btn" href="{wa_url}" target="_blank" rel="noopener noreferrer" data-lead="{esc(codigo)}">{WA_SVG}<span>Pedir por WhatsApp</span></a></p>\n'
    out += f'    <p class="envio">{esc(TEXTO_ENVIO)}</p>\n'
    out += "  </div>\n"
    out += "</div>\n"

    out += "<h2>Cómo comprar</h2>\n"
    out += '<ol class="pasos">\n'
    out += "  <li>Escribe por WhatsApp con la referencia: al tocar el botón, el mensaje ya incluye el nombre, el código y el precio.</li>\n"
    out += "  <li>Te confirmamos disponibilidad, el costo y el tiempo de envío según tu ciudad.</li>\n"
    out += "  <li>Pagas por Nequi o transferencia.</li>\n"
    out += "</ol>\n"
    out += "<h2>Cambios</h2>\n"
    out += '<p>¿Algo no te queda? Consulta nuestra política de <a href="/cambios.html">cambios y devoluciones</a>. Todos los precios están en pesos colombianos (COP).</p>\n'

    rels = relacionados(x, codigos, cat)
    out += "<h2>Más como esto</h2>\n"
    out += '<ul class="grid">\n'
    for r in rels:
        r_nom = nombre(r)
        r_t = tallas(r)
        r_url = url_producto(r["codigo"])
        out += f"""<li class="card">
  <a class="card-link" href="{r_url}">
    <img src="/{r['imagenes'][0]}" alt="{esc(r_nom)}" width="675" height="900" loading="lazy" decoding="async">
    <div class="cuerpo">
      <h3>{esc(r_nom)}</h3>
      <span class="ref">Ref. {esc(r['codigo'])}</span>
      {f'<span class="tallas">Talla: {esc(r_t)}</span>' if r_t else ''}
      <span class="precio">{cop(r['precio_venta'])} COP</span>
    </div>
  </a>
</li>
"""
    out += "</ul>\n"
    out += f'<div class="cta-final"><a class="btn" href="{wa_url}" target="_blank" rel="noopener noreferrer" data-lead="{esc(codigo)}">{WA_SVG}<span>Pedir {esc(nom)} por WhatsApp</span></a> <a href="/">Volver al catálogo</a></div>\n'
    out += "</main>\n"
    return out + PIE


def sitemap(codigos):
    p = RAIZ / "sitemap.xml"
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"\s*<url><loc>https://siavaran\.com/producto/.*?</url>", "", t)
    urls = [f"{SITIO}{url_producto(c)}" for c in codigos]
    nuevo = "".join(f"\n  <url><loc>{u}</loc><lastmod>{HOY}</lastmod></url>" for u in urls)
    t = t.replace("\n</urlset>", nuevo + "\n</urlset>")
    p.write_text(t, encoding="utf-8")


def enlazar_index(codigos):
    """Actualiza en index.html el conjunto FICHAS (tarjetas del catálogo que enlazan a /producto/<codigo>/)."""
    p = RAIZ / "index.html"
    s = p.read_text(encoding="utf-8")
    nuevo = "/*FICHAS-INICIO*/const FICHAS = new Set(" + json.dumps(sorted(codigos)) + ");/*FICHAS-FIN*/"
    s2, n = re.subn(r"/\*FICHAS-INICIO\*/.*?/\*FICHAS-FIN\*/", lambda m: nuevo, s, flags=re.S)
    if n != 1:
        sys.exit("No encontré los marcadores FICHAS en index.html")
    p.write_text(s2, encoding="utf-8")


def main():
    codigos, cat = cargar()
    pixel = pixel_bloque()
    destino = RAIZ / "producto"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)
    indice = {}
    for c in codigos:
        d = destino / c
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(pagina_producto(cat[c], codigos, cat, pixel), encoding="utf-8")
        indice[c] = url_producto(c)
    (destino / "_indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sitemap(codigos)
    enlazar_index(codigos)
    print(f"{len(codigos)} páginas de producto generadas en producto/")


if __name__ == "__main__":
    main()
