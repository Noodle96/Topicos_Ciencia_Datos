#ifndef CORESTRUCTURE_H
#define CORESTRUCTURE_H

#include "macros.h"

class CoreStructure{
	private:
		unordered_map<t_userId, unordered_map<t_movieId,t_rating> > user_movie_rating;
		unordered_set<t_userId> users;
		unordered_map<t_movieId, pair<t_movieName, vector<t_movieGenre>> > movies;
		ofstream out_users,out_movies;
		ofstream out_knn_euclidean;
	public:
		CoreStructure();
		~CoreStructure(){}
		/*
			!add to hash to hash
		*/
		void add(t_userId, t_movieId, t_rating, t_timestamp);

		void getCommonMovies(t_userId, t_userId, vector<t_movieId> &);

		/*
			!Calculo de la distancia euclidiana entre el usuario A y el usuario B
		*/
		void details_calculatEuclideanDistance(t_userId, t_userId);
		pair<double, bool> calculatEuclideanDistance(t_userId, t_userId, int &);


		/*
			!Calculo de la distancia de manhatan entre el usuario A y el usuario B
		*/
		void details_calculateManhatanDistance(t_userId, t_userId);
		pair<double,bool> calculateManhatanDistance(t_userId, t_userId);


		/*
			!Calculo de la similaridad de coseno entre el usuario A y el usuario B
		*/
		void details_calculateCosineSimilarity(t_userId, t_userId);
		pair<double,bool> calculateCosineSimilarity(t_userId, t_userId);


		/*
			!Calculo de la correlaccion de pearson entre el usuario A y el usuario B
		*/
		void details_calculatePearsonCorrelation(t_userId, t_userId);
		pair<double,bool> calculatePearsonCorrelation(t_userId, t_userId);

		/*
			!Calculo de la distancia euclidiana entre el Usuario X, contra todos los demas usuarios
		*/
		void distanceBetweenUserXAndAll_by_EuclideanDistance(t_userId,vec_id_dist_inter &);
		
		/*
			!Calculo de la distancia de manhatan entre el Usuario X, contra todos los demas usuarios
		*/
		void distanceBetweenUserXAndAll_by_ManhatanDistance(t_userId, vec_id_dist_inter &);

		/*
			!Calculo de la similaridad de coseno entre el Usuario X, contra todos los demas usuarios
		*/
		void distanceBetweenUserXAndAll_by_CosineSimilarity(t_userId, vec_id_dist_inter &);

		/*
			!Calculo de la correlaccion de pearson entre el Usuario X, contra todos los demas usuarios
		*/
		void distanceBetweenUserXAndAll_by_PearsonCorrelation(t_userId, vec_id_dist_inter &);

		/*
			!K-NN con la distancia euclidiana
		*/
		void knn_by_euclideanDistance(t_userId, int);

		/*
			!Guardar los usuarios en el archivo printUsers.txt
		*/
		void print_users();

		/*
			!Guardar las peliculas en el archivo printMovies.txt
		*/
		void print_movies();

		/*
			!Consultar el rating de una pelicula dado el usuario(id) y la pelicula(id)
		*/
		void query_rating(t_userId, t_movieId);

		/*
			!Consultar las peliculas que ha visto un usuario dado el id
		*/
		void query_movies(t_userId);
};
#endif // CORESTRUCTURE_H