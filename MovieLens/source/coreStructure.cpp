#include "../header/coreStructure.h"
#include "../header/timer.h"



// ~ =================================BEGIN CONSTRUCTOR======================================
CoreStructure::CoreStructure(){
	// * Load rating.csv
	// atributos rating.csv
	t_userId userId;
	t_movieId movieId;
	t_rating rating;
	t_timestamp timestamp;
	char delimiter = ',';
	string linea;
	Timer timer;
	// ifstream archivo_csv("data/ml-20m/temporal.csv");


	cout << "[CORESTRUCTURE] Load rating.csv" << endl;
	timer.startt();
	std::ifstream archivo_csv("../data-ml-latest/ratings.csv");
	getline(archivo_csv,linea); // omitir la linea de cabecera
	// Verificar si el archivo se abrió correctamente
	if (archivo_csv.is_open()) {
		while (std::getline(archivo_csv, linea)) {
			std::istringstream ss(linea);// [1]30seg
			ss >> userId >>delimiter>> movieId >> delimiter>> rating >>delimiter>> timestamp;
			// mapa[userId]++;
			// coreStructure.add(userId, movieId, rating, timestamp); //[1] 30seg
			add(userId, movieId, rating, timestamp); //[1] 30seg
			// cout << userId << " " << movieId << " " << rating << " " << timestamp << endl;
		}
		archivo_csv.close();
		cout << TAB << "[CORESTRUCTURE] Total time to load rating.csv: " << timer.getCurrentTime() << endl;
		cout << TAB << "[CORESTRUCTURE] Load rating.csv [OK]" << endl;

	} else {
		std::cerr << "Error al abrir el archivo CSV" << std::endl;
	}

	// * Load movies.csv
	t_movieName movieName;
	t_movieGenre movieGenres;
	cout << "[CORESTRUCTURE] Load movies.csv" << endl;
	timer.startt();
	std::ifstream archivo_csv_movies("../data-ml-latest/movies.csv");
	getline(archivo_csv_movies,linea); // omitir la linea de cabecera
	// Verificar si el archivo se abrió correctamente
	if (archivo_csv_movies.is_open()) {
		while (std::getline(archivo_csv_movies, linea)) {
			istringstream iss(linea);
			// Extract ID
			std::string idStr;
			if (std::getline(iss, idStr, ',')) {
				movieId = std::stoi(idStr);
			}

			// Extract movie title
			std::string titleStr;
			if (std::getline(iss, titleStr, ',')) {
				movieName = titleStr;
			}

			// procesar luego los generos !important
			// Extract genres
			// std::string genreStr;
			// while (std::getline(iss, genreStr, ',')) {
			// 	genreStr.erase(std::remove_if(genreStr.begin(), genreStr.end(), isspace), genreStr.end());
			// 	movie.genres.push_back(genreStr);
			// }
			// cout << "movieId: " << movieId << " movieName: " << movieName << endl;
			movies[movieId] = {movieName, {}};
		}
		archivo_csv_movies.close();
		cout << TAB << "[CORESTRUCTURE] Total time to load movies.csv: " << timer.getCurrentTime() << endl;
		cout << TAB << "[CORESTRUCTURE] Load movies.csv [OK]" << endl;
	} else {
		std::cerr << "Error al abrir el archivo CSV" << std::endl;
	}

}
// ~ =================================BEGIN CONSTRUCTOR======================================



// ~ =================================BEGIN MAIN FUNCTIONS======================================

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
// ~ =================================END MAIN FUNCTIONS======================================





