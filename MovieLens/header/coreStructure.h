#ifndef CORESTRUCTURE_H
#define CORESTRUCTURE_H

#include "macros.h"

class CoreStructure{
	private:
		unordered_map<t_userId, unordered_map<t_movieId,t_rating> > user_movie_rating;
		unordered_set<t_userId> users;
		ofstream out_users;
		ofstream out_knn_euclidean;
	public:
		CoreStructure(){}
		~CoreStructure(){}
		/*
			add to hash to hash
		*/
		void add(t_userId, t_movieId, t_rating, t_timestamp);

		void getCommonMovies(t_userId, t_userId, vector<t_movieId> &);

		/*
			Calculo de la distancia euclidiana entre el usuario A y el usuario B
		*/
		void details_calculatEuclideanDistance(t_userId, t_userId);
		pair<double, bool> calculatEuclideanDistance(t_userId, t_userId);


		/*
			Calculo de la distancia de manhatan entre el usuario A y el usuario B
		*/
		void details_calculateManhatanDistance(t_userId, t_userId);
		pair<double,bool> calculateManhatanDistance(t_userId, t_userId);


		/*
			Calculo de la similaridad de coseno entre el usuario A y el usuario B
		*/
		void details_calculateCosineSimilarity(t_userId, t_userId);
		pair<double,bool> calculateCosineSimilarity(t_userId, t_userId);


		/*
			Calculo de la correlaccion de pearson entre el usuario A y el usuario B
		*/
		void details_calculatePearsonCorrelation(t_userId, t_userId);
		pair<double,bool> calculatePearsonCorrelation(t_userId, t_userId);

		/*
			Calculo de la distancia euclidiana entre el Usuario X, contra todos los demas usuarios
		*/
		void distanceBetweenUserXAndAll_by_EuclideanDistance(t_userId,vec_id_dist_inter &);
		
		/*
			Calculo de la distancia de manhatan entre el Usuario X, contra todos los demas usuarios
		*/
		void distanceBetweenUserXAndAll_by_ManhatanDistance(t_userId);

		/*
			Calculo de la similaridad de coseno entre el Usuario X, contra todos los demas usuarios
		*/
		void distanceBetweenUserXAndAll_by_CosineSimilarity(t_userId);

		/*
			Calculo de la correlaccion de pearson entre el Usuario X, contra todos los demas usuarios
		*/
		void distanceBetweenUserXAndAll_by_PearsonCorrelation(t_userId);

		/*
			K-NN con la distancia euclidiana
		*/
		void knn_by_euclideanDistance(t_userId, int);

		void print_users();

		void query_rating(t_userId userId, t_movieId movieId){
			if(user_movie_rating.find(userId) != user_movie_rating.end()){
				if(user_movie_rating[userId].find(movieId) != user_movie_rating[userId].end()){
					cout << "Rating: " << user_movie_rating[userId][movieId] << endl;
				}else{
					cout << "Movie not found" << endl;
				}
			}else{
				cout << "User not found" << endl;
			}
		}
};
#endif // CORESTRUCTURE_H