# Diseño: consolidación del repositorio canónico del plugin

Fecha: 2026-08-13

## Objetivo

Convertir `codex_marketplace` en la única fuente de verdad, publicación e
instalación de `professional-growth-coach`, preservando el trabajo público y
las protecciones de seguridad que hoy están divididas entre
`codex_marketplace` y `job_search_coach`.

La consolidación termina cuando el código publicado, el catálogo, la
proveniencia, la caché instalada y la resolución en una tarea nueva apuntan a
una sola identidad canónica. Hasta entonces, `job_search_coach` sigue siendo
una fuente de migración recuperable y no se archiva ni se elimina.

## Estado comprobado

- `job_search_coach` y `codex_marketplace` son repositorios con historias Git
  independientes; no son dos clones sincronizados.
- `codex_marketplace` nació como una publicación sanitizada con un commit raíz
  nuevo y después recibió su propia línea de hardening público.
- `job_search_coach` continuó como repositorio de desarrollo y acumuló cambios
  que no llegaron al marketplace, incluido dossier v2 y una rama no publicada
  de investigación de cinco vacantes.
- La configuración activa habilita dos selectores con el mismo nombre lógico
  de plugin y skills, uno por cada repositorio. Una tarea puede resolver una
  versión distinta de la esperada.
- Ningún árbol es un superconjunto seguro del otro. Los dos contienen controles
  exclusivos que deben conservarse.

## Alternativas consideradas

### 1. Reconciliación curada sobre `codex_marketplace` — elegida

Partir del `origin/main` público y limpio de `codex_marketplace`; portar
funcionalidad y pruebas por lotes temáticos; resolver cada archivo divergente
con revisión explícita; regenerar la proveniencia y publicar una nueva versión
canónica.

Ventajas:

- conserva el historial público sanitizado, `LICENSE`, README, catálogo e
  identidad de instalación;
- evita hacer alcanzable la historia privada o de desarrollo;
- permite unir los controles de seguridad de ambos árboles;
- produce commits revisables y una ruta de rollback clara.

Costo: requiere inventario, reconciliación semántica y gates completos; no es
una copia mecánica.

### 2. `git merge --allow-unrelated-histories` — rechazada

Haría alcanzable desde el repositorio público la historia completa de
desarrollo y sus estados previos a sanitización, produciría conflictos masivos
y mezclaría dos modelos de proveniencia incompatibles.

### 3. Reemplazo total o `rsync --delete` — rechazado

Un reemplazo con `job_search_coach` perdería hardening exclusivo del
marketplace y restauraría nombres/configuración locales. Un reemplazo en la
dirección contraria perdería dossier v2, mejoras recientes de privacidad y el
trabajo de cinco vacantes.

## Decisión de autoridad

Después de la consolidación:

- repositorio fuente y remoto público: `codex_marketplace`;
- rama de publicación: `main` de `codex_marketplace`;
- catálogo: `.agents/plugins/marketplace.json` del marketplace;
- selector instalado: `professional-growth-coach@codex-marketplace-public`;
- directorio fuente del plugin: `plugins/professional-growth-coach` dentro de
  `codex_marketplace`;
- `job_search_coach` no recibe nuevos cambios de producto, releases ni
  attestations.

El repositorio anterior se conserva inicialmente como migración histórica de
solo lectura. Archivarlo en GitHub o eliminar copias locales es una acción
posterior y separada, únicamente después de verificar la nueva publicación y
un respaldo recuperable.

## Baseline y congelamiento

1. Registrar los hashes verificados de ambos `main`, del commit público del
   marketplace y de toda rama no publicada.
2. Congelar cambios funcionales en `job_search_coach` mientras dura la
   reconciliación.
3. Crear y verificar bundles privados de todos los refs de
   `job_search_coach`, de su rama de cinco vacantes y de cualquier lineage
   privado de respaldo.
