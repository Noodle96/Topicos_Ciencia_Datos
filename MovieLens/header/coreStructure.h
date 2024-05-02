#ifndef CORESTRUCTURE_H
#define CORESTRUCTURE_H

#include "macros.h"

class CoreStructure{
	private:
		unordered_map<t_userId, unordered_map<t_movieId,t_rating> > user_movie_rating;
		unordered_set<t_userId> users;
		ofstream out_users;
	public:
		CoreStructure(){}
		~CoreStructure(){}
		/*
			add to hash to hash
		*/
		void add(t_userId, t_movieId, t_rating, t_timestamp);

		/*
			Calculo de la distancia euclidiana entre el usuario A y el usuario B
		*/
		void details_calculatEuclideanDistance(t_userId, t_userId);
		pair<double, bool> calculatEuclideanDistance(t_userId, t_userId);

		/*
			Calculo de la distancia euclidiana entre el Usuario X, contra todos los demas usuarios
		*/
		double distanceBetweenUserXAndAll_by_EuclideanDistance(t_userId);
		
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


		void print_users();
};
#endif // CORESTRUCTURE_H