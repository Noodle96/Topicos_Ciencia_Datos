from recommendation_system.recommendationSystemInterface import RecommendationSystem as BaseRS
from recommendation_system.timer import Timer
from operator import itemgetter
from typing import Dict, List, Set, Tuple
import math
import os
import csv

# DEFINICIÓN DE UMBRALES
DISTANCIA_MAXIMA: float = 1e9
UMBRAL_RATING_VECINO: float = 3.0 # Umbral para el rating de un vecino
UMBRAL_PELICULAS_COMUNES: int = 1 # Umbral para delrecommended_moviesimitar el número mínimo de películas comunes entre dos usuarios para considerar su similitud
UMBRAL_COSINE_SIMILARITY: float = 0.5 # Umbral para similitud del coseno
UMBRAL_PEARSON_CORRELATION: float = 0.5 # Umbral para correlación de Pearson
# UMBRAL_VECINOS_SIMILARES:int = 15


class RecommendationSystem(BaseRS):
    def __init__(self):
        super().__init__()

        out_dir = os.path.join(os.path.dirname(__file__), "..", "out")
        os.makedirs(out_dir, exist_ok=True)  # asegúrate de que exista

        # Abrir archivos de salida
        # self.cout_debug_file = open("../out/output_recommendation_systema.txt", "w")
        self.cout_debug_file = open(os.path.join(out_dir, "output_recommendation_systema.txt"), "w", buffering=1)

        # self.cout_debug_file_01_validar_distancias = open("../out/01_validar_distancias.txt", "w")
        self.cout_debug_file_01_validar_distancias = open(os.path.join(out_dir, "01_validar_distancias.txt"), "w",buffering=1)

        # self.cout_debug_file_02_calcular_knn = open("../out/02_calcular_knn.txt", "w")
        self.cout_debug_file_02_calcular_knn = open(os.path.join(out_dir, "02_calcular_knn.txt"), "w", buffering=1)

        # self.cout_debug_file_03_calcular_recomendaciones = open("../out/03_calcular_recomendaciones.txt", "w")
        self.cout_debug_file_03_calcular_recomendaciones = open(os.path.join(out_dir, "03_calcular_recomendaciones.txt"), "w", buffering=1)

        # self.cout_debug_file_04_peliculas_recomendar = open("../out/04_peliculas_recomendar.txt", "w")
        self.cout_debug_file_04_peliculas_recomendar = open(os.path.join(out_dir, "04_peliculas_recomendar.txt"), "w", buffering=1)

        self.cout_debug_file.write("[RECOMMENDATION SYSTEM] RecommendationSystem()\n")
        self.cout_debug_file.write("\t[RECOMMENDATION SYSTEM] Load ratings.csv BEGIN\n")
        timer = Timer("Load ratings.csv")

        base_dir = os.path.dirname(__file__)
        ratings_path = os.path.abspath(os.path.join(base_dir, "..", "dataset_32M", "ratings.csv"))
        try:
            with open(ratings_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header
                for row in reader:
                    userId, movieId, rating, timestamp = int(row[0]), int(row[1]), float(row[2]), row[3]
                    self.addRatingAndUser(userId, movieId, rating, timestamp)
            self.cout_debug_file.write("\t\t")
            timer.printElapsed(self.cout_debug_file)
            self.cout_debug_file.write("\t[RECOMMENDATION SYSTEM] Load ratings.csv END\n\n")
            self.cout_debug_file.write("\t")
            self.printUser()
        except FileNotFoundError:
            self.cout_debug_file.write("\tError al abrir el archivo rating.csv\n")

        self.cout_debug_file.write("\t[RECOMMENDATION SYSTEM] Load movies.csv BEGIN\n")
        timer.reset("Load movies.csv")

        movies_path = os.path.abspath(os.path.join(base_dir, "..", "dataset_32M", "movies.csv"))
        try:
            with open(movies_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header
                for row in reader:
                    movieId = int(row[0])
                    title = row[1].replace('"', '')
                    genres = row[2].split('|')
                    self.addMovie(movieId, title, genres)
            self.cout_debug_file.write("\t\t")
            timer.printElapsed(self.cout_debug_file)
            self.cout_debug_file.write("\t[RECOMMENDATION SYSTEM] Load movies.csv END\n\n")
            self.printMMovies()
        except FileNotFoundError:
            self.cout_debug_file.write("\tError al abrir el archivo movies.csv\n")

    def __del__(self):
        if self.cout_debug_file: self.cout_debug_file.close()
        if self.cout_debug_file_01_validar_distancias: self.cout_debug_file_01_validar_distancias.close()
        if self.cout_debug_file_02_calcular_knn: self.cout_debug_file_02_calcular_knn.close()
        if self.cout_debug_file_03_calcular_recomendaciones: self.cout_debug_file_03_calcular_recomendaciones.close()
        if self.cout_debug_file_04_peliculas_recomendar: self.cout_debug_file_04_peliculas_recomendar.close()
        # No se imprime en archivo aquí porque puede estar cerrado

    '''
        addRatingAndUser(idUser, idMovie, rating, timestamp)
        idUser: int
        idMovie: int
        rating: float
        timestamp: string
    '''
    def addRatingAndUser(self, idUser: int, idMovie: int, rating: float, timestamp: str):
        # setdefault(idUser, {})
        # Si idUser ya existe como clave, devuelve el diccionario asociado a ese usuario.
        # Si no existe, lo agrega con un valor por defecto {} (un diccionario vacío) y lo devuelve.
        # [idMovie] = rating
        # Accede al diccionario de películas para ese usuario y asigna el rating a la película con id 
        self.user_movie_ratings.setdefault(idUser, {})[idMovie] = rating
        self.users.add(idUser)

    '''
        addMovie(idMovie, title, genres)
        idMovie: int
        title: string
        genres: vector<string>
    '''
    def addMovie(self, idMovie: int, title: str, genres: List[str]):
        self.movies[idMovie] = (title, genres)

    '''
        getNumberOfRatedMovies(userId)
        userId: int
        return: int
    '''
    def getNumberOfRatedMovies(self, userId: int) -> int:
        return len(self.user_movie_ratings.get(userId, {}))

    '''
        calculateEuclideanDistance(userA, userB, commonMovies)
        userA: int
        userB: int
        commonMovies: int&
        return: pair<float, bool>
    '''
    def calculateEuclideanDistance(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        euclideanDistance = 0.0
        commonMovies[0] = 0

        ratingsA = self.user_movie_ratings.get(userA, {})
        ratingsB = self.user_movie_ratings.get(userB, {})

        if not ratingsA or not ratingsB:
            return DISTANCIA_MAXIMA, False

        smaller = ratingsA if len(ratingsA) <= len(ratingsB) else ratingsB
        larger = ratingsB if smaller is ratingsA else ratingsA

        for movie, rating in smaller.items():
            if movie in larger:
                diff = rating - larger[movie]
                euclideanDistance += diff * diff
                commonMovies[0] += 1

        if commonMovies[0] > 0:
            return math.sqrt(euclideanDistance), True
        return DISTANCIA_MAXIMA, False

    def calculateEuclideanDistanceDebug(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        out = self.cout_debug_file_01_validar_distancias
        out.write("[EUCLIDEAN DISTANCE] calculateEuclideanDistanceDebug() BEGIN\n")
        out.write(f"\t[EUCLIDEAN DISTANCE] distance between {userA} and {userB}\n")

        euclideanDistance = 0.0
        commonMovies[0] = 0

        ratingsA = self.user_movie_ratings.get(userA, {})
        ratingsB = self.user_movie_ratings.get(userB, {})

        if not ratingsA or not ratingsB:
            out.write("\t[EUCLIDEAN DISTANCE] usuario no valido o no tiene ratings\n")
            out.write("[EUCLIDEAN DISTANCE] calculateEuclideanDistanceDebug() END\n\n")
            return DISTANCIA_MAXIMA, False

        smaller = ratingsA if len(ratingsA) <= len(ratingsB) else ratingsB
        larger = ratingsB if smaller is ratingsA else ratingsA

        out.write(f"\t[EUCLIDEAN DISTANCE] smaller size: {len(smaller)}\n")
        out.write(f"\t[EUCLIDEAN DISTANCE] larger size: {len(larger)}\n")

        timer = Timer("Calculate Euclidean Distance")
        for movie, rating in smaller.items():
            if movie in larger:
                diff = rating - larger[movie]
                euclideanDistance += diff * diff
                commonMovies[0] += 1

        out.write(f"\t[EUCLIDEAN DISTANCE] commonMovies: {commonMovies[0]}\n")
        out.write("\t")
        timer.printElapsed(out, "seg")

        if commonMovies[0] > 0:
            result = math.sqrt(euclideanDistance)
            out.write(f"\t[EUCLIDEAN DISTANCE] euclidean distance: {result:.8f}\n")
            out.write("[EUCLIDEAN DISTANCE] calculateEuclideanDistanceDebug() END\n\n")
            return result, True
        else:
            out.write(f"\t[EUCLIDEAN DISTANCE] No common movies found between user {userA} and user {userB}\n")
            out.write("[EUCLIDEAN DISTANCE] calculateEuclideanDistanceDebug() END\n\n")
            return DISTANCIA_MAXIMA, False

    '''
        calculateManhattanDistance(userA, userB, commonMovies)
        userA: int
        userB: int
        commonMovies: int&
        return: pair<float, bool>
    '''
    def calculateManhattanDistance(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        manhattanDistance = 0.0
        commonMovies[0] = 0

        ratingsA = self.user_movie_ratings.get(userA, {})
        ratingsB = self.user_movie_ratings.get(userB, {})

        if not ratingsA or not ratingsB:
            return DISTANCIA_MAXIMA, False

        smaller = ratingsA if len(ratingsA) <= len(ratingsB) else ratingsB
        larger = ratingsB if smaller is ratingsA else ratingsA

        for movie, rating in smaller.items():
            if movie in larger:
                diff = rating - larger[movie]
                manhattanDistance += abs(diff)
                commonMovies[0] += 1

        if commonMovies[0] > 0:
            return manhattanDistance, True
        return DISTANCIA_MAXIMA, False

    def calculateManhattanDistanceDebug(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        out = self.cout_debug_file_01_validar_distancias
        out.write("[MANHATTAN DISTANCE] calculateManhattanDistanceDebug() BEGIN\n")
        out.write(f"\t[MANHATTAN DISTANCE] distance between {userA} and {userB}\n")

        manhattanDistance = 0.0
        commonMovies[0] = 0

        ratingsA = self.user_movie_ratings.get(userA, {})
        ratingsB = self.user_movie_ratings.get(userB, {})

        if not ratingsA or not ratingsB:
            out.write("\t[MANHATTAN DISTANCE] usuario no valido o no tiene ratings\n")
            out.write("[MANHATTAN DISTANCE] calculateManhattanDistanceDebug() END\n\n")
            return DISTANCIA_MAXIMA, False

        smaller = ratingsA if len(ratingsA) <= len(ratingsB) else ratingsB
        larger = ratingsB if smaller is ratingsA else ratingsA

        out.write(f"\t[MANHATTAN DISTANCE] smaller size: {len(smaller)}\n")
        out.write(f"\t[MANHATTAN DISTANCE] larger size: {len(larger)}\n")

        timer = Timer("Calculate Manhattan Distance")
        for movie, rating in smaller.items():
            if movie in larger:
                diff = rating - larger[movie]
                manhattanDistance += abs(diff)
                commonMovies[0] += 1

        out.write(f"\t[MANHATTAN DISTANCE] commonMovies: {commonMovies[0]}\n")
        out.write("\t")
        timer.printElapsed(out, "seg")

        if commonMovies[0] > 0:
            out.write(f"\t[MANHATTAN DISTANCE] manhattan distance: {manhattanDistance:.8f}\n")
            out.write("[MANHATTAN DISTANCE] calculateManhattanDistanceDebug() END\n\n")
            return manhattanDistance, True
        else:
            out.write(f"\t[MANHATTAN DISTANCE] No common movies found between user {userA} and user {userB}\n")
            out.write("[MANHATTAN DISTANCE] calculateManhattanDistanceDebug() END\n\n")
            return DISTANCIA_MAXIMA, False
        
    '''
        calculateCosineSimilarity(userA, userB, commonMovies)
        userA: int
        userB: int
        commonMovies: int&
        return: pair<float, bool>
    '''
    def calculateCosineSimilarity(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        dotProduct = 0.0
        normA = 0.0
        normB = 0.0
        commonMovies[0] = 0

        ratingsA = self.user_movie_ratings.get(userA, {})
        ratingsB = self.user_movie_ratings.get(userB, {})

        if not ratingsA or not ratingsB:
            return 0.0, False

        smaller = ratingsA if len(ratingsA) <= len(ratingsB) else ratingsB
        larger = ratingsB if smaller is ratingsA else ratingsA

        for movie, ratingA in smaller.items():
            if movie in larger:
                ratingB = larger[movie]
                dotProduct += ratingA * ratingB
                normA += ratingA ** 2
                normB += ratingB ** 2
                commonMovies[0] += 1

        if commonMovies[0] == 0 or normA == 0 or normB == 0:
            return 0.0, False

        cosineSimilarity = dotProduct / (math.sqrt(normA) * math.sqrt(normB))
        return cosineSimilarity, True

    def calculateCosineSimilarityDebug(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        out = self.cout_debug_file_01_validar_distancias
        out.write("[COSINE SIMILARITY] calculateCosineSimilarityDebug() BEGIN\n")
        out.write(f"\t[COSINE SIMILARITY] similarity between {userA} and {userB}\n")

        dotProduct = 0.0
        normA = 0.0
        normB = 0.0
        commonMovies[0] = 0

        ratingsA = self.user_movie_ratings.get(userA, {})
        ratingsB = self.user_movie_ratings.get(userB, {})

        if not ratingsA or not ratingsB:
            out.write("\t[COSINE SIMILARITY] usuario no valido o no tiene ratings\n")
            out.write("[COSINE SIMILARITY] calculateCosineSimilarityDebug() END\n\n")
            return 0.0, False

        smaller = ratingsA if len(ratingsA) <= len(ratingsB) else ratingsB
        larger = ratingsB if smaller is ratingsA else ratingsA

        out.write(f"\t[COSINE SIMILARITY] smaller size: {len(smaller)}\n")
        out.write(f"\t[COSINE SIMILARITY] larger size: {len(larger)}\n")

        timer = Timer("Calculate Cosine Similarity")
        for movie, ratingA in smaller.items():
            if movie in larger:
                ratingB = larger[movie]
                dotProduct += ratingA * ratingB
                normA += ratingA ** 2
                normB += ratingB ** 2
                commonMovies[0] += 1

        out.write(f"\t[COSINE SIMILARITY] commonMovies: {commonMovies[0]}\n")
        out.write("\t")
        timer.printElapsed(out, "seg")

        if commonMovies[0] == 0 or normA == 0 or normB == 0:
            out.write("\t[COSINE SIMILARITY] No common movies or invalid norms\n")
            out.write("[COSINE SIMILARITY] calculateCosineSimilarityDebug() END\n\n")
            return 0.0, False

        cosineSimilarity = dotProduct / (math.sqrt(normA) * math.sqrt(normB))
        out.write(f"\t[COSINE SIMILARITY] cosine similarity: {cosineSimilarity:.8f}\n")
        out.write("[COSINE SIMILARITY] calculateCosineSimilarityDebug() END\n\n")
        return cosineSimilarity, True

    '''
        calculatePearsonCorrelation(userA, userB, commonMovies)
        userA: int
        userB: int
        commonMovies: int&
        return: pair<float, bool>
    '''
    def calculatePearsonCorrelation(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        sumA = sumB = sumA2 = sumB2 = sumAB = 0.0
        commonMovies[0] = 0

        ratingsA = self.user_movie_ratings.get(userA, {})
        ratingsB = self.user_movie_ratings.get(userB, {})

        if not ratingsA or not ratingsB:
            return 0.0, False

        smaller = ratingsA if len(ratingsA) <= len(ratingsB) else ratingsB
        larger = ratingsB if smaller is ratingsA else ratingsA

        for movie, ratingA in smaller.items():
            if movie in larger:
                ratingB = larger[movie]
                sumA += ratingA
                sumB += ratingB
                sumA2 += ratingA ** 2
                sumB2 += ratingB ** 2
                sumAB += ratingA * ratingB
                commonMovies[0] += 1

        if commonMovies[0] == 0:
            return 0.0, False

        numerator = sumAB - (sumA * sumB / commonMovies[0])
        denominator = math.sqrt(sumA2 - (sumA ** 2 / commonMovies[0])) * math.sqrt(sumB2 - (sumB ** 2 / commonMovies[0]))

        if denominator == 0:
            return 0.0, False

        pearson = numerator / denominator
        return pearson, True

    def calculatePearsonCorrelationDebug(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        out = self.cout_debug_file_01_validar_distancias
        out.write("[PEARSON CORRELATION] calculatePearsonCorrelationDebug() BEGIN\n")
        out.write(f"\t[PEARSON CORRELATION] correlation between {userA} and {userB}\n")

        sumA = sumB = sumA2 = sumB2 = sumAB = 0.0
        commonMovies[0] = 0

        ratingsA = self.user_movie_ratings.get(userA, {})
        ratingsB = self.user_movie_ratings.get(userB, {})

        if not ratingsA or not ratingsB:
            out.write("\t[PEARSON CORRELATION] usuario no valido o no tiene ratings\n")
            out.write("[PEARSON CORRELATION] calculatePearsonCorrelationDebug() END\n\n")
            return 0.0, False

        smaller = ratingsA if len(ratingsA) <= len(ratingsB) else ratingsB
        larger = ratingsB if smaller is ratingsA else ratingsA

        out.write(f"\t[PEARSON CORRELATION] smaller size: {len(smaller)}\n")
        out.write(f"\t[PEARSON CORRELATION] larger size: {len(larger)}\n")

        timer = Timer("Calculate Pearson Correlation")
        for movie, ratingA in smaller.items():
            if movie in larger:
                ratingB = larger[movie]
                sumA += ratingA
                sumB += ratingB
                sumA2 += ratingA ** 2
                sumB2 += ratingB ** 2
                sumAB += ratingA * ratingB
                commonMovies[0] += 1

        out.write(f"\t[PEARSON CORRELATION] commonMovies: {commonMovies[0]}\n")
        out.write("\t")
        timer.printElapsed(out, "seg")

        if commonMovies[0] == 0:
            out.write(f"\t[PEARSON CORRELATION] No common movies found between user {userA} and user {userB}\n")
            out.write("[PEARSON CORRELATION] calculatePearsonCorrelationDebug() END\n\n")
            return 0.0, False

        numerator = sumAB - (sumA * sumB / commonMovies[0])
        denominator = math.sqrt(sumA2 - (sumA ** 2 / commonMovies[0])) * math.sqrt(sumB2 - (sumB ** 2 / commonMovies[0]))

        if denominator == 0:
            out.write("\t[PEARSON CORRELATION] denominator is zero, returning 0.0\n")
            out.write("[PEARSON CORRELATION] calculatePearsonCorrelationDebug() END\n\n")
            return 0.0, False

        pearson = numerator / denominator
        out.write(f"\t[PEARSON CORRELATION] pearson correlation: {pearson:.8f}\n")
        out.write("[PEARSON CORRELATION] calculatePearsonCorrelationDebug() END\n\n")
        return pearson, True
    
    '''
        knn(n, userX, metric)
        n: int
        userX: int
        metric: string
        return: vector<pair<int, float>>
    '''
    def knn(self, n: int, userX: int, metric: str) -> List[Tuple[int, float]]:
        distances: List[Tuple[int, float]] = []

        for user in self.users:
            if user == userX: continue
            commonMovies: List[int] = [0]
            if metric == "euclidean":
                distance, valid = self.calculateEuclideanDistance(userX, user, commonMovies)
            elif metric == "manhattan":
                distance, valid = self.calculateManhattanDistance(userX, user, commonMovies)
            elif metric == "cosine":
                distance, valid = self.calculateCosineSimilarity(userX, user, commonMovies)
                if distance < UMBRAL_COSINE_SIMILARITY:
                    continue
            elif metric == "pearson":
                distance, valid = self.calculatePearsonCorrelation(userX, user, commonMovies)
                if distance < UMBRAL_PEARSON_CORRELATION:
                    continue
            else:
                self.cout_debug_file.write("Metrica no valida\n")
                return []

            if valid and commonMovies[0] >= UMBRAL_PELICULAS_COMUNES:
                distances.append((user, distance))

        if metric in {"euclidean", "manhattan"}:
            distances.sort(key=itemgetter(1))  # Ascendente
        elif metric in {"cosine", "pearson"}:
            distances.sort(key=itemgetter(1), reverse=True)  # Descendente

        return distances[:n]

    '''
        recomendar(knn_result, idUser)
        knn_result: List[Tuple[int, float]]
        idUser: int
        return: Dict[int, List[Tuple[float, int]]]
    '''
    def recomendar(self, knn_result: List[Tuple[int, float]], userARecomendar: int) -> Dict[int, List[Tuple[float, int]]]:
        recommended_movies: Dict[int, List[Tuple[float, int]]] = {}

        out = self.cout_debug_file_03_calcular_recomendaciones
        out.write("[RECOMENDAR] recomendar() BEGIN\n")

        if userARecomendar not in self.users:
            out.write(f"\t[RECOMENDAR] User {userARecomendar} not found\n")
            return recommended_movies

        ratingsA = self.user_movie_ratings[userARecomendar]
        timer = Timer("first timer")

        dictUserRating: Dict[int, float] = {}
        for userX, distance in knn_result:
            ratingsX = self.user_movie_ratings[userX]
            for movie, rating in ratingsX.items():
                if rating < UMBRAL_RATING_VECINO:
                    continue
                if movie not in ratingsA:
                    # recommended_movies[userX].append((rating, movie))
                    recommended_movies.setdefault(userX, []).append((rating, movie))
                    # llenar dictUserRating con el valor de distance
                    dictUserRating[userX] = distance
                    # dictUserRating.setdefault(userX, 0.0)


            recommended_movies[userX].sort(key=lambda x: x[0], reverse=True)

        out.write("\t[RECOMENDAR] Time taken to process recommendations: ")
        timer.printElapsed(out, "seg")

        out.write(f"\t[RECOMENDAR] Recommended movies for user {userARecomendar}:\n")
        if not recommended_movies:
            out.write(f"\t[RECOMENDAR] No recommendations found for user {userARecomendar}\n")

        out.write(f"\t\t[RECOMENDAR] Peliculas calificadas por el usuario {userARecomendar} = {self.getNumberOfRatedMovies(userARecomendar)}\n")

        vecino = 1
        contador: int = 0
        timer2 = Timer("second timer")
        for userX, movies in list(recommended_movies.items())[:20]:
            out.write(f"\t\t[RECOMENDAR] Recomendaciones del User {userX}[{self.getNumberOfRatedMovies(userX)}] con similaridad={dictUserRating[userX]} vecino #{vecino}, total movies: {len(movies)}\n")
            vecino += 1
            for movieRating, movieId in movies:
                out.write(f"\t\t\t[RECOMENDAR] Movie: {movieId} with rating: {movieRating:.1f}\n")
            out.write("\n")
            contador += 1
            if(contador >= 20):
                break

        out.write("\t[RECOMENDAR] Time taken to process recommendations: ")
        timer2.printElapsed(out, "seg")
        out.write("[RECOMENDAR] recomendar() END\n")
        return recommended_movies

    '''
        recomendarMovie(peliculasRecomendadasPorUsuarios, userARecomendar)
    '''
    def recomendarMovie(self, peliculasRecomendadasPorUsuarios: Dict[int, List[Tuple[float, int]]], userARecomendar: int):
        out = self.cout_debug_file_04_peliculas_recomendar
        out.write("[RECOMENDAR MOVIE] recomendarCancion() BEGIN\n")
        out.write(f"\t[RECOMENDAR MOVIE] Recomendacion para el user: {userARecomendar}\n")

        timer = Timer("recomendarMovie")
        movie_vectorRatings: Dict[int, List[float]] = {}
        for _, movies in peliculasRecomendadasPorUsuarios.items():
            for rating, movieId in movies:
                movie_vectorRatings.setdefault(movieId, []).append(rating)

        out.write("\t")
        timer.printElapsed(out, "seg")

        respuestaFinal: List[Tuple[float, int]] = []
        timer2 = Timer("calculo all score")
        for movieId, ratings in movie_vectorRatings.items():
            suma = sum(ratings)
            count = len(ratings)
            if count < UMBRAL_VECINOS_SIMILARES:
                continue
            totalVecinos = len(peliculasRecomendadasPorUsuarios)
            score = (suma * count) / totalVecinos
            respuestaFinal.append((score, movieId))

        respuestaFinal.sort(reverse=True)
        out.write("\t")
        timer2.printElapsed(out, "seg")

        timer3 = Timer("write recomendacion movies")
        out.write("\t[RECOMENDAR MOVIE] write recomendacion movies\n")
        for score, movieId in respuestaFinal:
            title = self.movies[movieId][0]
            out.write(f"\t\t[RECOMENDAR MOVIE] Movie ID: {movieId}{{{title}}} with score: {score:.4f}\n")
        out.write("\t")
        timer3.printElapsed(out)

        out.write("[RECOMENDAR MOVIE] recomendarCancion() END\n")

    '''
        AgregarUsuario
    '''
    def agregarUsuario(self) -> None:
        ## Elegir un id que no esta en self.users
        new_user_id = max(self.users) + 1 if self.users else 1
        print(f"[RECOMMENDATION SYSTEM] Adding new user with ID: {new_user_id}")
        self.users.add(new_user_id)
        self.user_movie_ratings[new_user_id] = {}
        self.cout_debug_file.write(f"[RECOMMENDATION SYSTEM] New user added with ID: {new_user_id}\n")
        self.printUser()  # Imprimir el estado de los usuarios después de agregar el nuevo
        return None
    

    '''
        calificarPeliculas
        Allows a user to rate multiple movies at once.
        idUser: ID of the user
        peliculas: List of movie IDs and their ratings
    '''
    def calificarPeliculas(self, idUser: int, peliculas: List[Tuple[int, float]]) -> None:
        if idUser not in self.users:
            self.cout_debug_file.write(f"[RECOMMENDATION SYSTEM] User {idUser} does not exist. Cannot rate movies.\n")
            return None
        for movieId, rating in peliculas:
            if movieId in self.movies:
                self.user_movie_ratings[idUser][movieId] = rating
                self.cout_debug_file.write(f"[RECOMMENDATION SYSTEM] User {idUser} rated movie {movieId} with rating {rating}\n")
            else:
                self.cout_debug_file.write(f"[RECOMMENDATION SYSTEM] Movie {movieId} does not exist. Cannot rate.\n")
        self.printUser()  # Imprimir el estado de los usuarios después de calificar las
        return None

    '''
        printUser()
    '''
    def printUser(self):
        out = self.cout_debug_file
        out.write("[RECOMMENDATION SYSTEM] printUser() BEGIN\n")
        timer = Timer("write users.txt")

        base_dir = os.path.dirname(__file__)
        users_path = os.path.abspath(os.path.join(base_dir, "..", "out", "users.txt"))
        try:
            with open(users_path, "w", buffering=1) as user_file:
                for user in self.users:
                    user_file.write(f"User ID: {user} -> {len(self.user_movie_ratings[user])} ratings\n")
        except Exception as e:
            out.write(f"Error writing to users.txt: {e}\n")

        out.write("\t\t")
        timer.printElapsed(out)
        out.write("\t[RECOMMENDATION SYSTEM] printUser() END\n")

    '''
        Imprimir en el archivo de salida las películas
        que se han agregado al sistema.
        Ordenar por el numero de ratinf que posee cada película.
    '''
    def printMMovies(self) -> None:
        out = self.cout_debug_file
        out.write("[RECOMMENDATION SYSTEM] printMMovies() BEGIN\n")
        timer = Timer("write movies.txt")
        base_dir = os.path.dirname(__file__)
        movies_path = os.path.abspath(os.path.join(base_dir, "..", "out", "movies.txt"))
        try:
            with open(movies_path, "w", buffering=1) as movie_file:
                sorted_movies = sorted(self.movies.items(), key=lambda x: len(self.user_movie_ratings.get(x[0], {})), reverse=True)
                for movieId, (title, genres) in sorted_movies:
                    movie_file.write(f"Movie ID: {movieId}, Title: {title}, Genres: {', '.join(genres)}, Ratings: {len(self.user_movie_ratings.get(movieId, {}))}\n")
        except Exception as e:
            out.write(f"Error writing to movies.txt: {e}\n")
        out.write("\t\t")
        timer.printElapsed(out)
        out.write("\t[RECOMMENDATION SYSTEM] printMMovies() END\n")
        return None




