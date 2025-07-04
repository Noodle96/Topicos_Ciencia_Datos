# 📽️ Sistema de Recomendación de Películas en Python

Este proyecto implementa un sistema de recomendación basado en vecinos (KNN) y distintas métricas de similitud/distancia entre usuarios, migrado desde C++ a Python.

---

## 🗂️ Estructura del Proyecto

├── dataset_32M/
│ ├── ratings.csv
│ ├── movies.csv
Raiz_general/
├── recommendation_system/
│ ├── __init__.py
│ ├── timer.py
│ ├── recommendationSystemInterface.py
│ ├── recommendationSystemImpl.py
├── out/ # Archivos de salida (.txt)
│ ├── 01_validar_distancias.txt
│ ├── 02_calcular_knn.txt
│ ├── 03_calcular_recomendaciones.txt
│ ├── 04_peliculas_recomendar.txt
│ └── users.txt
├── main.py # Punto de entrada (menú)
└── README.md



---

## ▶️ Cómo ejecutar

1. Asegúrate de tener Python 3.7 o superior instalado.

2. Posiciónate en la raíz del proyecto:

```bash
cd Raiz_general/
python main.py


📋 Funcionalidades del Menú
| Opción | Descripción                                                   |
| ------ | ------------------------------------------------------------- |
| 1      | Calcula distancia **euclidiana** entre dos usuarios           |
| 2      | Calcula distancia **manhattan** entre dos usuarios            |
| 3      | Calcula **similitud del coseno** entre dos usuarios           |
| 4      | Calcula **correlación de Pearson** entre dos usuarios         |
| 5      | Ejecuta **KNN** para un usuario con una métrica dada          |
| 6      | Genera recomendaciones básicas (películas vistas por vecinos) |
| 7      | Genera recomendaciones finales con promedio ponderado         |
| 0      | Salir del sistema                                             |



📂 Archivos de salida
Los resultados y logs se escriben en la carpeta out/, en los siguientes archivos:

01_validar_distancias.txt → Debug de métricas

02_calcular_knn.txt → Resultados de KNN

03_calcular_recomendaciones.txt → Detalles de recomendaciones vecinales

04_peliculas_recomendar.txt → Recomendaciones finales por película

users.txt → Información de usuarios y sus ratings
