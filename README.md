# Catálogo Web — Siavaran (siavaran.com)

Sitio público estático de **Siavaran** (`https://siavaran.com/`), publicado directamente desde la rama `main` mediante **GitHub Pages**.

## Estructura

- `index.html` — portada editorial (ropa de mujer y perfumes destacados) y catálogo interactivo con filtros, favoritos y pedido directo por WhatsApp.
- `envios.html`, `cambios.html`, `privacidad.html`, `terminos.html` — páginas informativas y legales.
- `data/catalogo.json` — datos del catálogo público saneados (sin costos ni datos internos de proveedores).
- `fotos/` — imágenes WebP de los productos (`fotos/thumbs/` contiene miniaturas de 360 px para las tarjetas destacadas de portada).
- `logos/` y `assets/` — recursos gráficos de la tienda.
- `robots.txt` y `sitemap.xml` — indexación SEO.

## Publicación (GitHub Pages)

El sitio se sirve como HTML estático puro desde GitHub Pages (rama `main`, dominio `siavaran.com` configurado en `CNAME`). No utiliza `package.json`, bundler ni pasos de compilación (`npm run build`).

## Actualizar el catálogo

Este `index.html` contiene el diseño de la tienda. Cuando el datalake tenga productos nuevos, actualiza `data/catalogo.json` y las tarjetas destacadas de portada con los scripts incluidos:

```bash
# 1. Sanear el catálogo público (elimina costos, márgenes y datos de proveedor):
python3 scripts/sanear_catalogo_publico.py

# 2. Regenerar las tarjetas estáticas destacadas de portada en index.html:
python3 scripts/generar_portada.py
```

## Compatibilidad de `localStorage`

En `index.html` se conservan deliberadamente las claves históricas de `localStorage`:
- `calzado_favs` — lista de códigos marcados como favoritos por la usuaria.
- `calzado_theme` — preferencia de tema claro/oscuro (`light` / `dark`).
- `calzado_seccion` — última sección consultada en el catálogo.

**Nota:** No renombrar estas claves para no borrar los favoritos ni las preferencias guardadas en los navegadores de las clientas actuales.
