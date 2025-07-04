from typing import Dict, Set, List, Tuple

class RecommendationSystem:
    def __init__(self):
        self.user_movie_ratings: Dict[int, Dict[int, float]] = {}
        self.users: Set[int] = set()
        self.movies: Dict[int, Tuple[str, List[str]]] = {}
        self.cout_debug_file = None
        self.cout_debug_file_01_validar_distancias = None
        self.cout_debug_file_02_calcular_knn = None
        self.cout_debug_file_03_calcular_recomendaciones = None
        self.cout_debug_file_04_peliculas_recomendar = None

    def __del__(self):
        pass  # Se puede cerrar archivos aquí si se abrieron

    # implementar una funcion get para usar cout_debug_file_01_validar_distancias fuera de la clase
    def getCoutDebugFile01ValidarDistancias(self):
        return self.cout_debug_file_01_validar_distancias

    def getCoutDebugFile02CalcularKNN(self):
        return self.cout_debug_file_02_calcular_knn

    def getCoutDebugFile03CalcularRecomendaciones(self):
        return self.cout_debug_file_03_calcular_recomendaciones

    def getCoutDebugFile04PeliculasRecomendar(self):
        return self.cout_debug_file_04_peliculas_recomendar

    '''
        add to hash to hash
        addRatingAndUser(idUser, idMovie, rating, timestamp)
        idUser: int
        idMovie: int
        rating: float
        timestamp: string
    '''
    def addRatingAndUser(self, idUser: int, idMovie: int, rating: float, timestamp: str):
        pass

    '''
        addMovie(idMovie, title, genres)
        idMovie: int
        title: string
        genres: vector<string>
    '''
    def addMovie(self, idMovie: int, title: str, genres: List[str]):
        pass

    '''
        Funcion que retorna el numero de peliculas que ha calificado un usuario
        userId: int
        return: int
    '''
    def getNumberOfRatedMovies(self, userId: int) -> int:
        pass

    '''
        Calculo de la distancia euclidiana entre el usuario A y el usuario B
        userA: int
        userB: int
        commonMovies: int&
        return: pair<float, bool>
    '''
    def calculateEuclideanDistance(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        pass

    def calculateEuclideanDistanceDebug(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        pass

    '''
        Calculo de la distancia de manhattan entre el usuario A y el usuario B
        userA: int
        userB: int
        commonMovies: int&
        return: pair<float, bool>
    '''
    def calculateManhattanDistance(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        pass

    def calculateManhattanDistanceDebug(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        pass

    '''
        Calculo de la similitud del coseno entre el usuario A y el usuario B
        userA: int
        userB: int
        commonMovies: int&
        return: pair<float, bool>
    '''
    def calculateCosineSimilarity(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        pass

    def calculateCosineSimilarityDebug(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        pass

    '''
        Calculo del coeficiente de correlacion de pearson entre el usuario A y el usuario B,
        mediante la aproximacion de pearson
        userA: int
        userB: int
        commonMovies: int&
        return: pair<float, bool>
    '''
    def calculatePearsonCorrelation(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        pass

    def calculatePearsonCorrelationDebug(self, userA: int, userB: int, commonMovies: List[int]) -> Tuple[float, bool]:
        pass

    '''
        Funcion knn que calcula la distancia del usuarioX entre todos los usuarios
        y retorna un vector de n pares con el id del usuario y la distancia.
        n: int
        userX: int
        metric: string (puede ser "euclidean", "manhattan", "cosine", "pearson")
        return: vector<pair<int, float>>
        Esta funcion es utilizada para obtener las recomendaciones de un usuario.
    '''
    def knn(self, n: int, userX: int, metric: str) -> List[Tuple[int, float]]:
        pass

    '''
        La funcion recomendar recibe lo que me retorno la funcio knn 
        y ademas al usuario que queremos recomendar.
        knn_result: vector<pair<int, float>>
        idUser: int 
    '''
    def recomendar(self, knn_result: List[Tuple[int, float]], idUser: int) -> Dict[int, List[Tuple[float, int]]]:
        pass

    '''
        La funcion recomendarCancion retorna un vector de pares con el id de la cancion
        y su RATING CALCULADO.
        peliculasRecomendadasPorUsuarios: unordered_map<int,vector<pair<float, int>>>
        userARecomendar: int
    '''
    def recomendarMovie(self, peliculasRecomendadasPorUsuarios: Dict[int, List[Tuple[float, int]]], userARecomendar: int):
        pass

    '''
        printUser()
        Prints the user information to out/users.txt
        This function is used for debugging purposes.
    '''
    '''
        AgregarUsuario
    '''
    def agregarUsuario(self) -> None:
        pass

    '''
        printUser()
        Prints the user information to out/users.txt
        This function is used for debugging purposes.
    '''
    def printUser(self):
        pass

    def printMMovies(self):
        pass

    '''
        calificarPeliculas
        Allows a user to rate multiple movies at once.
        idUser: ID of the user
        peliculas: List of movie IDs and their ratings
    '''
    def calificarPeliculas(self, idUser: int, peliculas: List[Tuple[int, float]]) -> None:
        pass