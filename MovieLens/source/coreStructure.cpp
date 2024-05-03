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
	================================= BEGIN EUCLIDEAN DISTANCE=================================
*/

/*
	Complexity: O(n), where n: number of movies rated by min(userA, userB)
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
	Complexity: O(n), where n: number of movies rated by min(size(userA), size(userB))
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
//  ===================================END EUCLIDEAN DISTANCE=================================





/*
	================================= BEGIN MANHATAN DISTANCE=================================
*/
/*
	Complexity: O(n), where n: number of movies rated by min(size(userA), size(userB))
	Both
*/
void CoreStructure::details_calculateManhatanDistance(t_userId userA, t_userId userB){
	double manhatanDistance = 0.0;
	bool interseccion = false;
	cout << TAB <<DEVELOPING << "Manhatan Distance between userA: " << userA << " and userB: " << userB << endl;
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
			auto it_find = hash_movie_rating_userB.find(movie); //O(1)
			if(it_find != hash_movie_rating_userB.end()){
				// FOUND
				interseccion = true;
				manhatanDistance += abs(it->second - it_find->second);
			}
		}
	}else{
		// sizeHashUserA<= sizeHashUserB
		for(auto it = hash_movie_rating_userB.begin(); it != hash_movie_rating_userB.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userA.find(movie);
			if(it_find != hash_movie_rating_userA.end()){
				// found
				interseccion = true;
				manhatanDistance += abs(it->second - it_find->second);
			}
		}
	}
	cout << TAB <<DEVELOPING<< fixed << setprecision(10)<<"Manhatan Distance: " << manhatanDistance << endl;
	cout << TAB DEVELOPING << "Interseccion: " << interseccion << endl;
}

/*
	* Not details
	* Esta funcion se utilizara dentro de la funcion distanceBetweenUserXAndAll_by_ManhatanDistance
*/
pair<double,bool> CoreStructure::calculateManhatanDistance(t_userId userA, t_userId userB){
	double manhatanDistance = 0.0;
	bool interseccion = false;

	auto hash_movie_rating_userA = user_movie_rating[userA];
	auto hash_movie_rating_userB = user_movie_rating[userB];

	if(hash_movie_rating_userA.size() == 0 || hash_movie_rating_userB.size() == 0){
		// cout << DEVELOPING <<"UserA or UserB not found" << endl;
		// cout << DEVELOPING <<"Interseccion: " << interseccion << endl;
		return {0.0, false};
	}
	/*
		* Es eficiente comparar quien tiene menos peliculas recomendadas contra el que tiene mas peliculas
		* Para ello condicionamos con el criterio anterior
	*/
	auto sizeHashUserA = hash_movie_rating_userA.size();
	auto sizeHashUserB = hash_movie_rating_userB.size();

	if( sizeHashUserA<= sizeHashUserB){
		for(auto it = hash_movie_rating_userA.begin(); it != hash_movie_rating_userA.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userB.find(movie); //O(1)
			if(it_find != hash_movie_rating_userB.end()){
				// FOUND
				interseccion = true;
				manhatanDistance += abs(it->second - it_find->second);
			}
		}
	}else{
		// sizeHashUserA<= sizeHashUserB
		for(auto it = hash_movie_rating_userB.begin(); it != hash_movie_rating_userB.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userA.find(movie);
			if(it_find != hash_movie_rating_userA.end()){
				// found
				interseccion = true;
				manhatanDistance += abs(it->second - it_find->second);
			}
		}
	}
	return {manhatanDistance, interseccion};
}

//  ===================================END MANHATAN DISTANCE=================================





