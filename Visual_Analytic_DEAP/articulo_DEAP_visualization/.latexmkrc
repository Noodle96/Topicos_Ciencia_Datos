# Archivo de configuración de latexmk (NO es plantilla ni contenido del
# artículo -- solo le dice a BibTeX/pdflatex dónde buscar archivos cuando
# se compila con -outdir=build).
#
# Problema que resuelve (2026-07-22, diagnosticado con el log de LaTeX
# Workshop): al compilar con -outdir=build, BibTeX no encuentra jaes.bst ni
# jaes.bib ("Cannot resolve file jaes.bst"), y como BibTeX no tiene un modo
# "nonstopmode" real, ante ese error se queda esperando entrada interactiva
# para siempre -- el build nunca termina (el ícono gira sin parar).
#
# El primer intento con ensure_path('BSTINPUTS', '../') no funcionó --
# probablemente porque el directorio de trabajo real de BibTeX dentro de
# latexmk con -outdir no es el que yo asumía. Esta versión usa la ruta
# ABSOLUTA del proyecto en vez de una relativa, así no importa desde qué
# directorio corra BibTeX internamente: siempre la va a encontrar. El ":"
# final en cada valor preserva las rutas de búsqueda por defecto de
# kpathsea (TEXMF, etc.) como respaldo.

my $projdir = '/home/russell/ssd/code/Topicos_Ciencia_Datos/Visual_Analytic_DEAP/articulo_DEAP_visualization';
$ENV{'BSTINPUTS'}  = $projdir . ':' . ($ENV{'BSTINPUTS'}  // '.') . ':';
$ENV{'BIBINPUTS'}  = $projdir . ':' . ($ENV{'BIBINPUTS'}  // '.') . ':';
$ENV{'TEXINPUTS'}  = $projdir . ':' . ($ENV{'TEXINPUTS'}  // '.') . ':';

# Segundo intento (2026-07-22, mismo día): lo anterior tampoco funcionó --
# probablemente porque latexmk pisa/reconfigura BSTINPUTS/BIBINPUTS por su
# cuenta, internamente, para manejar -outdir, después de leer este archivo.
# En vez de pelear con eso, se sobreescribe directamente el comando que
# latexmk usa para invocar BibTeX, fijando las variables justo en el
# momento de la ejecución -- así no hay forma de que se pisen.
$bibtex = "BSTINPUTS=$projdir: BIBINPUTS=$projdir: bibtex %O %S";

# Tercer intento (2026-07-22, mismo día): el segundo tampoco funcionó --
# el main.log de pdflatex confirma que ESA parte compila perfecto y rápido
# (termina normal, "Output written on build/main.pdf"), así que el cuelgue
# es 100% en el paso de BibTeX, y ninguna variable de entorno que le paso
# parece estarle llegando realmente. En vez de seguir peleando con rutas de
# búsqueda, la solución más a prueba de balas: copiar jaes.bst y jaes.bib
# directamente a build/ antes de compilar, para que BibTeX los encuentre
# ahí mismo, en su propio directorio de trabajo, sin necesitar ninguna
# variable de entorno ni ruta de búsqueda especial. Esto NO mueve ni
# reemplaza los originales -- son copias, y build/ ya es una carpeta 100%
# generada (nunca se edita a mano ahí).
mkdir("$projdir/build") unless -d "$projdir/build";
system('cp', '-f', "$projdir/jaes.bst", "$projdir/build/jaes.bst");
system('cp', '-f', "$projdir/jaes.bib", "$projdir/build/jaes.bib");