4. No agregar esos bundles, remotos ni refs al repositorio público.
5. Trabajar en una worktree limpia creada desde `codex_marketplace/origin/main`.

El commit local no publicado de gráficas analíticas del marketplace se revisa
como contenido, no se incorpora automáticamente: sus ejemplos de tres vacantes
y métricas fechadas pueden haber quedado obsoletos frente al contrato nuevo de
cinco vacantes.

## Inventario de migración

La migración usa una lista permitida por ruta y propósito. Cada lote debe
registrar:

- archivo fuente y archivo canónico;
- estado: idéntico, solo desarrollo, solo marketplace o divergente;
- decisión: conservar marketplace, portar desarrollo o reconciliar;
- pruebas que protegen la decisión;
- revisión de privacidad y de datos públicos.

Se excluyen expresamente:

- `.git`, configuración de remotos, ramas y metadatos de worktrees;
- `.release-validation-venv`, `.worktrees`, `.superpowers`, temporales de
  Superdesign, `__pycache__` y archivos compilados;
- cachés instaladas bajo el directorio de Codex;
- artefactos HTML generados en `.professional-growth-coach-artifacts`;
- reportes de revisión privados o ignorados;
- versiones, hashes y attestations anteriores;
- configuración o nombres del marketplace local anterior;
- fixtures o documentos con datos privados, identificadores personales,
  rutas locales o material no aprobado para publicación.

Además del scanner existente, todo archivo tracked nuevo pasa una revisión de
privacidad del release público.

## Orden de reconciliación

### Lote 1: infraestructura de validación y privacidad

Construir primero el superset defensivo y sus pruebas. Se conserva, como
mínimo:

De `job_search_coach`:

- proyección fail-closed de privacidad para dossier v2;
- presupuesto de evaluación de schema, validación de keywords malformadas y
  ciclos de `$ref`;
- diagnósticos sin eco de identificadores, rutas, controles o material del
  candidato;
- guards recientes de recursión e identidad no etiquetada.

De `codex_marketplace`:

- límites directos para estructuras en memoria profundas o cíclicas;
- manejo defensivo de `ValueError` y clasificación de symlinks en componentes
  padre del loader privado;
- límites de profundidad de schema y de longitud/complejidad de expresiones
  regulares.

Los controles se combinan; ninguno sustituye silenciosamente al otro.

### Lote 2: prerequisitos funcionales del dossier v2

Portar schema, compatibilidad, renderer, CSS, validator, fixtures y pruebas de
dossier v2. Conservar el contrato público y la identidad del marketplace.
Revisar que la proyección v2 hacia v1 no oculte texto de los guards semánticos
ni datos del scanner de privacidad.

### Lote 3: investigación de cinco vacantes

Migrar la rama no publicada únicamente después de completar su revisión
pendiente. El lote incluye sus prerequisitos, contratos de cinco empresas,
disponibilidad/fecha de acceso, denominador dinámico, composición del dossier,
accesibilidad y pruebas.

No se publica una feature a medias ni se conservan sus commits de desarrollo
como historia pública. Se porta como cambios curados sobre la base canónica.

### Lote 4: documentación pública y diseño

Reconciliar README, licencia, guías de instalación, skills, referencias y
Superdesign. El marketplace conserva autoridad sobre nombres públicos y
comandos de instalación. Los documentos con cifras o vacantes fechadas se
actualizan o se omiten; no se presentan como estado actual si no se
revalidaron.

## Proveniencia y release

Los commits de `job_search_coach` no resuelven en la historia del marketplace.
Por ello, copiar valores de proveniencia sería inválido.

Después del último commit funcional canónico:

1. regenerar `source_commit` y `source_tree` de fixtures deterministas;
2. ejecutar una sola actualización de versión/cachebuster;
3. instalar exactamente esa versión desde `codex_marketplace`;
4. verificar la misma lista de archivos y bytes entre fuente y caché;
5. calcular y registrar el hash normalizado y conteos;
6. crear una attestation final cuyo padre sea el commit de release;
7. repetir todos los gates desde el HEAD de attestation.