/*
	================================= BEGIN SIMILARIDAD COSENO=================================
*/
/*
	Calculo de la similaridad de coseno entre el usuario A y el usuario B
*/
void CoreStructure::details_calculateCosineSimilarity(t_userId userA, t_userId userB){
	int n = 0;
	double cosinoSimilaridad = 0.0;
	double productoPunto = 0.0;
	double longitudX = 0.0;
	double longitudY = 0.0;
	bool interseccion = false;

	cout << TAB <<DEVELOPING << "Cosino Similaridad between userA: " << userA << " and userB: " << userB << endl;
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
			auto it_find = hash_movie_rating_userB.find(movie); //O(1)
			if(it_find != hash_movie_rating_userB.end()){
				// FOUND
				interseccion = true;
				n++;
				productoPunto += (it->second * it_find->second);
				longitudX += pow(it->second, 2);
				longitudY += pow(it_find->second, 2);
			}
		}
	}else{
		// sizeHashUserA<= sizeHashUserB
		for(auto it = hash_movie_rating_userB.begin(); it != hash_movie_rating_userB.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userA.find(movie);
			if(it_find != hash_movie_rating_userA.end()){
				// found
				interseccion = true;
				n++;
				productoPunto += (it->second * it_find->second);
				longitudX += pow(it->second, 2);
				longitudY += pow(it_find->second, 2);
			}
		}
	}
	if(n == 0){
		cout << TAB <<DEVELOPING<< fixed << setprecision(10) << "Cosino Similaridad: " << 0 << endl;
		cout << TAB DEVELOPING << "Interseccion: " << interseccion << endl;
	}else{
		longitudX = sqrt(longitudX);
		longitudY = sqrt(longitudY);
		double denominador = (longitudX * longitudY);
		if(denominador == 0){
			cout << TAB <<DEVELOPING<< fixed << setprecision(10)<<"Cosino Similaridad: " << 0 << endl;
			cout << TAB DEVELOPING << "Interseccion: " << interseccion << endl;
		}else{
			cosinoSimilaridad = productoPunto / denominador;
			cout << TAB <<DEVELOPING<< fixed << setprecision(10)<<"Cosino Similaridad: " << cosinoSimilaridad << endl;
			cout << TAB DEVELOPING << "Interseccion: " << interseccion << endl;
		}
	}
}

pair<double,bool> CoreStructure::calculateCosineSimilarity(t_userId userA, t_userId userB){
	int n = 0;
	double cosinoSimilaridad = 0.0;
	double productoPunto = 0.0;
	double longitudX = 0.0;
	double longitudY = 0.0;
	bool interseccion = false;

	auto hash_movie_rating_userA = user_movie_rating[userA];
	auto hash_movie_rating_userB = user_movie_rating[userB];

	if(hash_movie_rating_userA.size() == 0 || hash_movie_rating_userB.size() == 0){
		return{0.0, false};
	}
	/*
		* Es eficiente comparar quien tiene menos peliculas recomendadas contra el que tiene mas peliculas
		* Para ello condicionamos con el criterio anterior
	*/
	auto sizeHashUserA = hash_movie_rating_userA.size();
	auto sizeHashUserB = hash_movie_rating_userB.size();
	if( sizeHashUserA<= sizeHashUserB){
		for(auto it = hash_movie_rating_userA.begin(); it != hash_movie_rating_userA.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userB.find(movie); //O(1)
			if(it_find != hash_movie_rating_userB.end()){
				// FOUND
				interseccion = true;
				n++;
				productoPunto += (it->second * it_find->second);
				longitudX += pow(it->second, 2);
				longitudY += pow(it_find->second, 2);
			}
		}
	}else{
		for(auto it = hash_movie_rating_userB.begin(); it != hash_movie_rating_userB.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userA.find(movie);
			if(it_find != hash_movie_rating_userA.end()){
				// found
				interseccion = true;
				n++;
				productoPunto += (it->second * it_find->second);
				longitudX += pow(it->second, 2);
				longitudY += pow(it_find->second, 2);
			}
		}
	}
	if(n == 0){
		return {0.0, interseccion};
	}else{
		longitudX = sqrt(longitudX);
		longitudY = sqrt(longitudY);
		double denominador = (longitudX * longitudY);
		if(denominador == 0){
			return {0.0, interseccion};
		}else{
			cosinoSimilaridad = productoPunto / denominador;
			return {cosinoSimilaridad, interseccion};
		}
	}
}
//  ===================================END SIMILARIDAD COSENO=================================





