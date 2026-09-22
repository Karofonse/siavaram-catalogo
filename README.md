# Catálogo de Calzado - Siavaram

Catálogo público estático (HTML + fotos) lista para alojar en tu dominio.

## Estructura

- `index.html` — página con 2.720 productos (zapatos, ropa, perfumes), filtros, fotos, carrito, botón "Comprar por WhatsApp".
- `fotos/` — 943 MB de imágenes optimizadas (900px, JPEG calidad 60).

## Desplegar a tu hosting

### Opción 1: SCP / SSH

```bash
scp -r fotos index.html tu-usuario@siavaram:/var/www/html/
```

### Opción 2: Git (después de crear el repo en GitHub)

```bash
git add .gitignore README.md index.html
git commit -m "Initial: catálogo estático"
git remote add origin https://github.com/tu-usuario/siavaram-catalogo.git
git branch -M main
git push -u origin main
# Luego haz pull en tu servidor
```

### Opción 3: SFTP / FTP

Usa tu cliente FTP (Transmit, Cyberduck, etc.) para subir la carpeta.

## Actualizar el catálogo

Cuando el datalake tenga nuevos productos:

```bash
# En didactic-octo-eureka:
python3 datalake.py unificar datalake/gold --salida tienda --cliente
# Copia tienda/cliente.html y catalogo_clientes/fotos/ a este repo
```

## Estructura esperada en el servidor

```
/var/www/html/siavaram/
├── index.html
└── fotos/
    ├── NIKE-730-01.jpg
    ├── ADIDAS-001-01.jpg
    └── ...
```

La URL será: `https://siavaram/` (o `https://siavaram/catalogo/` si lo montas en una subcarpeta).

## Notas

- **Sin servidor dinámico**: todo es HTML + imágenes estáticas. Muy rápido.
- **Botón "Comprar por WhatsApp"**: prellenable con el código del producto.
- **Responsivo**: optimizado para móviles.
- **Offline**: funciona después del primer load sin red.
