FEEDS DE CATÁLOGO — SIAVARAN (siavaran.com)
===========================================
Fecha de generación: 2026-11-21
Total de productos:  19 (Perfumes: 5, Ropa: 14)

ARCHIVOS GENERADOS
------------------
1. meta-catalogo.csv (19 productos)
   - Formato: CSV (UTF-8) compatible con Meta Commerce Manager / Instagram Shop.
   - URL esperada al publicar el sitio: https://siavaran.com/feeds/meta-catalogo.csv
   - Columnas: id, title, description, availability, condition, price, link, image_link, brand, additional_image_link, google_product_category, product_type, gender, age_group

2. google-merchant.tsv (19 productos)
   - Formato: TSV (UTF-8, separado por tabuladores) para Google Merchant Center.
   - URL esperada al publicar el sitio: https://siavaran.com/feeds/google-merchant.tsv
   - Columnas: id, title, description, link, image_link, additional_image_link, availability, price, brand, condition, identifier_exists, google_product_category, product_type, gender, age_group, item_group_id

REQUISITO PREVIO ANTES DE CONECTAR
----------------------------------
Verifica que el sitio publicado responda HTTP 200 en:
- Las páginas de producto: https://siavaran.com/producto/<codigo>/
- Las fotos del catálogo:  https://siavaran.com/fotos/<archivo>.webp
- Los dos archivos en:     https://siavaran.com/feeds/

PASOS MANUALES PARA CONECTAR EN META COMMERCE MANAGER (INSTAGRAM SHOP)
----------------------------------------------------------------------
1. Entra a https://business.facebook.com/commerce/ y selecciona el catálogo de Siavaran
   (o crea uno nuevo de tipo Comercio electrónico).
2. Ve a Catálogo -> Orígenes de datos -> Agregar artículos -> Lista de datos (Data feed).
3. Elige «Usar una URL» (lista programada) y pega:
   https://siavaran.com/feeds/meta-catalogo.csv
4. Configura la moneda predeterminada en COP (Peso colombiano) y programación diaria.
5. Inicia la carga y revisa la pestaña «Problemas» / diagnósticos para confirmar que
   los 19 productos queden activos sin errores.

PASOS MANUALES PARA CONECTAR EN GOOGLE MERCHANT CENTER
------------------------------------------------------
1. Entra a https://merchants.google.com/ con la cuenta de Siavaran (dominio siavaran.com
   verificado y reclamado).
2. Ve a Productos -> Fuentes de datos -> Agregar fuente de producto.
3. Selecciona «Agregar productos desde un archivo» -> «Introducir un vínculo a tu archivo»
   y pega:
   https://siavaran.com/feeds/google-merchant.tsv
4. Selecciona país de destino Colombia, idioma Español, moneda COP y programación diaria.
5. Guarda, ejecuta la primera obtención («Actualizar ahora») y revisa Diagnósticos para
   confirmar que los 19 productos se procesen correctamente.

ACTUALIZACIÓN DE LOS FEEDS
--------------------------
Cuando cambie data/catalogo.json o scripts/productos_permitidos.json, corre desde la raíz
del repositorio:
    python3 scripts/generar_feeds.py
y publica la carpeta feeds/ actualizada.