No se modifica la proveniencia para ocultar fallos funcionales ni se consume el
cachebuster antes de que todos los gates previos a release estén verdes, salvo
los fallos de proveniencia explícitamente esperados.

## Configuración e instalación única

La identidad heredada se desactiva solo después de que el release canónico esté
publicado, instalado y comprobado.

Secuencia:

1. crear un respaldo fechado de la configuración activa de Codex;
2. instalar y habilitar la versión exacta de
   `professional-growth-coach@codex-marketplace-public`;
3. comprobar source/cache, smokes instalados y versión;
4. remover el selector heredado con el comando oficial de Codex;
5. comprobar que el selector canónico continúa habilitado;
6. remover el marketplace heredado y su trust stanza exacta;
7. validar el TOML y confirmar que no quedan strings activos del alias anterior;
8. abrir una tarea nueva de Codex y confirmar que expone una sola identidad y
   los skills/version esperados.

Las cachés históricas no se borran manualmente como parte de esta migración.
Cualquier eliminación material será una decisión destructiva independiente.

## Validación

Cada lote exige TDD y revisión independiente. Antes del release final deben
pasar:

1. pruebas enfocadas de cada cambio y compatibilidad v1/v2;
2. profundidad/recursión tanto desde JSON como desde objetos en memoria;
3. schemas malformados, ciclos `$ref`, agotamiento de evaluación y patrones
   excesivos;
4. límites de archivo, descriptor, symlink, hardlink y FIFO;
5. privacidad fail-closed, identidad no etiquetada y diagnósticos sin eco;
6. static/schema/handoff y scanner de privacidad;
7. suite completa del plugin y suite raíz;
8. contratos HTML/CSS, Superdesign, responsive, impresión, forced-colors y
   accesibilidad estática;
9. release validator oficial, `git diff --check` y worktree limpio;
10. paridad source/cache e installed smokes;
11. revisión de todos los archivos públicos tracked;
12. verificación independiente del remoto publicado;
13. smoke en una tarea nueva con exactamente una identidad activa.

La QA visual real en navegador y tecnologías asistivas se informa por separado;
los contratos estáticos no se presentan como evidencia visual empírica.

## Rollback

- Antes de desactivar la identidad heredada, el rollback consiste en volver al
  selector anterior y al bundle privado verificado.
- Después de desactivarla, restaurar primero el respaldo de configuración y
  verificar su parseo; no copiar cachés manualmente.
- Un fallo funcional revierte el commit/lote canónico afectado. No se reabre el
  flujo de publicación desde `job_search_coach`.
- El repositorio anterior no se archiva ni se elimina hasta que la publicación,
  instalación, tarea nueva y respaldo hayan sido verificados de forma
  independiente.

## Criterios de aceptación

1. Todo código y documentación publicada del plugin vive en
   `codex_marketplace`.
2. Las protecciones exclusivas de ambos árboles tienen tests y están presentes
   en el árbol canónico.
3. Dossier v2 y la investigación de cinco vacantes completada funcionan desde
   la instalación canónica.
4. La proveniencia y attestation apuntan a commits/árboles de
   `codex_marketplace` y coinciden con la caché instalada.
5. Los gates definidos pasan sin excepciones no documentadas.
6. El remoto público verificado contiene el release esperado.
7. Una tarea nueva muestra una sola identidad de Professional Growth Coach.
8. `job_search_coach` queda congelado y recuperable, sin ser fuente de
   publicación.

## Fuera de alcance

- Mezclar o publicar la historia completa de `job_search_coach`.
- Borrar repositorios, bundles, cachés o artefactos históricos.
- Modificar LinkedIn, postular a vacantes o realizar acciones externas por el
  candidato.
- Declarar disponibles vacantes no verificadas con fuentes actuales.
- Reescribir funciones no relacionadas con la reconciliación.
