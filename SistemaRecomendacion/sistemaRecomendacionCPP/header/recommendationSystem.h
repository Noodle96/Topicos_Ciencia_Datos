#ifndef RECOMENDATION_SYSTEM_H
#define RECOMENDATION_SYSTEM_H

#include <iostream>
#include <iomanip>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <fstream>
#include <cmath>
#include <algorithm>
#include <string>

using namespace std;
const float DISTANCIA_MAXIMA = 1e9;

// DEFINICION DE UMBRALES
const float UMBRAL_RATING_VECINO = 3.0;
const int UMBRAL_PELICULAS_COMUNES = 5;
const float UMBRAL_COSINE_SIMILARITY = 0.5; // Umbral para similitud del coseno
const float UMBRAL_PEARSON_CORRELATION = 0.5; // Umbral para correlación de Pearson



class RecommendationSystem {
    private:
        unordered_map<int, unordered_map<int, float>> user_movie_ratings;
        unordered_set<int> users;
        unordered_map<int, pair<string, vector<string>>> movies;
        ofstream cout_debug_file;
        ofstream cout_debug_file_01_validar_distancias,
                 cout_debug_file_02_calcular_knn,
                 cout_debug_file_03_calcular_recomendaciones,
                 cout_debug_file_04_peliculas_recomendar;
    public:
        RecommendationSystem();
		~RecommendationSystem();

        // implementar una funcion get para usar cout_debug_file_01_validar_distancias fuera de la clase
        ofstream& getCoutDebugFile01ValidarDistancias(){
            return cout_debug_file_01_validar_distancias;
        }
        ofstream& getCoutDebugFile02CalcularKNN(){
            return cout_debug_file_02_calcular_knn;
        }
        ofstream& getCoutDebugFile03CalcularRecomendaciones(){
            return cout_debug_file_03_calcular_recomendaciones;
        }
        ofstream& getCoutDebugFile04PeliculasRecomendar(){
            return cout_debug_file_04_peliculas_recomendar;
        }

        /*
			add to hash to hash
            addRatingAndUser(idUser, idMovie, rating, timestamp)
            idUser: int
            idMovie: int
            rating: float
            timestamp: string
		*/
		void addRatingAndUser(int, int, float, string);

        /*
            addMovie(idMovie, title, genres)
            idMovie: int
            title: string
            genres: vector<string>
        */
        void addMovie(int, const string, const vector<string>&);

        /*
            Funcion que retorna el numero de peliculas que ha calificado un usuario
            userId: int
            return: int
        */
        int getNumberOfRatedMovies(int);
        /*
			Calculo de la distancia euclidiana entre el usuario A y el usuario B
            userA: int
            userB: int
            commonMovies: int&
            return: pair<float, bool>
		*/        
		pair<float, bool> calculateEuclideanDistance(int, int, int &);
        pair<float, bool> calculateEuclideanDistanceDebug(int, int, int &);

        /*
            Calculo de la distancia de manhattan entre el usuario A y el usuario B
            userA: int
            userB: int
            commonMovies: int&
            return: pair<float, bool>
        */
       pair<float, bool> calculateManhattanDistance(int, int, int &);
       pair<float, bool> calculateManhattanDistanceDebug(int, int, int &);


       /*
        Calculo de la similitud del coseno entre el usuario A y el usuario B
        userA: int
        userB: int
        commonMovies: int&
        return: pair<float, bool>
       */
        pair<float, bool> calculateCosineSimilarity(int, int, int &);  
        pair<float, bool> calculateCosineSimilarityDebug(int, int, int &);      


        /*
            Calculo del coeficiente de correlacion de pearson entre el usuario A y el usuario B,
            mediante la aproximacion de pearson
            userA: int
            userB: int
            commonMovies: int&
            return: pair<float, bool>
        */
        pair<float, bool> calculatePearsonCorrelation(int, int, int &);
        pair<float, bool> calculatePearsonCorrelationDebug(int, int, int &);


        /*
            Funcion knn que calcula la distancia del usuarioX entre todos los usuarios
            y retorna un vector de n pares con el id del usuario y la distancia.
            n: int
            userX: int
            metric: string (puede ser "euclidean", "manhattan", "cosine", "pearson")
            return: vector<pair<int, float>>
            Esta funcion es utilizada para obtener las recomendaciones de un usuario.
        */
        vector<pair<int, float>> knn(int, int, string);

        /*
            La funcion recomendar recibe lo que me retorno la funcio knn 
            y ademas al usuario que queremos recomendar.
            knn_result: vector<pair<int, float>>
            idUser: int 
        */
        unordered_map<int, vector<pair<float, int>>> recomendar(vector<pair<int, float>>&, int);

        /*
            La funcion recomendarCancion retorna un vector de pares con el id de la cancion
            y su RATING CALCULADO.
            peliculasRecomendadasPorUsuarios: unordered_map<int,vector<pair<float, int>>>
            userARecomendar: int
        */
        void recomendarMovie(unordered_map<int,vector<pair<float, int>>> &, int);

        /*
            printUser()
            Prints the user information to out/users.txt
            This function is used for debugging purposes.
        */
        void printUser();
};

#endif // RECOMENDATION_SYSTEM_H