/*
	================================= BEGIN SIMILARIDAD PEARSON=================================
*/
/*
	Calculo de la correlaccion de pearson entre el usuario A y el usuario B
*/
void CoreStructure::details_calculatePearsonCorrelation(t_userId userA, t_userId userB){
	double pearsonCorrelation = 0.0;
	double n = 0;
	double xy = 0.0;
	double x = 0.0;
	double y = 0.0;
	double x2 = 0.0;
	double y2 = 0.0;
	bool interseccion = false;

	cout << TAB <<DEVELOPING << "Pearson Correlation between userA: " << userA << " and userB: " << userB << endl;
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
			auto it_find = hash_movie_rating_userB.find(movie); //O(1)
			if(it_find != hash_movie_rating_userB.end()){
				// FOUND
				interseccion = true;
				n++;
				xy += (it->second * it_find->second);
				x += it->second;
				y += it_find->second;
				x2 += pow(it->second, 2);
				y2 += pow(it_find->second, 2);
			}
		}
	}else{
		// sizeHashUserA<= sizeHashUserB
		for(auto it = hash_movie_rating_userB.begin(); it != hash_movie_rating_userB.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userA.find(movie);
			if(it_find != hash_movie_rating_userA.end()){
				// found
				interseccion = true;
				n++;
				xy += (it->second * it_find->second);
				x += it->second;
				y += it_find->second;
				x2 += pow(it->second, 2);
				y2 += pow(it_find->second, 2);
			}
		}
	}
	if(n == 0){
		cout << TAB <<DEVELOPING<< fixed << setprecision(10)<<"Pearson Correlation: " << 0 << endl;
		cout << TAB DEVELOPING << "Interseccion: " << interseccion << endl;
	}else{
		double denominador = (sqrt(x2 - pow(x, 2) / n) * sqrt(y2 - pow(y, 2) / n));
		if(denominador == 0){
			cout << TAB <<DEVELOPING<< fixed << setprecision(10)<<"Pearson Correlation: " << 0 << endl;
			cout << TAB DEVELOPING << "Interseccion: " << interseccion << endl;
			return;
		}else{
			// cout << "xy: " << xy << " x: " << x << " y: " << y << " x2: " << x2 << " y2: " << y2 << " n: " << n << endl; 
			pearsonCorrelation = (xy - (x * y) / n) / denominador;
			cout << TAB <<DEVELOPING<< fixed << setprecision(10)<<"Pearson Correlation: " << pearsonCorrelation << endl;
			cout << TAB DEVELOPING << "Interseccion: " << interseccion << endl;
		}
	}
}
pair<double,bool> CoreStructure::calculatePearsonCorrelation(t_userId userA, t_userId userB){
	double pearsonCorrelation = 0.0;
	double n = 0;
	double xy = 0.0;
	double x = 0.0;
	double y = 0.0;
	double x2 = 0.0;
	double y2 = 0.0;
	bool interseccion = false;

	auto hash_movie_rating_userA = user_movie_rating[userA];
	auto hash_movie_rating_userB = user_movie_rating[userB];

	if(hash_movie_rating_userA.size() == 0 || hash_movie_rating_userB.size() == 0){
		return{0.0,false};
	}
	/*
		* Es eficiente comparar quien tiene menos peliculas recomendadas contra el que tiene mas peliculas
		* Para ello condicionamos con el criterio anterior
	*/
	auto sizeHashUserA = hash_movie_rating_userA.size();
	auto sizeHashUserB = hash_movie_rating_userB.size();
	if( sizeHashUserA<= sizeHashUserB){
		for(auto it = hash_movie_rating_userA.begin(); it != hash_movie_rating_userA.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userB.find(movie); //O(1)
			if(it_find != hash_movie_rating_userB.end()){
				// FOUND
				interseccion = true;
				n++;
				xy += (it->second * it_find->second);
				x += it->second;
				y += it_find->second;
				x2 += pow(it->second, 2);
				y2 += pow(it_find->second, 2);
			}
		}
	}else{
		for(auto it = hash_movie_rating_userB.begin(); it != hash_movie_rating_userB.end(); it++){
			auto movie = it->first;
			auto it_find = hash_movie_rating_userA.find(movie);
			if(it_find != hash_movie_rating_userA.end()){
				interseccion = true;
				n++;
				xy += (it->second * it_find->second);
				x += it->second;
				y += it_find->second;
				x2 += pow(it->second, 2);
				y2 += pow(it_find->second, 2);
			}
		}
	}
	if(n == 0){
		return {0.0, interseccion};
	}else{
		double denominador = (sqrt(x2 - pow(x, 2) / n) * sqrt(y2 - pow(y, 2) / n));
		if(denominador == 0){
			return {0.0, interseccion};
		}else{
			pearsonCorrelation = (xy - (x * y) / n) / denominador;
			return {pearsonCorrelation, interseccion};
		}
	}
}

//  ===================================END SIMILARIDAD COSENO=================================





//----------------------------------------one-to-all----------------------------------------

