from recommendation_system.recommendationSystemImplementation import RecommendationSystem
from typing import Dict, List, Set, Tuple

def start_recommendation_system():
    sistema = RecommendationSystem()

    print("Menú Principal:")
    print("\t0. Salir")
    print("\t1. Calcular distancia euclidiana entre userA y userB")
    print("\t2. Calcular distancia de manhattan entre userA y userB")
    print("\t3. Calcular similitud del coseno entre userA y userB")
    print("\t4. Calcular correlación de Pearson entre userA y userB")
    print("\t5. Calcular KNN")
    print("\t6. Recomendar películas a un usuario (por vecinos)")
    print("\t7. Recomendar películas finales (promedio ponderado)")
    print("\t8. Agregar un nuevo usuario")
    print("\t9. Calificar películas de un usuario")

    while True:
        try:
            choise = int(input("Input opción: ").strip())
        except ValueError:
            print("\tEntrada inválida. Use números.")
            continue

        if choise == 0:
            print("\tSaliendo del sistema de recomendación...")
            break

        elif choise in {1, 2, 3, 4}:
            userA = int(input("\tInsertar ID de user A: "))
            userB = int(input("\tInsertar ID de user B: "))
            # commonMovies = 0
            commonMovies = [0]  # ← mutable para simular referencia


            if choise == 1:
                print(f"\tCalculando distancia euclidiana entre {userA} y {userB}")
                result, valid = sistema.calculateEuclideanDistanceDebug(userA, userB, commonMovies)
            elif choise == 2:
                print(f"\tCalculando distancia de Manhattan entre {userA} y {userB}")
                result, valid = sistema.calculateManhattanDistanceDebug(userA, userB, commonMovies)
            elif choise == 3:
                print(f"\tCalculando similitud del coseno entre {userA} y {userB}")
                result, valid = sistema.calculateCosineSimilarityDebug(userA, userB, commonMovies)
            else:
                print(f"\tCalculando correlación de Pearson entre {userA} y {userB}")
                result, valid = sistema.calculatePearsonCorrelationDebug(userA, userB, commonMovies)

            if valid:
                print(f"\tResultado: {result:.8f} | Películas en común: {commonMovies[0]}")
            else:
                print("\tUsuario no válido o sin películas en común")

        elif choise == 5:
            userA = int(input("\tInsertar ID del usuario: "))
            n = int(input("\tNúmero de vecinos a buscar (n): "))
            metric = input("\tMétrica (euclidean, manhattan, cosine, pearson): ").strip().lower()
            print(f"\tCalculando KNN para usuario {userA} con métrica '{metric}' y n = {n}")
            log02 = sistema.getCoutDebugFile02CalcularKNN()
            log02.write("[KNN] knn(n, user, metrica) BEGIN\n")

            resultado = sistema.knn(n, userA, metric)

            if not resultado:
                print("\tNo se encontraron vecinos válidos.")
                log02.write("\t[KNN] No se encontraron vecinos válidos o no hay usuarios registrados.\n\n")

            else:
                print(f"\tVecinos encontrados para el usuario {userA}:")
                log02.write(f"\t[KNN] Calculando KNN para el  user {userA} con n = {n} y metrica={metric}:\n")
                log02.write(f"\t[KNN] Vecinos encontrados para user {userA}:\n")

                for vecino, valor in resultado:
                    etiqueta = {
                        "euclidean": "Distancia",
                        "manhattan": "Distancia",
                        "cosine": "Similaridad",
                        "pearson": "Correlación"
                    }.get(metric, "Valor")
                    print(f"\t\tUser {vecino} - {etiqueta}: {valor:.8f}")
                    log02.write(f"\t\tUser ID: {vecino}, {etiqueta}: {valor:.8f}\n")
            
            log02.write("[KNN] knn(n, user, metrica) END\n\n")



        elif choise == 6:
            idUser = int(input("Insertar ID del usuario a recomendar: "))
            n = int(input("Número de vecinos (n): "))
            metrica = input("Métrica (euclidean, manhattan, cosine, pearson): ").strip().lower()
            vecinos = sistema.knn(n, idUser, metrica)
            if not vecinos:
                print("\tNo se encontraron vecinos con películas en común.")
                continue
            sistema.recomendar(vecinos, idUser)
            print("\tRecomendaciones generadas. Ver archivo de salida.")

        elif choise == 7:
            idUser = int(input("Insertar ID del usuario a recomendar: "))
            n = int(input("Número de vecinos (n): "))
            metrica = input("Métrica (euclidean, manhattan, cosine, pearson): ").strip().lower()
            vecinos = sistema.knn(n, idUser, metrica)
            if not vecinos:
                print("\tNo se encontraron vecinos con películas en común.")
                continue
            recomendaciones = sistema.recomendar(vecinos, idUser)
            sistema.recomendarMovie(recomendaciones, idUser)
            print("\t¡Recomendación final generada!")
        elif choise == 8:
            print("\tAgregando un nuevo usuario...")
            sistema.agregarUsuario()
            print("\tUsuario agregado exitosamente.")
        elif choise == 9:
            idUser = int(input("Insertar ID del usuario: "))
            peliculas: List[Tuple[int, float]] = []
            while True:
                try:
                    pelicula_id = int(input("\tInsertar ID de la película (0 para terminar): "))
                    if pelicula_id == 0:
                        break
                    rating = float(input("\tInsertar rating de la película: "))
                    peliculas.append((pelicula_id, rating))
                except ValueError:
                    print("\tEntrada inválida. Use números.")
            sistema.calificarPeliculas(idUser, peliculas)
            print("\tPelículas calificadas exitosamente.")
        else:
            print("\tOpción inválida. Intente nuevamente.")
    del sistema

if __name__ == "__main__":
    start_recommendation_system()
