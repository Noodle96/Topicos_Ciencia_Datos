# Archivo de configuración de latexmk (NO es plantilla ni contenido del
# artículo). Historial breve, por si vuelve a pasar algo parecido:
#
# 2026-07-22: las citas aparecían como [?] y el build se colgaba girando
# sin parar. Se probaron varios arreglos de rutas de búsqueda (BSTINPUTS/
# BIBINPUTS/TEXINPUTS, sobreescribir el comando de BibTeX, copiar jaes.bst
# a build/) -- ninguno era necesario. La causa real, encontrada corriendo
# BibTeX a mano en la terminal: un comentario en jaes.bib (cerca de la
# entrada "evoair") contenía el texto "@misc" dentro de una nota en
# español -- BibTeX no tiene comentarios de línea con "%" como LaTeX, así
# que interpretó ese "@" suelto como el inicio de una entrada nueva y
# rompió el parseo del archivo completo. Arreglado reformulando esa nota
# para no tener un "@" literal. Este archivo se deja vacío (sin config
# extra) porque BibTeX encuentra jaes.bst y jaes.bib sin problema por su
# cuenta una vez que el .bib es válido.