void CoreStructure::distanceBetweenUserXAndAll_by_EuclideanDistance(t_userId userX, vec_id_dist_inter &distancesOfUserXWithAll){
	for(auto user: users){
		if(user != userX){
			auto [dis,inters] = calculatEuclideanDistance(userX, user);
			// distancesOfUserXWithAll.emplace_back(user,dis,inters);
			// si no hay inters
			if(inters){
				distancesOfUserXWithAll.pb({user,{dis,inters}});
				// cout << TAB <<DEVELOPING << "Euclidean Distance between userX: " << userX << " and user: " << user << " is: " << distance << endl;
			}

		}

	}
	sort(distancesOfUserXWithAll.begin(), distancesOfUserXWithAll.end(), [](const auto &a, const auto &b){
		// ordenar  por distancias que se encuentra en a.second.first
		return a.second.first < b.second.first;
	});
}

void CoreStructure::distanceBetweenUserXAndAll_by_ManhatanDistance(t_userId userX, vec_id_dist_inter &vec){
	for(auto user: users){
		if(user != userX){
			auto [dis,inters] = calculateManhatanDistance(userX, user);
			if(inters){
				vec.pb({user,{dis,inters}});
			}
		}
	}
	sort(vec.begin(), vec.end(), [](const auto &a, const auto &b){
		// ordenar  por distancias que se encuentra en a.second.first
		return a.second.first < b.second.first;
	});
}

void CoreStructure::distanceBetweenUserXAndAll_by_CosineSimilarity(t_userId userX, vec_id_dist_inter &vec){
	for(auto user: users){
		if(user != userX){
			auto [dis,inters] = calculateCosineSimilarity(userX, user);
			if(inters){
				vec.pb({user,{dis,inters}});
			}
		}
	}
	sort(vec.begin(), vec.end(), [](const auto &a, const auto &b){
		// ordenar  por distancias que se encuentra en a.second.first
		return a.second.first < b.second.first;
	});
}

void CoreStructure::distanceBetweenUserXAndAll_by_PearsonCorrelation(t_userId userX, vec_id_dist_inter &vec){
	for(auto user: users){
		if(user != userX){
			auto [dis,inters] = calculatePearsonCorrelation(userX, user);
			if(inters){
				vec.pb({user,{dis,inters}});
			}
		}
	}
	sort(vec.begin(), vec.end(), [](const auto &a, const auto &b){
		// ordenar  por distancias que se encuentra en a.second.first
		return a.second.first < b.second.first;
	});
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




/*
	================================= BEGIN KNN=================================
*/

void CoreStructure::knn_by_euclideanDistance(t_userId userX, int n){
	vec_id_dist_inter distancesOfUserXWithAll;
	Timer timer;
	timer.startt();
	distanceBetweenUserXAndAll_by_EuclideanDistance(userX, distancesOfUserXWithAll);
	cout << TAB << " [CORESTRUCTURE]" << "Total Time in distanceBetweenUserXAndAll_by_EuclideanDistance: " << timer.getCurrentTime() << endl;
	cout << TAB << " [CORESTRUCTURE]" << "Total all users: " << distancesOfUserXWithAll.size() << endl;
	// cout << TAB <<DEVELOPING << "K-NN with Euclidean Distance between userX: " << userX << " and all users" << endl;
	auto sizeVector = distancesOfUserXWithAll.size();
	if(sizeVector == 0){
		cout << TAB <<DEVELOPING << "distancesOfUserXWithAll is equal 0" << endl;
		return;
	}
	out_knn_euclidean.open("../out/knn_euclidean.txt");
	out_knn_euclidean << "User-Distance-Interseccion" << endl;
	if(n >= sizeVector){
		// cout << TAB <<DEVELOPING << "K-NN with Euclidean Distance between userX: " << userX << " and all users" << endl;
		// cout << TAB <<DEVELOPING << "n: " << n << " is greater than the number of users: " << sizeVector << endl;
		// cout << TAB <<DEVELOPING << "The result will be the same as the number of users" << endl;
		// n = sizeVector;
		// mostrat todos los usuarios
		for(auto x: distancesOfUserXWithAll){
			// cout << TAB <<DEVELOPING << "User: " << x.first << " Distance: " << x.second.first << " Interseccion: " << x.second.second << endl;
			out_knn_euclidean << fixed << setprecision(10) << x.first << " " << x.second.first << " " << x.second.second << endl;
		}
	}else{
		// mostrar solo los n primeros
		for(int e = 0 ; e < n; e++){
			out_knn_euclidean << fixed << setprecision(10) << distancesOfUserXWithAll[e].first << " " << distancesOfUserXWithAll[e].second.first << " " << distancesOfUserXWithAll[e].second.second << endl;
		}
	}
	out_knn_euclidean.close();

}
//  ===================================END  KNN=================================
