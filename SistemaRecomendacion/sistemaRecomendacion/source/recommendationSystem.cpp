#include "../header/recommendationSystem.h"
#include "../header/timer.h"

#include <fstream>
#include <sstream>
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											BEGIN CONSTRUCTOR AND DESTRUCTOR
///////////////////////////////////////////////////////////////////////////////////////////////////////
RecommendationSystem::RecommendationSystem() {
	// Abre el archivo para escritura (sobrescribe cada vez)
	cout_debug_file.open("../out/output_recommendation_systema.txt", std::ios::out);
	cout_debug_file_01_validar_distancias.open("../out/01_validar_distancias.txt", std::ios::out);
	cout_debug_file_02_calcular_knn.open("../out/02_calcular_knn.txt", std::ios::out);
	cout_debug_file_03_calcular_recomendaciones.open("../out/03_calcular_recomendaciones.txt", std::ios::out);
	cout_debug_file_04_peliculas_recomendar.open("../out/04_peliculas_recomendar.txt", std::ios::out);
	if (!cout_debug_file) std::cerr << "No se pudo abrir debug.txt\n";
	if(!cout_debug_file_01_validar_distancias) std::cerr << "No se pudo abrir 01_validar_distancias.txt\n";
	if(!cout_debug_file_02_calcular_knn) std::cerr << "No se pudo abrir 02_calcular_knn.txt\n";
	if(!cout_debug_file_03_calcular_recomendaciones) std::cerr << "No se pudo abrir 03_calcular_recomendaciones.txt\n";
	if(!cout_debug_file_04_peliculas_recomendar) std::cerr << "No se pudo abrir 04_peliculas_recomendar.txt\n";

    string linea;
    int userId, movieId;
    float rating;
    string timestamp;
    // Constructor implementation can be empty or initialize data structures if needed
    cout_debug_file << "[RECOMMENDATION SYSTEM] RecommendationSystem()" << endl;
    cout_debug_file << "\t[RECOMMENDATION SYSTEM] Load ratings.csv BEGIN" << endl;
    Timer timer("Load ratings.csv");
    std::ifstream archivo_csv_ratings("../../dataset_32M/ratings.csv");
    getline(archivo_csv_ratings,linea); // omitir la linea de cabecera
	// Verificar si el archivo se abrió correctamente
	if (archivo_csv_ratings.is_open()) {
		while (getline(archivo_csv_ratings, linea)) {
            stringstream ss(linea);
			string userIdStr, movieIdStr, ratingStr, timestampStr;
			getline(ss, userIdStr, ',');
			getline(ss, movieIdStr, ',');
			getline(ss, ratingStr, ',');
			getline(ss, timestampStr, ',');
			userId = stoi(userIdStr);
			movieId = stoi(movieIdStr);
			rating = stof(ratingStr);
			timestamp = timestampStr;
			addRatingAndUser(userId, movieId, rating, timestamp);
		}
		archivo_csv_ratings.close();
		cout_debug_file << "\t\t";
		timer.printElapsed(cout_debug_file);
    	cout_debug_file << "\t[RECOMMENDATION SYSTEM] Load ratings.csv END\n" << endl;
		cout_debug_file << "\t";
		printUser();
	} else {
		cout_debug_file << "\tError al abrir el archivo rating.csv" << std::endl;
	}

	string genre;
	cout_debug_file << "\t[RECOMMENDATION SYSTEM] Load movies.csv BEGIN" << endl;
	timer.reset("Load movies.csv");
	std::ifstream archivo_csv_movies("../../dataset_32M/movies.csv");
	getline(archivo_csv_movies, linea); // omitir la linea de cabecera
	// Verificar si el archivo se abrió correctamente
	if (archivo_csv_movies.is_open()) {
		while (getline(archivo_csv_movies, linea)) {
			stringstream ss(linea);
			string movieIdStr, title, genres;
			getline(ss, movieIdStr, ',');
			getline(ss, title, ',');
			getline(ss, genres, ',');
			movieId = stoi(movieIdStr);
			vector<string> genreList;
			stringstream genreStream(genres);
			while (getline(genreStream, genre, '|')) {
				genreList.push_back(genre);
			}
			addMovie(movieId, title, genreList);
		}
		archivo_csv_movies.close();
		cout_debug_file << "\t\t";
		timer.printElapsed(cout_debug_file);
		cout_debug_file << "\t[RECOMMENDATION SYSTEM] Load movies.csv END\n" << endl;
	} else{
		cout_debug_file << "\tError al abrir el archivo movies.csv" << std::endl;
	}
}

