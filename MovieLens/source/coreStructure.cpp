#include "../header/coreStructure.h"
#include "../header/timer.h"
void CoreStructure::add(t_userId userId, t_movieId movieId, t_rating rating, t_timestamp timestamp){
	user_movie_rating[userId][movieId] = rating;
	users.insert(userId);
}

void CoreStructure::getCommonMovies(t_userId userA, t_userId userB, vector<t_movieId> &vec){
	auto hash_movie_rating_userA = user_movie_rating[userA];
	auto hash_movie_rating_userB = user_movie_rating[userB];

	auto sizeHashUserA = hash_movie_rating_userA.size();
	auto sizeHashUserB = hash_movie_rating_userB.size();
	// cout << "sizeHashUserA: " << sizeHashUserA << " sizeHashUserB: " << sizeHashUserB << endl;

	//criterio para recorrer solo el hash con el menor tamaño
	if(sizeHashUserA <= sizeHashUserB){
		for(auto it = hash_movie_rating_userA.begin() ;it != hash_movie_rating_userA.end() ; it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userB.find(movie);
			if(it_find != hash_movie_rating_userB.end()){
				// found
				vec.pb(movie);
			}
		}
	}else{
		for(auto it = hash_movie_rating_userB.begin() ;it != hash_movie_rating_userB.end() ; it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userA.find(movie);
			if(it_find != hash_movie_rating_userA.end()){
				// found
				vec.pb(movie);
			}
		}
	}
}

/*
	Complexity: O(n), where n: number of movies rated by userA
*/
void CoreStructure::details_calculatEuclideanDistance(t_userId userA, t_userId userB){
	double euclideanDistance = 0.0;
	bool interseccion = false;
	cout << TAB <<DEVELOPING << "Euclidean Distance between userA: " << userA << " and userB: " << userB << endl;
	// usuarios validos
	auto hash_movie_rating_userA = user_movie_rating[userA];
	auto hash_movie_rating_userB = user_movie_rating[userB];

	if(hash_movie_rating_userA.size() == 0 || hash_movie_rating_userB.size() == 0){
		cout << DEVELOPING <<"UserA or UserB not found" << endl;
		cout << DEVELOPING <<"Interseccion: " << interseccion << endl;
		return;
	}
	/*
		* Es eficiente comparar quien tiene menos peliculas recomendadas contra el que tiene mas peliculas
		* Para ello condicionamos con el criterio anterior
	*/
	auto sizeHashUserA = hash_movie_rating_userA.size();
	auto sizeHashUserB = hash_movie_rating_userB.size();
	cout << TAB <<DEVELOPING << "SizeHashUserA: " << sizeHashUserA << " SizeHashUserB: " << sizeHashUserB << endl;
	if( sizeHashUserA<= sizeHashUserB){
		for(auto it = hash_movie_rating_userA.begin(); it != hash_movie_rating_userA.end(); it++){
			// cout << it->first << " " << it->second << endl;
			auto movie = it->first;
			auto it_find = hash_movie_rating_userB.find(movie);
			if(it_find != hash_movie_rating_userB.end()){
				// found
				// cout << "Movie: " << movie << " Rating userA: " << it->second << " Rating userB: " << it_find->second << endl;
				// podriamos optimizar
				interseccion = true;
				euclideanDistance += pow(it->second - it_find->second, 2);
			}
		}
	}else{
		// sizeHashUserA<= sizeHashUserB
		for(auto it = hash_movie_rating_userB.begin(); it != hash_movie_rating_userB.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userA.find(movie);
			if(it_find != hash_movie_rating_userA.end()){
				// found
				// cout << "Movie: " << movie << " Rating userA: " << it->second << " Rating userB: " << it_find->second << endl;
				// podriamos optimizar
				interseccion = true;
				euclideanDistance += pow(it->second - it_find->second, 2);
			}
		}
	}
	euclideanDistance = sqrt(euclideanDistance);
	cout << TAB <<DEVELOPING<< fixed << setprecision(10)<<"Euclidean Distance: " << euclideanDistance << endl;
	cout << TAB DEVELOPING << "Interseccion: " << interseccion << endl;
}

