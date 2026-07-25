# data/

Capas locales congeladas. **No versionar los microdatos crudos**, solo la
estructura (ver `.gitignore`).

- `raw/`       — capas geo descargadas y congeladas el día 1 (DANE MGN, CNPV,
                 catastro, SNIES). Verificar rutas y formatos el día 1.
- `donor/`     — microdatos IEFIC + ENPH armonizados a UN año.
- `synthetic/` — 2.000 afiliados con 36 meses de eventos generados con hazard
                 conocido (verdad de campo).
