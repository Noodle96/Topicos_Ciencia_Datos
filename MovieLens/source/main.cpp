#include "../header/coreStructure.h"
#include "../header/timer.h"

CoreStructure coreStructure;
std::string linea;
// unordered_map<int,int> mapa;

void readRatingCSV(){
	// atributos rating.csv
	t_userId userId;
	t_movieId movieId;
	t_rating rating;
	t_timestamp timestamp;
	char delimiter = ',';

	// ifstream archivo_csv("data/ml-20m/temporal.csv");
	std::ifstream archivo_csv("../data-ml-latest/ratings_test.csv");
	getline(archivo_csv,linea); // omitir la linea de cabecera

	// Verificar si el archivo se abrió correctamente
	if (archivo_csv.is_open()) {
		while (std::getline(archivo_csv, linea)) {
			std::istringstream ss(linea);// [1]30seg
			ss >> userId >>delimiter>> movieId >> delimiter>> rating >>delimiter>> timestamp;
			// mapa[userId]++;
			coreStructure.add(userId, movieId, rating, timestamp); //[1] 30seg
			// cout << userId << " " << movieId << " " << rating << " " << timestamp << endl;
		}
		archivo_csv.close();
	} else {
		std::cerr << "Error al abrir el archivo CSV" << std::endl;
	}
}
void solve(){
	Timer timer;
	t_userId user_test_A;
	t_userId user_test_B;
	int choice;
	// to save distances between userX and all users
	// called in opcion 3 of menu
	ofstream out_distance_userX_all, out_common_movies_userA_userB;

	// commmon Vectors, clear before use
	vec_id_dist_inter distancesOfUserXWithAll;
	vector<t_movieId> commonMovies;

	cout << "Menu Principal:" << endl;;
	cout << "0. Salir" << endl;
	cout << "1. Imprimir usuarios in printUsers.txt" << endl;
	cout << "2. Calculate Euclidean Distance between userA and userB (ids) details" << endl;
	cout << "3. Distance Between UserX And All by EuclideanDistance" << endl;
	cout << "4. Common movies between UserA and UserB" << endl;
	cout << "5. Calculate Manhatan Distance between userA and userB (ids) details" << endl;
	cout << "6. Calculate Cosine Similarity between userA and userB (ids) details" << endl;
	cout << "7. Calculate Pearson Correlation between userA and userB (ids) details" << endl;
	cout << endl;

	cout << SOLVE <<"Load Data ..." << endl;
	timer.startt();
	readRatingCSV();
	cout << TAB SOLVE << "Total Time in load rating.csv and STORE : " << timer.getCurrentTime() << endl << endl;

    while (true) {
        // Get user input
        cout << "Input option: ";
        cin >> choice;
        switch (choice) {
			case 0:
                cout << "Saliendo del sistema de recomendacion..." << endl;
                exit(0);
            case 1:
				/*
					* Imprimir usuarios in printUsers.txt
				*/
				cout << SOLVE << "Print Users in printUsers.txt ..." << endl;
				timer.startt();
				coreStructure.print_users();
				cout << TAB SOLVE << "Total Time in print users in printUsers.txt  : " << timer.getCurrentTime() << endl << endl;
                break;
            case 2:
                /*
					* Calcular la distancia euclidiana entre dos usuarios (id_userA, id_userB)
				*/
				cout << "Insert users (valid ids)" << endl;
				cin>>user_test_A>>user_test_B;
				// // Usuarios validos
				cout << SOLVE<< "Call calculatEuclideanDistance" << endl;
				timer.startt();
				coreStructure.details_calculatEuclideanDistance(user_test_A, user_test_B);
				cout << TAB SOLVE<<"[calculatEuclideanDistance] Total Time in calculate Euclidean Distance: " << timer.getCurrentTime() << endl << endl;
                break;
            case 3:
				/*
					* Calcular la distancia euclidiana entre el Usuario X, contra todos los demas usuarios
				*/
				cout << "Insert User (id valid)" << endl;
				cin>>user_test_A;
				cout << SOLVE << "Call distanceBetweenUserXAndAll_by_EuclideanDistance" << endl;
				
                timer.reset();
				distancesOfUserXWithAll.clear();
				coreStructure.distanceBetweenUserXAndAll_by_EuclideanDistance(user_test_A,distancesOfUserXWithAll);
				cout << TAB SOLVE<< "total time in distanceBetweenUserXAndAll_by_EuclideanDistance: " << timer.getCurrentTime() << endl << endl;

				cout << TAB SOLVE << "Begin save in../out/distanceBetweenUserXAndAll_by_EuclideanDistance.txt " << endl;
				out_distance_userX_all.open("../out/distanceBetweenUserXAndAll_by_EuclideanDistance.txt");
				for(auto x: distancesOfUserXWithAll){
					out_distance_userX_all  << std::fixed << std::setprecision(10)<< x.first << " " << x.second.first << " " << x.second.second<< endl;
				}
				out_distance_userX_all.close();
				cout << TAB SOLVE << "End save in../out/distanceBetweenUserXAndAll_by_EuclideanDistance.txt "<< endl << endl;
                break;
			case 4:
				/*
					* Listar las peliculas en comun entre el usuarioA y el usuarioB
				*/
				cout << "Insert users (valid ids)" << endl;
				cin>>user_test_A>>user_test_B;
				cout << SOLVE << "Call getCommonMovies" << endl;
				timer.startt();
				commonMovies.clear();
				coreStructure.getCommonMovies(user_test_A, user_test_B, commonMovies);
				cout << TAB SOLVE << "Total Time in getCommonMovies: " << timer.getCurrentTime() << endl << endl;

				cout << TAB SOLVE << "Begin save in ../out/commonMovies_userA_userB.txt" << endl;
				out_common_movies_userA_userB.open("../out/commonMovies_userA_userB.txt");
				for(auto x: commonMovies){
					out_common_movies_userA_userB << x << endl;
				}
				out_common_movies_userA_userB.close();
				cout << TAB SOLVE << "End save in ../out/commonMovies_userA_userB.txt" << endl << endl;
				break;
			case 5:
				/*
					* Calcular la distancia de manhatan entre dos usuarios (id_userA, id_userB)
				*/
				cout << "Insert users (valid ids)" << endl;
				cin>>user_test_A>>user_test_B;
				// // Usuarios validos
				cout << SOLVE<< "Call calculateManhatanDistance" << endl;
				timer.startt();
				coreStructure.details_calculateManhatanDistance(user_test_A, user_test_B);
				cout << TAB SOLVE << "[calculateManhatanDistance] Total Time in calculate Manhatan Distance: " << timer.getCurrentTime() << endl << endl;
				break;
			case 6:
				/*
					* Calcular la similaridad de coseno entre dos usuarios (id_userA, id_userB)
				*/
				cout << "Insert users (valid ids)" << endl;
				cin>>user_test_A>>user_test_B;
				// // Usuarios validos
				cout << SOLVE<< "Call calculateCosineSimilarity" << endl;
				timer.startt();
				coreStructure.details_calculateCosineSimilarity(user_test_A, user_test_B);
				cout << TAB SOLVE << "[calculateCosineSimilarity] Total Time in calculate Cosine Similarity: " << timer.getCurrentTime() << endl << endl;
				break;
			case 7:
				/*
					* Calcular la correlaccion de pearson entre dos usuarios (id_userA, id_userB)
				*/
				cout << "Insert users (valid ids)" << endl;
				cin>>user_test_A>>user_test_B;
				// // Usuarios validos
				cout << SOLVE<< "Call calculatePearsonCorrelation" << endl;
				timer.startt();
				coreStructure.details_calculatePearsonCorrelation(user_test_A, user_test_B);
				cout << TAB SOLVE << "[calculatePearsonCorrelation] Total Time in calculate Pearson Correlation: " << timer.getCurrentTime() << endl << endl;
				break;
            default:
                cout << "Opción inválida. Intente nuevamente." << endl << endl;
        }
    }


}

int main(){
	// ios_base::sync_with_stdio(false);
	// cin.tie(0);
	// #ifdef DEBUG
	// 	freopen("input.txt","r",stdin);
	// 	freopen("output.txt","w",stdout);
	// #endif
	// read();
	solve();
	return 0;
}