/*
	Complexity: O(n), where n: number of movies rated by userA
*/
pair<double, bool> CoreStructure::calculatEuclideanDistance(t_userId userA, t_userId userB){
	double euclideanDistance = 0.0;
	bool interseccion = false;
	// usuarios validos
	auto hash_movie_rating_userA = user_movie_rating[userA];
	auto hash_movie_rating_userB = user_movie_rating[userB];

	if(hash_movie_rating_userA.size() == 0 || hash_movie_rating_userB.size() == 0){
		// cout << DEVELOPING <<"UserA or UserB not found" << endl;
		return {0.0,false};
	}
	/*
		* Es eficiente comparar quien tiene menos peliculas recomendadas contra el que tiene mas peliculas
		* Para ello condicionamos con el criterio anterior
	*/
	auto sizeHashUserA = hash_movie_rating_userA.size();
	auto sizeHashUserB = hash_movie_rating_userB.size();
	// cout << TAB <<DEVELOPING << "SizeHashUserA: " << sizeHashUserA << " SizeHashUserB: " << sizeHashUserB << endl;
	if( sizeHashUserA<= sizeHashUserB){
		for(auto it = hash_movie_rating_userA.begin(); it != hash_movie_rating_userA.end(); it++){
			// cout << it->first << " " << it->second << endl;
			auto movie = it->first;
			auto it_find = hash_movie_rating_userB.find(movie);
			if(it_find != hash_movie_rating_userB.end()){
				// found
				// cout << "Movie: " << movie << " Rating userA: " << it->second << " Rating userB: " << it_find->second << endl;
				// podriamos optimizar
				interseccion = true;
				euclideanDistance += pow(it->second - it_find->second, 2);
			}
		}
	}else{
		// sizeHashUserA<= sizeHashUserB
		for(auto it = hash_movie_rating_userB.begin(); it != hash_movie_rating_userB.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userA.find(movie);
			if(it_find != hash_movie_rating_userA.end()){
				// found
				// cout << "Movie: " << movie << " Rating userA: " << it->second << " Rating userB: " << it_find->second << endl;
				// podriamos optimizar
				interseccion = true;
				euclideanDistance += pow(it->second - it_find->second, 2);
			}
		}
	}
	euclideanDistance = sqrt(euclideanDistance);
	return {euclideanDistance, interseccion};
}

//----------------------------------------one-to-all----------------------------------------

void CoreStructure::distanceBetweenUserXAndAll_by_EuclideanDistance(t_userId userX, vec_id_dist_inter &distancesOfUserXWithAll){
	for(auto user: users){
		if(user != userX){
			auto [dis,inters] = calculatEuclideanDistance(userX, user);
			// distancesOfUserXWithAll.emplace_back(user,dis,inters);
			distancesOfUserXWithAll.pb({user,{dis,inters}});
			// cout << TAB <<DEVELOPING << "Euclidean Distance between userX: " << userX << " and user: " << user << " is: " << distance << endl;
		}

	}
	sort(distancesOfUserXWithAll.begin(), distancesOfUserXWithAll.end(), [](const auto &a, const auto &b){
		// ordenar  por distancias que se encuentra en a.second.first
		return a.second.first < b.second.first;
	});
}

void CoreStructure::distanceBetweenUserXAndAll_by_ManhatanDistance(t_userId userX){
	;
}

void CoreStructure::distanceBetweenUserXAndAll_by_CosineSimilarity(t_userId userX){
	;
}

void CoreStructure::distanceBetweenUserXAndAll_by_PearsonCorrelation(t_userId userX){
	;
}
//--------------------------------------------------------------------------------------------


//--------------------------------------------OUTS--------------------------------------------
void CoreStructure::print_users(){
	out_users.open("../out/printUsers.txt");
	for(auto x: users){
		out_users << x << endl;
	}
	out_users << "Total users: " << users.size() << endl;
}
//--------------------------------------------------------------------------------------------