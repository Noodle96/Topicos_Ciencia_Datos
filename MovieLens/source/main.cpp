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

	cout << "Menu Principal:" << endl;;
	cout << "0. Salir" << endl;
	cout << "1. Imprimir usuarios in printUsers.txt" << endl;
	cout << "2. Calculate Euclidean Distance between userA and userB (ids)" << endl;
	cout << "3. Distance Between UserX And All by EuclideanDistance" << endl;

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
				cout << "Insert users" << endl;
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
				coreStructure.distanceBetweenUserXAndAll_by_EuclideanDistance(user_test_A);
				cout << TAB SOLVE<< "total time in distanceBetweenUserXAndAll_by_EuclideanDistance: " << timer.getCurrentTime() << endl << endl;
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