// Implementacion del destructor
RecommendationSystem::~RecommendationSystem() {
	if(cout_debug_file.is_open()) cout_debug_file.close();
	if(cout_debug_file_01_validar_distancias.is_open()) cout_debug_file_01_validar_distancias.close();
	if(cout_debug_file_02_calcular_knn.is_open()) cout_debug_file_02_calcular_knn.close();
	if(cout_debug_file_03_calcular_recomendaciones.is_open()) cout_debug_file_03_calcular_recomendaciones.close();
	if(cout_debug_file_04_peliculas_recomendar.is_open()) cout_debug_file_04_peliculas_recomendar.close();
	cout_debug_file << "[RECOMMENDATION SYSTEM] Destructor called" << endl;																																																																																																			
}
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											END CONSTRUCTOR AND DESTRUCTOR
///////////////////////////////////////////////////////////////////////////////////////////////////////
//													|
//										            |
//													|
//													|
//													|
//													|
//													|
// 												    |
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											BEGIN ADD FUNCTIONS
///////////////////////////////////////////////////////////////////////////////////////////////////////
void RecommendationSystem::addRatingAndUser(int userId, int movieId, float rating, string timestamp){
	user_movie_ratings[userId][movieId] = rating;
	users.insert(userId);
}

void RecommendationSystem::addMovie(int movieId, const string title, const vector<string>& genres) {
	movies[movieId] = make_pair(title, genres);
}
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											END ADD FUNCTIONS
///////////////////////////////////////////////////////////////////////////////////////////////////////
//													|
//										            |
//													|
//													|
//													|
//													|
//													|
// 												    |
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											BEGIN EUCLIDEAN DISTANCE
///////////////////////////////////////////////////////////////////////////////////////////////////////
pair<float, bool> RecommendationSystem::calculateEuclideanDistance(int userA, int userB, int &commonMovies){
	float euclideanDistance = 0.0;
	commonMovies = 0;
	// usuarios validos
	const auto& hash_movie_rating_userA = user_movie_ratings[userA];
	const auto& hash_movie_rating_userB = user_movie_ratings[userB];

	if(hash_movie_rating_userA.empty() || hash_movie_rating_userB.empty()){
		// cout << DEVELOPING <<"UserA or UserB not found" << endl;
		// retornar DISTANCIA_MAXIMA ya que no hay peliculas en comun
		// usuario no valido o no tiene calificaciones
		return {DISTANCIA_MAXIMA,false};
	}
	/*
		* Es eficiente comparar quien tiene menos peliculas recomendadas contra el que tiene mas peliculas
		* Para ello condicionamos con el criterio anterior
	*/
	const auto& smaller = (hash_movie_rating_userA.size() <= hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
    const auto& larger  = (hash_movie_rating_userA.size() >  hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	for (const auto& [movie, rating] : smaller) {
        auto it = larger.find(movie);
        if (it != larger.end()) {
            float diff = rating - it->second;
            euclideanDistance += diff * diff;
            ++commonMovies;
        }
    }
	if (commonMovies > 0)
        return {sqrt(euclideanDistance), true};
    return {DISTANCIA_MAXIMA, false};
}

pair<float, bool> RecommendationSystem::calculateEuclideanDistanceDebug(int userA, int userB, int &commonMovies){
	cout_debug_file_01_validar_distancias << "[EUCLIDEAN DISTANCE] calculateEuclideanDistanceDebug() BEGIN" << endl;
	cout_debug_file_01_validar_distancias << "\t[EUCLIDEAN DISTANCE] distance between " << userA << " and " << userB << endl;

	float euclideanDistance = 0.0;
	commonMovies = 0;
	// usuarios validos
	const auto& hash_movie_rating_userA = user_movie_ratings[userA];
	const auto& hash_movie_rating_userB = user_movie_ratings[userB];

	if(hash_movie_rating_userA.empty() || hash_movie_rating_userB.empty()){
		// cout << DEVELOPING <<"UserA or UserB not found" << endl;
		// retornar DISTANCIA_MAXIMA ya que no hay peliculas en comun
		// usuario no valido o no tiene calificaciones
		cout_debug_file_01_validar_distancias << "\t[EUCLIDEAN DISTANCE] usuario no valido o no tiene ratings" << endl;
		cout_debug_file_01_validar_distancias << "[EUCLIDEAN DISTANCE] calculateEuclideanDistanceDebug() END\n\n" << endl;
		return {DISTANCIA_MAXIMA,false};
	}
	/*
		* Es eficiente comparar quien tiene menos peliculas recomendadas contra el que tiene mas peliculas
		* Para ello condicionamos con el criterio anterior
	*/
	const auto& smaller = (hash_movie_rating_userA.size() <= hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
    const auto& larger  = (hash_movie_rating_userA.size() >  hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	cout_debug_file_01_validar_distancias << "\t[EUCLIDEAN DISTANCE] smaller size: " << smaller.size() << endl;
	cout_debug_file_01_validar_distancias << "\t[EUCLIDEAN DISTANCE] larger size: " << larger.size() << endl;

	Timer timer("Calculate Euclidean Distance");
	for (const auto& [movie, rating] : smaller) {
        auto it = larger.find(movie);
        if (it != larger.end()) {
            float diff = rating - it->second;
            euclideanDistance += diff * diff;
            ++commonMovies;
        }
    }
	cout_debug_file_01_validar_distancias << "\t[EUCLIDEAN DISTANCE] commonMovies: " << commonMovies << endl;
	cout_debug_file_01_validar_distancias << "\t";
	timer.printElapsed(cout_debug_file_01_validar_distancias, "seg");
	if (commonMovies > 0){
		cout_debug_file_01_validar_distancias << "\t[EUCLIDEAN DISTANCE] euclidean distance: " << fixed << setprecision(8)<< sqrt(euclideanDistance) << endl;
		cout_debug_file_01_validar_distancias << "[EUCLIDEAN DISTANCE] calculateEuclideanDistanceDebug() END\n\n" << endl;
		return {sqrt(euclideanDistance), true};
	}
	else{
		cout_debug_file_01_validar_distancias << "\t[EUCLIDEAN DISTANCE] No common movies found between user " << userA << " and user " << userB << endl;
		cout_debug_file_01_validar_distancias << "[EUCLIDEAN DISTANCE] calculateEuclideanDistanceDebug() END\n\n" << endl;
		return {DISTANCIA_MAXIMA, false};
	}
}

///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											END EUCLIDEAN DISTANCE
///////////////////////////////////////////////////////////////////////////////////////////////////////
//													|
//										            |
//													|
//													|
//													|
//													|
//													|
// 												    |
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											BEGIN MANHATTAN DISTANCE
///////////////////////////////////////////////////////////////////////////////////////////////////////
pair<float, bool> RecommendationSystem::calculateManhattanDistance(int userA, int userB, int &commonMovies){
	float manhattanDistance = 0.0;
	commonMovies = 0;
	// usuarios validos
	const auto& hash_movie_rating_userA = user_movie_ratings[userA];
	const auto& hash_movie_rating_userB = user_movie_ratings[userB];

	if(hash_movie_rating_userA.empty() || hash_movie_rating_userB.empty()){
		// cout << DEVELOPING <<"UserA or UserB not found" << endl;
		// retornar DISTANCIA_MAXIMA ya que no hay peliculas en comun
		// usuario no valido o no tiene calificaciones
		return {DISTANCIA_MAXIMA,false};
	}
	/*
		* Es eficiente comparar quien tiene menos peliculas recomendadas contra el que tiene mas peliculas
		* Para ello condicionamos con el criterio anterior
	*/
	const auto& smaller = (hash_movie_rating_userA.size() <= hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
    const auto& larger  = (hash_movie_rating_userA.size() >  hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	for (const auto& [movie, rating] : smaller) {
        auto it = larger.find(movie);
        if (it != larger.end()) {
            float diff = rating - it->second;
            manhattanDistance += abs(diff);
            ++commonMovies;
        }
    }
	if (commonMovies > 0)
        return {manhattanDistance, true};
    return {DISTANCIA_MAXIMA, false};
}
pair<float, bool> RecommendationSystem::calculateManhattanDistanceDebug(int userA, int userB, int &commonMovies){
	cout_debug_file_01_validar_distancias << "[MANHATTAN DISTANCE] calculateManhattanDistanceDebug() BEGIN" << endl;
	cout_debug_file_01_validar_distancias << "\t[MANHATTAN DISTANCE] distance between " << userA << " and " << userB << endl;
	float manhattanDistance = 0.0;
	commonMovies = 0;
	// usuarios validos
	const auto& hash_movie_rating_userA = user_movie_ratings[userA];
	const auto& hash_movie_rating_userB = user_movie_ratings[userB];

	if(hash_movie_rating_userA.empty() || hash_movie_rating_userB.empty()){
		// cout << DEVELOPING <<"UserA or UserB not found" << endl;
		// retornar DISTANCIA_MAXIMA ya que no hay peliculas en comun
		// usuario no valido o no tiene calificaciones
		cout_debug_file_01_validar_distancias << "\t[MANHATTAN DISTANCE] usuario no valido o no tiene ratings" << endl;
		cout_debug_file_01_validar_distancias << "[MANHATTAN DISTANCE] calculateManhattanDistanceDebug() END\n\n" << endl;
		// retornar DISTANCIA_MAXIMA
		return {DISTANCIA_MAXIMA,false};
	}
	/*
		* Es eficiente comparar quien tiene menos peliculas recomendadas contra el que tiene mas peliculas
		* Para ello condicionamos con el criterio anterior
	*/
	const auto& smaller = (hash_movie_rating_userA.size() <= hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
    const auto& larger  = (hash_movie_rating_userA.size() >  hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	cout_debug_file_01_validar_distancias << "\t[MANHATTAN DISTANCE] smaller size: " << smaller.size() << endl;
	cout_debug_file_01_validar_distancias << "\t[MANHATTAN DISTANCE] larger size: " << larger.size() << endl;

	Timer timer("calculate Manhattan Distance");
	for (const auto& [movie, rating] : smaller) {
        auto it = larger.find(movie);
        if (it != larger.end()) {
            float diff = rating - it->second;
            manhattanDistance += abs(diff);
            ++commonMovies;
        }
    }
	cout_debug_file_01_validar_distancias << "\t[MANHATTAN DISTANCE] commonMovies: " << commonMovies << endl;
	cout_debug_file_01_validar_distancias << "\t";
	timer.printElapsed(cout_debug_file_01_validar_distancias, "seg");
	if (commonMovies > 0){
		cout_debug_file_01_validar_distancias << "\t[MANHATTAN DISTANCE] manhattan distance: " << fixed << setprecision(8)<< manhattanDistance << endl;
		cout_debug_file_01_validar_distancias << "[MANHATTAN DISTANCE] calculateManhattanDistanceDebug() END\n\n" << endl;
    	return {manhattanDistance, true};
	}else{
		cout_debug_file_01_validar_distancias << "\t[MANHATTAN DISTANCE] No common movies found between user " << userA << " and user " << userB << endl;
		cout_debug_file_01_validar_distancias << "[MANHATTAN DISTANCE] calculateManhattanDistanceDebug() END\n\n" << endl;
		return {DISTANCIA_MAXIMA, false};
	}
}
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											END MANHATTAN DISTANCE
///////////////////////////////////////////////////////////////////////////////////////////////////////
//													|
//										            |
//													|
//													|
//													|
//													|
//													|
// 												    |
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											BEGIN COSINE SIMILARITY
///////////////////////////////////////////////////////////////////////////////////////////////////////
pair<float, bool> RecommendationSystem::calculateCosineSimilarity(int userA, int userB, int &commonMovies) {
	// Implementación de la similitud del coseno
	float dotProduct = 0.0;
	float normA = 0.0;
	float normB = 0.0;
	commonMovies = 0;

	const auto& hash_movie_rating_userA = user_movie_ratings[userA];
	const auto& hash_movie_rating_userB = user_movie_ratings[userB];	

	if (hash_movie_rating_userA.empty() || hash_movie_rating_userB.empty()) {
		// POdemos asignar tambien -1, pero al tener interseccion como false, solamente no las vamos a considar
		return {0.0, false}; // el usuario no tiene registros de calificacion o usuario no existe
	}

	const auto& smaller = (hash_movie_rating_userA.size() <= hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	const auto& larger  = (hash_movie_rating_userA.size() >  hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;

	for (const auto& [movie, ratingA] : smaller) {
		auto it = larger.find(movie);
		if (it != larger.end()) {
			float ratingB = it->second;
			dotProduct += ratingA * ratingB;
			normA += ratingA * ratingA;
			normB += ratingB * ratingB;
			++commonMovies;
		}
	}

	if (commonMovies == 0) {
		return {0.0, false}; // No hay películas en común
	}
	if( normA == 0 || normB == 0) {
		return {0.0, false}; // Evitar división por cero
	}
	float cosineSimilarity = dotProduct / (sqrt(normA) * sqrt(normB));
	return {cosineSimilarity, true}; // Retorna la similitud del coseno y true
}
pair<float, bool> RecommendationSystem::calculateCosineSimilarityDebug(int userA, int userB, int &commonMovies) {
	cout_debug_file_01_validar_distancias << "[COSINE SIMILARITY] calculateCosineSimilarityDebug() BEGIN" << endl;
	cout_debug_file_01_validar_distancias << "\t[COSINE SIMILARITY] similarity between " << userA << " and " << userB << endl;
	// Implementación de la similitud del coseno
	float dotProduct = 0.0;
	float normA = 0.0;
	float normB = 0.0;
	commonMovies = 0;

	const auto& hash_movie_rating_userA = user_movie_ratings[userA];
	const auto& hash_movie_rating_userB = user_movie_ratings[userB];	

	if (hash_movie_rating_userA.empty() || hash_movie_rating_userB.empty()) {
		// POdemos asignar tambien -1, pero al tener interseccion como false, solamente no las vamos a considar
		cout_debug_file_01_validar_distancias << "\t[COSINE SIMILARITY] usuario no valido o no tiene ratings" << endl;
		cout_debug_file_01_validar_distancias << "[COSINE SIMILARITY] calculateCosineSimilarityDebug() END\n\n" << endl;
		return {0.0, false}; // el usuario no tiene registros de calificacion o usuario no existe
	}

	const auto& smaller = (hash_movie_rating_userA.size() <= hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	const auto& larger  = (hash_movie_rating_userA.size() >  hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	cout_debug_file_01_validar_distancias << "\t[COSINE SIMILARITY] smaller size: " << smaller.size() << endl;
	cout_debug_file_01_validar_distancias << "\t[COSINE SIMILARITY] larger size: " << larger.size() << endl;

	Timer timer("Calculate Cosine Similarity");
	for (const auto& [movie, ratingA] : smaller) {
		auto it = larger.find(movie);
		if (it != larger.end()) {
			float ratingB = it->second;
			dotProduct += ratingA * ratingB;
			normA += ratingA * ratingA;
			normB += ratingB * ratingB;
			++commonMovies;
		}
	}
	cout_debug_file_01_validar_distancias << "\t[COSINE SIMILARITY] commonMovies: " << commonMovies << endl;
	cout_debug_file_01_validar_distancias << "\t";
	timer.printElapsed(cout_debug_file_01_validar_distancias, "seg");

	if (commonMovies == 0) {
		cout_debug_file_01_validar_distancias << "\t[COSINE SIMILARITY] No common movies found between user " << userA << " and user " << userB << endl;
		cout_debug_file_01_validar_distancias << "[COSINE SIMILARITY] calculateCosineSimilarityDebug() END\n\n" << endl;
		// No hay películas en
		return {0.0, false}; // No hay películas en común
	}
	if( normA == 0 || normB == 0){
		cout_debug_file_01_validar_distancias << "\t[COSINE SIMILARITY] normA or normB is zero, returning 0.0" << endl;
		cout_debug_file_01_validar_distancias << "[COSINE SIMILARITY] calculateCosineSimilarityDebug() END\n\n" << endl;
		return {0.0, false}; // Evitar división por cero
	}
	float cosineSimilarity = dotProduct / (sqrt(normA) * sqrt(normB));
	cout_debug_file_01_validar_distancias << "\t[COSINE SIMILARITY] cosine similarity: "<< fixed << setprecision(8) << cosineSimilarity << endl;
	cout_debug_file_01_validar_distancias << "[COSINE SIMILARITY] calculateCosineSimilarityDebug() END\n\n" << endl;
	return {cosineSimilarity, true}; // Retorna la similitud del coseno y true
}
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											END COSINE SIMILARITY
///////////////////////////////////////////////////////////////////////////////////////////////////////
//													|
//										            |
//													|
//													|
//													|
//													|
//													|
// 												    |
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											BEGIN PEARSON CORRELATION
///////////////////////////////////////////////////////////////////////////////////////////////////////
pair<float, bool> RecommendationSystem::calculatePearsonCorrelation(int userA, int userB, int &commonMovies){
	float sumA = 0.0, sumB = 0.0, sumA2 = 0.0, sumB2 = 0.0, sumAB = 0.0;
	commonMovies = 0;

	const auto& hash_movie_rating_userA = user_movie_ratings[userA];
	const auto& hash_movie_rating_userB = user_movie_ratings[userB];

	if (hash_movie_rating_userA.empty() || hash_movie_rating_userB.empty()) {
		return {0.0, false}; // el usuario no tiene registros de calificacion o usuario no valido
	}

	const auto& smaller = (hash_movie_rating_userA.size() <= hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	const auto& larger  = (hash_movie_rating_userA.size() >  hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;

	for (const auto& [movie, ratingA] : smaller) {
		auto it = larger.find(movie);
		if (it != larger.end()) {
			float ratingB = it->second;
			sumA += ratingA;
			sumB += ratingB;
			sumA2 += ratingA * ratingA;
			sumB2 += ratingB * ratingB;
			sumAB += ratingA * ratingB;
			++commonMovies;
		}
	}

	if (commonMovies == 0) {
		return {0.0, false}; // No hay películas en común
	}

	float numerator = sumAB - (sumA * sumB / commonMovies);
	float denominator = sqrt((sumA2 - (sumA * sumA / commonMovies))) * sqrt((sumB2 - (sumB * sumB / commonMovies)));

	if (denominator == 0) {
		return {0.0, false}; // Evitar división por cero
	}

	float pearsonCorrelation = numerator / denominator;
	return {pearsonCorrelation, true}; // Retorna el coeficiente de correlación de Pearson y true
}
pair<float, bool> RecommendationSystem::calculatePearsonCorrelationDebug(int userA, int userB, int &commonMovies){
	cout_debug_file_01_validar_distancias << "[PEARSON CORRELATION] calculatePearsonCorrelationDebug() BEGIN" << endl;
	cout_debug_file_01_validar_distancias << "\t[PEARSON CORRELATION] correlation between " << userA << " and " << userB << endl;
	float sumA = 0.0, sumB = 0.0, sumA2 = 0.0, sumB2 = 0.0, sumAB = 0.0;
	commonMovies = 0;

	const auto& hash_movie_rating_userA = user_movie_ratings[userA];
	const auto& hash_movie_rating_userB = user_movie_ratings[userB];

	if (hash_movie_rating_userA.empty() || hash_movie_rating_userB.empty()) {
		cout_debug_file_01_validar_distancias << "\t[PEARSON CORRELATION] usuario no valido o no tiene ratings" << endl;
		cout_debug_file_01_validar_distancias << "[PEARSON CORRELATION] calculatePearsonCorrelationDebug() END\n\n" << endl;
		return {0.0, false}; // el usuario no tiene registros de calificacion o usuario no valido
	}

	const auto& smaller = (hash_movie_rating_userA.size() <= hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	const auto& larger  = (hash_movie_rating_userA.size() >  hash_movie_rating_userB.size()) ? hash_movie_rating_userA : hash_movie_rating_userB;
	cout_debug_file_01_validar_distancias << "\t[PEARSON CORRELATION] smaller size: " << smaller.size() << endl;
	cout_debug_file_01_validar_distancias << "\t[PEARSON CORRELATION] larger size: " << larger.size() << endl;

	Timer timer("Calculate Pearson Correlation");
	for (const auto& [movie, ratingA] : smaller) {
		auto it = larger.find(movie);
		if (it != larger.end()) {
			float ratingB = it->second;
			sumA += ratingA;
			sumB += ratingB;
			sumA2 += ratingA * ratingA;
			sumB2 += ratingB * ratingB;
			sumAB += ratingA * ratingB;
			++commonMovies;
		}
	}
	cout_debug_file_01_validar_distancias << "\t[PEARSON CORRELATION] commonMovies: " << commonMovies << endl;
	cout_debug_file_01_validar_distancias << "\t";
	timer.printElapsed(cout_debug_file_01_validar_distancias, "seg");

	if (commonMovies == 0) {
		cout_debug_file_01_validar_distancias << "\t[PEARSON CORRELATION] No common movies found between user " << userA << " and user " << userB << endl;
		cout_debug_file_01_validar_distancias << "[PEARSON CORRELATION] calculatePearsonCorrelationDebug() END\n\n" << endl;
		return {0.0, false}; // No hay películas en común
	}

	float numerator = sumAB - (sumA * sumB / commonMovies);
	float denominator = sqrt((sumA2 - (sumA * sumA / commonMovies))) * sqrt((sumB2 - (sumB * sumB / commonMovies)));

	if (denominator == 0) {
		cout_debug_file_01_validar_distancias << "\t[PEARSON CORRELATION] denominator is zero, returning 0.0" << endl;
		cout_debug_file_01_validar_distancias << "[PEARSON CORRELATION] calculatePearsonCorrelationDebug() END\n\n" << endl;
		return {0.0, false}; // Evitar división por cero
	}

	float pearsonCorrelation = numerator / denominator;
	cout_debug_file_01_validar_distancias << "\t[PEARSON CORRELATION] pearson correlation: "<< fixed << setprecision(8) << pearsonCorrelation << endl;
	cout_debug_file_01_validar_distancias << "[PEARSON CORRELATION] calculatePearsonCorrelationDebug() END\n\n" << endl;
	return {pearsonCorrelation, true}; // Retorna el coeficiente de correlación de Pearson y true
}
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											END PEARSON CORRELATION
///////////////////////////////////////////////////////////////////////////////////////////////////////
//													|
//										            |
//													|
//													|
//													|
//													|
//													|
// 												    |
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 										    	BEGIN KNN 
///////////////////////////////////////////////////////////////////////////////////////////////////////
vector<pair<int, float>> RecommendationSystem::knn(int n, int userX, string metrica){
	vector<pair<int, float>> distances;
	int commonMovies = 0;

	for (const auto& user : users) {
		if (user != userX) {
			pair<float, bool> distance;
			if (metrica == "euclidean") {
				distance = calculateEuclideanDistance(userX, user, commonMovies);
			} else if (metrica == "manhattan") {
				distance = calculateManhattanDistance(userX, user, commonMovies);
			} else if (metrica == "cosine") {
				distance = calculateCosineSimilarity(userX, user, commonMovies);
			} else if (metrica == "pearson") {
				distance = calculatePearsonCorrelation(userX, user, commonMovies);
			} else {
				cout_debug_file << "Metrica no valida" << endl;
				return {};
			}
			if (distance.second) { // Si hay peliculas en comun
				distances.emplace_back(user, distance.first);
			}
		}
	}
	if(metrica == "euclidean" || metrica == "manhattan") {
		// Si la metrica es euclidean o manhattan, ordenamos por distancia ascendente
		sort(distances.begin(), distances.end(), [](const pair<int, float>& a, const pair<int, float>& b) {
			return a.second < b.second; // Ordenar por distancia ascendente
		});
	} else if (metrica == "cosine" || metrica == "pearson") {
		// Si la metrica es cosine o pearson, ordenamos por similitud descendente
		sort(distances.begin(), distances.end(), [](const pair<int, float>& a, const pair<int, float>& b) {
			return a.second > b.second; // Ordenar por similitud descendente
		});
	}

	if (distances.size() > n) {
		distances.resize(n); // Limitar a los n vecinos más cercanos
	}
	return distances;
}
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 												  END KNN
///////////////////////////////////////////////////////////////////////////////////////////////////////
//													|
//										            |
//													|
//													|
//													|
//													|
//													|
// 												    |
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 												BEGIN RECOMENDAR
///////////////////////////////////////////////////////////////////////////////////////////////////////
void RecommendationSystem::recomendar(vector<pair<int, float>>& knn_result, int userARecomendar){
	// for(auto & [user, distance] : knn_result){

	// }

}
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 												END RECOMENDAR
///////////////////////////////////////////////////////////////////////////////////////////////////////
//													|
//										            |
//													|
//													|
//													|
//													|
//													|
// 												    |
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 												BEGIN OTHERS
///////////////////////////////////////////////////////////////////////////////////////////////////////
void RecommendationSystem::printUser() {
	cout_debug_file << "[RECOMMENDATION SYSTEM] printUser() BEGIN" << endl;
    Timer timer("write users.txt");
	ofstream user_file("../out/users.txt");
	if (!user_file) {
		cout_debug_file << "No se pudo abrir el archivo users.txt\n";
		return;
	}
	for (const auto& user : users) {
		user_file << "User ID: "<<user << " -> " << user_movie_ratings[user].size() << " ratings\n";
	}
	user_file.close();
	cout_debug_file << "\t\t";
	timer.printElapsed(cout_debug_file);
	cout_debug_file << "\t[RECOMMENDATION SYSTEM] printUser() END\n" << endl;
}
///////////////////////////////////////////////////////////////////////////////////////////////////////
// 											END OTHERS
///////////////////////////////////////////////////////////////////////////////////////////////////////