/*
	~================================= BEGIN EUCLIDEAN DISTANCE=================================
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
pair<double, bool> CoreStructure::calculatEuclideanDistance(t_userId userA, t_userId userB, int &commom_movies){
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
				commom_movies++;
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
				commom_movies++;
				interseccion = true;
				euclideanDistance += pow(it->second - it_find->second, 2);
			}
		}
	}
	euclideanDistance = sqrt(euclideanDistance);
	return {euclideanDistance, interseccion};
}
//  ~===================================END EUCLIDEAN DISTANCE=================================





/*
	~================================= BEGIN MANHATAN DISTANCE=================================
*/
/*
	* Complexity: O(n), where n: number of movies rated by min(size(userA), size(userB))
	* Both
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
pair<double,bool> CoreStructure::calculateManhatanDistance(t_userId userA, t_userId userB, int &commom_movies){
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
				commom_movies++;
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
				commom_movies++;
				interseccion = true;
				manhatanDistance += abs(it->second - it_find->second);
			}
		}
	}
	return {manhatanDistance, interseccion};
}

//~  ===================================END MANHATAN DISTANCE=================================





/*
	~================================= BEGIN SIMILARIDAD COSENO=================================
*/
/*
	* Calculo de la similaridad de coseno entre el usuario A y el usuario B
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

pair<double,bool> CoreStructure::calculateCosineSimilarity(t_userId userA, t_userId userB, int &commom_movies){
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
				commom_movies++;
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
				commom_movies++;
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
//  ~===================================END SIMILARIDAD COSENO=================================





/*
	~================================= BEGIN SIMILARIDAD PEARSON=================================
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
pair<double,bool> CoreStructure::calculatePearsonCorrelation(t_userId userA, t_userId userB, int & commom_movies){
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
				commom_movies++;
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
				commom_movies++;
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

//  ~===================================END SIMILARIDAD COSENO=================================





/*
	~===================== BEGIN DISTANCE BETWEEN USERX AND ALL ===============================
*/
void CoreStructure::distanceBetweenUserXAndAll_by_EuclideanDistance(t_userId userX, vec_id_dist_inter &distancesOfUserXWithAll){
	int common_movies;
	for(auto user: users){
		if(user != userX){
			common_movies = 0;
			auto [dis,inters] = calculatEuclideanDistance(userX, user, common_movies);
			// distancesOfUserXWithAll.emplace_back(user,dis,inters);
			// si no hay inters
			if(inters && common_movies >= UMBRAL_MINIMUM_PELICULAS_COMMON){
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
	int common_movies;
	for(auto user: users){
		if(user != userX){
			common_movies = 0;
			auto [dis,inters] = calculateManhatanDistance(userX, user,common_movies);
			if(inters && common_movies >= UMBRAL_MINIMUM_PELICULAS_COMMON){
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
	int common_movies;
	for(auto user: users){
		if(user != userX){
			common_movies = 0;
			auto [dis,inters] = calculateCosineSimilarity(userX, user, common_movies);
			if(inters && common_movies >= UMBRAL_MINIMUM_PELICULAS_COMMON){
				vec.pb({user,{dis,inters}});
			}
		}
	}
	sort(vec.begin(), vec.end(), [](const auto &a, const auto &b){
		// ordenar  por distancias que se encuentra en a.second.first
		return a.second.first > b.second.first;
	});
}

void CoreStructure::distanceBetweenUserXAndAll_by_PearsonCorrelation(t_userId userX, vec_id_dist_inter &vec){
	int common_movies;
	for(auto user: users){
		if(user != userX){
			common_movies = 0;
			auto [dis,inters] = calculatePearsonCorrelation(userX, user, common_movies);
			if(inters && common_movies >= UMBRAL_MINIMUM_PELICULAS_COMMON){
				vec.pb({user,{dis,inters}});
			}
		}
	}
	sort(vec.begin(), vec.end(), [](const auto &a, const auto &b){
		// ordenar  por distancias que se encuentra en a.second.first
		return a.second.first < b.second.first;
	});
}
//	~===================== BEGIN DISTANCE BETWEEN USERX AND ALL ===============================





// ~ =======================================BEGIN OUTS=========================================
void CoreStructure::print_users(){
	out_users.open("../out/printUsers.txt");
	for(auto x: users){
		out_users << x << endl;
	}
	out_users << "Total users: " << users.size() << endl;
}

void CoreStructure::print_movies(){
	out_movies.open("../out/printMovies.txt");
	for(auto x: movies){
		out_movies << x.first << " " << x.second.first << endl;
	}
	out_movies << "Total movies: " << movies.size() << endl;

}
//~ ========================================END OUTS===========================================





/*
	~========================================= BEGIN KNN========================================
*/

void CoreStructure::knn_by_euclideanDistance(t_userId userX, int n){
	vec_id_dist_inter distancesOfUserXWithAll;
	Timer timer;
	timer.startt();
	distanceBetweenUserXAndAll_by_EuclideanDistance(userX, distancesOfUserXWithAll);
	cout << TAB << " [CORESTRUCTURE]" << "Total Time in distanceBetweenUserXAndAll_by_EuclideanDistance: " << timer.getCurrentTime() << endl;
	cout << TAB << " [CORESTRUCTURE]" << "Total all users with restrictions(DISJOINT, UMBRAL): " << distancesOfUserXWithAll.size() << endl;
	// cout << TAB <<DEVELOPING << "K-NN with Euclidean Distance between userX: " << userX << " and all users" << endl;
	auto sizeVector = distancesOfUserXWithAll.size();
	if(sizeVector == 0){
		cout << TAB <<DEVELOPING << "distancesOfUserXWithAll is equal 0" << endl;
		return;
	}

	vector<t_userId> kNN;

	// MOSTRAR LO SIGUIENTE:
	// 1.- Guardar en el archivo ../out/knn_euclidean.txt [Usuario, Distancia, Interseccion]
	ofstream out_knn_euclidean;
	cout << TAB << " [CORESTRUCTURE]" << "Begin Saving in ../out/knn_euclidean.txt" << endl;
	out_knn_euclidean.open("../out/knn_euclidean.txt");
	out_knn_euclidean << "User-Distance-Interseccion" << endl;
	if(n >= sizeVector){
		// cout << TAB <<DEVELOPING << "K-NN with Euclidean Distance between userX: " << userX << " and all users" << endl;
		// cout << TAB <<DEVELOPING << "n: " << n << " is greater than the number of users: " << sizeVector << endl;
		// cout << TAB <<DEVELOPING << "The result will be the same as the number of users" << endl;
		// n = sizeVector;
		// mostrat todos los usuarios
		for(auto x: distancesOfUserXWithAll){
			// Para analizar despues
			kNN.pb(x.first);
			// cout << TAB <<DEVELOPING << "User: " << x.first << " Distance: " << x.second.first << " Interseccion: " << x.second.second << endl;
			out_knn_euclidean << fixed << setprecision(10) << x.first << " " << x.second.first << " " << x.second.second << endl;
		}
	}else{
		// mostrar solo los n primeros
		for(int e = 0 ; e < n; e++){
			// Para analizar despues
			kNN.pb(distancesOfUserXWithAll[e].first);
			out_knn_euclidean << fixed << setprecision(10) << distancesOfUserXWithAll[e].first << " " << distancesOfUserXWithAll[e].second.first << " " << distancesOfUserXWithAll[e].second.second << endl;
		}
	}
	out_knn_euclidean.close();
	cout << TAB << " [CORESTRUCTURE]" << "End Saving in ../out/knn_euclidean.txt" << endl;

	/*
		? 2.- Por cada Usuario, mostrar las peliculas y el puntaje que le da
		?     ordenados por rating.
		?     en el archivo ../out/knn_euclidean_[user-peliculas-puntaje].txt
	*/

	unordered_map<t_userId, vector<pair<t_movieId, t_rating>> > recommender;
	cout << TAB << " [CORESTRUCTURE]" << "Begin Saving in ../out/knn_euclidean_[user-peliculas_puntaje].txt" << endl;
	ofstream out_knn_euclidean_user_peliculas_puntaje;
	out_knn_euclidean_user_peliculas_puntaje.open("../out/knn_euclidean_[user-peliculas_puntaje].txt");
	for(auto x: kNN){
		auto hash_movie_rating_userX = user_movie_rating[x];
		out_knn_euclidean_user_peliculas_puntaje << "User: " << x << endl;
		out_knn_euclidean_user_peliculas_puntaje << "Peliculas-Puntaje (" << hash_movie_rating_userX.size()<< " rows founded)"<<  endl;
		for(auto it = hash_movie_rating_userX.begin(); it != hash_movie_rating_userX.end(); it++){
			// auto movieName = movies[it->first].first;
			// out_knn_euclidean_user_peliculas_puntaje << "[" <<it->first << "]-[" << movieName<< "] => "<<  it->second << endl;
			out_knn_euclidean_user_peliculas_puntaje << it->first << " " << it->second << endl;

			// *VALIDANDO EL SEGUNDO UMBRAL
			if(it->second >= UMBRAL_MINIMUM_RATING){
				recommender[x].pb({it->first, it->second});
			}
		}
		out_knn_euclidean << endl;
	}
	out_knn_euclidean_user_peliculas_puntaje.close();
	cout << TAB << " [CORESTRUCTURE]" << "End Saving in ../out/knn_euclidean_[user-peliculas_puntaje].txt" << endl;


	/*
		? 3.- Finalemte mostrar las peliculas que se recomendaran al usuario X, en base
		?     al umbral de UMBRAL_MINIMUM_RATING y UMBRAL_MINIMUM_PELICULAS_COMMON(ya filtrado
		?     con anterioridad)
		?	 en el archivo ../out/knn_euclidean_[recomendation].txt
	*/
	for(auto x:kNN){
		sort(recommender[x].begin(), recommender[x].end(), [](const auto &a, const auto &b){
			return a.second > b.second;
		});
	}
	cout << TAB << " [CORESTRUCTURE]" << "Begin Saving in ../out/knn_euclidean_[recomendation].txt" << endl;
	ofstream out_knn_euclidean_recomendation;
	out_knn_euclidean_recomendation.open("../out/knn_euclidean_[recomendation].txt");
	for(auto x: kNN){
		out_knn_euclidean_recomendation << "User: " << x << endl;
		out_knn_euclidean_recomendation << "Recomendation (" << recommender[x].size() << " rows)" << endl;
		for(auto it: recommender[x]){
			// auto movieName = movies[it.first].first;
			// out_knn_euclidean_recomendation << "[" << it.first << "]-[" << movieName << "] => " << it.second << endl;
			out_knn_euclidean_recomendation << it.first << " " << it.second << endl;
		}
		out_knn_euclidean_recomendation << endl;
	}
	out_knn_euclidean_recomendation.close();
	cout << TAB << " [CORESTRUCTURE]" << "End Saving in ../out/knn_euclidean_[recomendation].txt" << endl;
}


void CoreStructure::knn_by_manhatanDistance(t_userId userX, int n){
	vec_id_dist_inter distancesOfUserXWithAll;
	Timer timer;
	timer.startt();
	distanceBetweenUserXAndAll_by_ManhatanDistance(userX, distancesOfUserXWithAll);
	cout << TAB << " [CORESTRUCTURE]" << "Total Time in distanceBetweenUserXAndAll_by_ManhatanDistance: " << timer.getCurrentTime() << endl;
	cout << TAB << " [CORESTRUCTURE]" << "Total all users with restrictions(DISJOINT, UMBRAL_MINIMUM_PELICULAS_COMMON): " << distancesOfUserXWithAll.size() << endl;
	auto sizeVector = distancesOfUserXWithAll.size();
	if(sizeVector == 0){
		cout << TAB <<DEVELOPING << "distancesOfUserXWithAll is equal 0" << endl;
		return;
	}

	vector<t_userId> kNN;
	ofstream out_knn_manhatan;
	// MOSTRAR LO SIGUIENTE:
	// 1.- Guardar en el archivo ../out/knn_manhatan.txt [Usuario, Distancia, Interseccion]
	cout << TAB << " [CORESTRUCTURE]" << "Begin Saving in ../out/knn_manhatan.txt" << endl;
	out_knn_manhatan.open("../out/knn_manhatan.txt");
	out_knn_manhatan << "User-Distance-Interseccion" << endl;
	if(n >= sizeVector){
		// cout << TAB <<DEVELOPING << "K-NN with Euclidean Distance between userX: " << userX << " and all users" << endl;
		// cout << TAB <<DEVELOPING << "n: " << n << " is greater than the number of users: " << sizeVector << endl;
		// cout << TAB <<DEVELOPING << "The result will be the same as the number of users" << endl;
		// n = sizeVector;
		// mostrat todos los usuarios
		for(auto x: distancesOfUserXWithAll){
			// Para analizar despues
			kNN.pb(x.first);
			// cout << TAB <<DEVELOPING << "User: " << x.first << " Distance: " << x.second.first << " Interseccion: " << x.second.second << endl;
			out_knn_manhatan << fixed << setprecision(10) << x.first << " " << x.second.first << " " << x.second.second << endl;
		}
	}else{
		// mostrar solo los n primeros
		for(int e = 0 ; e < n; e++){
			// Para analizar despues
			kNN.pb(distancesOfUserXWithAll[e].first);
			out_knn_manhatan << fixed << setprecision(10) << distancesOfUserXWithAll[e].first << " " << distancesOfUserXWithAll[e].second.first << " " << distancesOfUserXWithAll[e].second.second << endl;
		}
	}
	out_knn_manhatan.close();
	cout << TAB << " [CORESTRUCTURE]" << "End Saving in ../out/knn_manhatan.txt" << endl;

	/*
		? 2.- Por cada Usuario, mostrar las peliculas y el puntaje que le da
		?     ordenados por rating.
		?     en el archivo ../out/knn_manhatan_[user-peliculas-puntaje].txt
	*/

	unordered_map<t_userId, vector<pair<t_movieId, t_rating>> > recommender;
	cout << TAB << " [CORESTRUCTURE]" << "Begin Saving in ../out/knn_manhatan_[user-peliculas_puntaje].txt" << endl;
	ofstream out_knn_manhatan_user_peliculas_puntaje;
	out_knn_manhatan_user_peliculas_puntaje.open("../out/knn_manhatan_[user-peliculas_puntaje].txt");

	for(auto x: kNN){
		auto hash_movie_rating_userX = user_movie_rating[x];
		out_knn_manhatan_user_peliculas_puntaje << "User: " << x << endl;
		out_knn_manhatan_user_peliculas_puntaje << "Peliculas-Puntaje (" << hash_movie_rating_userX.size()<< " rows founded)"<<  endl;
		for(auto it = hash_movie_rating_userX.begin(); it != hash_movie_rating_userX.end(); it++){
			// auto movieName = movies[it->first].first;
			// out_knn_manhatan_user_peliculas_puntaje << "[" <<it->first << "]-[" << movieName<< "] => "<<  it->second << endl;
			out_knn_manhatan_user_peliculas_puntaje << it->first << " " << it->second << endl;

			// *VALIDANDO EL SEGUNDO UMBRAL
			if(it->second >= UMBRAL_MINIMUM_RATING){
				recommender[x].pb({it->first, it->second});
			}
		}
		out_knn_manhatan_user_peliculas_puntaje << endl;
	}
	out_knn_manhatan_user_peliculas_puntaje.close();
	cout << TAB << " [CORESTRUCTURE]" << "End Saving in ../out/knn_manhatan_[user-peliculas_puntaje].txt" << endl;


	/*
		? 3.- Finalemte mostrar las peliculas que se recomendaran al usuario X, en base
		?     al umbral de UMBRAL_MINIMUM_RATING y UMBRAL_MINIMUM_PELICULAS_COMMON(ya filtrado
		?     con anterioridad)
		?	 en el archivo ../out/knn_manhatan_[recomendation].txt
	*/
	for(auto x:kNN){
		sort(recommender[x].begin(), recommender[x].end(), [](const auto &a, const auto &b){
			return a.second > b.second;
		});
	}
	cout << TAB << " [CORESTRUCTURE]" << "Begin Saving in ../out/knn_manhatan_[recomendation].txt" << endl;
	ofstream out_knn_manhatan_recomendation;
	out_knn_manhatan_recomendation.open("../out/knn_manhatan_[recomendation].txt");
	for(auto x: kNN){
		out_knn_manhatan_recomendation << "User: " << x << endl;
		out_knn_manhatan_recomendation << "Recomendation (" << recommender[x].size() << " rows)" << endl;
		for(auto it: recommender[x]){
			// auto movieName = movies[it.first].first;
			// out_knn_manhatan_recomendation << "[" << it.first << "]-[" << movieName << "] => " << it.second << endl;
			out_knn_manhatan_recomendation << it.first << " " << it.second << endl;
		}
		out_knn_manhatan_recomendation << endl;
	}
	out_knn_manhatan_recomendation.close();
	cout << TAB << " [CORESTRUCTURE]" << "End Saving in ../out/knn_manhatan_[recomendation].txt" << endl;
}

void CoreStructure::knn_by_similaridad_cosenos(t_userId userX, int n){
	vec_id_dist_inter distancesOfUserXWithAll;
	Timer timer;
	timer.startt();
	distanceBetweenUserXAndAll_by_CosineSimilarity(userX, distancesOfUserXWithAll);
	cout << TAB << " [CORESTRUCTURE]" << "Total Time in distanceBetweenUserXAndAll_by_CosineSimilarity: " << timer.getCurrentTime() << endl;
	cout << TAB << " [CORESTRUCTURE]" << "Total all users with restrictions(DISJOINT, UMBRAL): " << distancesOfUserXWithAll.size() << endl;
	auto sizeVector = distancesOfUserXWithAll.size();
	if(sizeVector == 0){
		cout << TAB <<DEVELOPING << "distancesOfUserXWithAll is equal 0" << endl;
		return;
	}

	vector<t_userId> kNN;

	// MOSTRAR LO SIGUIENTE:
	// 1.- Guardar en el archivo ../out/knn_coseno.txt [Usuario, Distancia, Interseccion]
	ofstream out_knn_coseno;
	cout << TAB << " [CORESTRUCTURE]" << "Begin Saving in ../out/knn_coseno.txt" << endl;
	out_knn_coseno.open("../out/knn_coseno.txt");
	out_knn_coseno << "User-Distance-Interseccion" << endl;
	if(n >= sizeVector){
		// cout << TAB <<DEVELOPING << "K-NN with Euclidean Distance between userX: " << userX << " and all users" << endl;
		// cout << TAB <<DEVELOPING << "n: " << n << " is greater than the number of users: " << sizeVector << endl;
		// cout << TAB <<DEVELOPING << "The result will be the same as the number of users" << endl;
		// n = sizeVector;
		// mostrat todos los usuarios
		for(auto x: distancesOfUserXWithAll){
			// Para analizar despues
			kNN.pb(x.first);
			// cout << TAB <<DEVELOPING << "User: " << x.first << " Distance: " << x.second.first << " Interseccion: " << x.second.second << endl;
			out_knn_coseno << fixed << setprecision(10) << x.first << " " << x.second.first << " " << x.second.second << endl;
		}
	}else{
		// mostrar solo los n primeros
		for(int e = 0 ; e < n; e++){
			// Para analizar despues
			kNN.pb(distancesOfUserXWithAll[e].first);
			out_knn_coseno << fixed << setprecision(10) << distancesOfUserXWithAll[e].first << " " << distancesOfUserXWithAll[e].second.first << " " << distancesOfUserXWithAll[e].second.second << endl;
		}
	}
	out_knn_coseno.close();
	cout << TAB << " [CORESTRUCTURE]" << "End Saving in ../out/knn_coseno.txt" << endl;

	/*
		? 2.- Por cada Usuario, mostrar las peliculas y el puntaje que le da
		?     ordenados por rating.
		?     en el archivo ../out/knn_coseno_[user-peliculas-puntaje].txt
	*/

	unordered_map<t_userId, vector<pair<t_movieId, t_rating>> > recommender;
	cout << TAB << " [CORESTRUCTURE]" << "Begin Saving in ../out/knn_coseno_[user-peliculas_puntaje].txt" << endl;
	ofstream out_knn_coseno_user_peliculas_puntaje;
	out_knn_coseno_user_peliculas_puntaje.open("../out/knn_coseno_[user-peliculas_puntaje].txt");
	for(auto x: kNN){
		auto hash_movie_rating_userX = user_movie_rating[x];
		out_knn_coseno_user_peliculas_puntaje << "User: " << x << endl;
		out_knn_coseno_user_peliculas_puntaje << "Peliculas-Puntaje (" << hash_movie_rating_userX.size()<< " rows founded)"<<  endl;
		for(auto it = hash_movie_rating_userX.begin(); it != hash_movie_rating_userX.end(); it++){
			// auto movieName = movies[it->first].first;
			// out_knn_euclidean_user_peliculas_puntaje << "[" <<it->first << "]-[" << movieName<< "] => "<<  it->second << endl;
			out_knn_coseno_user_peliculas_puntaje << it->first << " " << it->second << endl;

			// *VALIDANDO EL SEGUNDO UMBRAL
			if(it->second >= UMBRAL_MINIMUM_RATING){
				recommender[x].pb({it->first, it->second});
			}
		}
		out_knn_coseno_user_peliculas_puntaje << endl;
	}
	out_knn_coseno_user_peliculas_puntaje.close();
	cout << TAB << " [CORESTRUCTURE]" << "End Saving in ../out/knn_coseno_[user-peliculas_puntaje].txt" << endl;


	/*
		? 3.- Finalemte mostrar las peliculas que se recomendaran al usuario X, en base
		?     al umbral de UMBRAL_MINIMUM_RATING y UMBRAL_MINIMUM_PELICULAS_COMMON(ya filtrado
		?     con anterioridad)
		?	 en el archivo ../out/knn_coseno_[recomendation].txt
	*/
	for(auto x:kNN){
		sort(recommender[x].begin(), recommender[x].end(), [](const auto &a, const auto &b){
			return a.second > b.second;
		});
	}
	cout << TAB << " [CORESTRUCTURE]" << "Begin Saving in ../out/knn_coseno_[recomendation].txt" << endl;
	ofstream out_knn_coseno_recomendation;
	out_knn_coseno_recomendation.open("../out/knn_coseno_[recomendation].txt");
	for(auto x: kNN){
		out_knn_coseno_recomendation << "User: " << x << endl;
		out_knn_coseno_recomendation << "Recomendation (" << recommender[x].size() << " rows)" << endl;
		for(auto it: recommender[x]){
			// auto movieName = movies[it.first].first;
			// out_knn_euclidean_recomendation << "[" << it.first << "]-[" << movieName << "] => " << it.second << endl;
			out_knn_coseno_recomendation << it.first << " " << it.second << endl;
		}
		out_knn_coseno_recomendation << endl;
	}
	out_knn_coseno_recomendation.close();
	cout << TAB << " [CORESTRUCTURE]" << "End Saving in ../out/knn_coseno_[recomendation].txt" << endl;
}

void CoreStructure::knn_by_correlacion_pearson(t_userId userX, int n){
	;
}

//  ~=========================================END  KNN==================================




/*
	~================================== BEGIN QUERIES ==================================
*/
void CoreStructure::query_rating(t_userId userId, t_movieId movieId){
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

void CoreStructure::query_movies(t_userId userId){
	for(auto x: user_movie_rating[userId]){
		cout << x.first << " " << x.second << endl;
	}
}
//  ~======================================END  QUERIES ===============================
