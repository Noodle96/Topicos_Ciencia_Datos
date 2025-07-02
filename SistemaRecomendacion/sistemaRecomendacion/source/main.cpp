#include "../header/recommendationSystem.h"
#include "../header/timer.h"

void startRecommendationSystem(){
    RecommendationSystem recommendationSystem;
    cout << "Menu Principal:" << endl;
	cout << "\t0. Salir" << endl;
	cout << "\t1. Calcular distancia euclidiana entre userA and userB" << endl;
	cout << "\t2. Calcular distancia de manhattan entre userA and userB" << endl;
	cout << "\t3. Calculate similitud del coseno entre userA and userB" << endl;
	cout << "\t4. Calcular coeficiente de correlacion de pearson entre userA and userB" << endl;
    cout << "\t5. Calcular KNN" << endl;

    int choise;
    while(true){
        cout << "Input opcion: ";
        cin>>choise;
        switch (choise){
            case 0:{
                cout << "\tSaliendo del sistema de recomendacion..." << endl;
                exit(0);
                break;
            }
            case 1:{
                /*
                    Calcular distancia euclidiana entre userA and userB
                */
                int userA, userB;
                pair<float, bool> result;
                int commonMovies;
                cout << "\tInsert users (valid ids) case 1" << endl;
                cin>> userA >> userB;
                result = recommendationSystem.calculateEuclideanDistanceDebug(userA, userB, commonMovies);
                cout << "\tCalculating Euclidean distance between user " << userA << " and user " << userB << endl;
                if(result.second) cout << "distance: " << fixed << setprecision(8) << result.first  << " y commonMovies: "<< commonMovies<< endl;
                else cout << "Usuario no valido or no hay peliculas en comun" << endl;
                break;
            }
            case 2:{
                /*
                    Calcular distancia de manhattan entre userA and userB
                */
                int userA, userB;
                pair<float, bool> result;
                int commonMovies;
                cout << "\tInsert users (valid ids) case 2" << endl;
                cin>> userA >> userB;
                cout << "\tCalculating Manhattan distance between user " << userA << " and user " << userB << endl;
                result = recommendationSystem.calculateManhattanDistanceDebug(userA, userB, commonMovies);
                if(result.second) cout << "distance: " << fixed << setprecision(8)<< result.first << " y commonMovies: " << commonMovies<< endl;
                else cout << "Usuario no valido or no hay peliculas en comun" << endl;
                break;
            }
            case 3:{
                /*
                    Calculate similitud del coseno entre userA and userB
                */
                int userA, userB;
                pair<float, bool> result;
                int commonMovies;
                cout << "\tInsert users (valid ids) case 3" << endl;
                cin>> userA >> userB;
                cout << "\tCalculating cosine similarity between user " << userA << " and user " << userB << endl;
                result = recommendationSystem.calculateCosineSimilarityDebug(userA, userB, commonMovies);
                if(result.second) cout << "cosine similarity: "<< fixed << setprecision(8) << result.first << " y commonMovies: " << commonMovies << endl;
                else cout << "Usuario no valido or no hay peliculas en comun" << endl;
                break;
            }
            case 4:{
                /*
                    Calcular coeficiente de correlacion de pearson entre userA and userB
                */
                int userA, userB;
                pair<float, bool> result;
                int commonMovies;
                cout << "\tInsert users (valid ids) case 4" << endl;
                cin>> userA >> userB;
                cout << "\tCalculating Pearson correlation coefficient between user " << userA << " and user " << userB << endl;
                result = recommendationSystem.calculatePearsonCorrelationDebug(userA, userB, commonMovies);
                if(result.second) cout << "pearson correlation: "<< fixed << setprecision(8) << result.first << " y commonMovies: " << commonMovies << endl;
                else cout << "Usuario no valido or no hay peliculas en comun" << endl;
                break;
            }
            case 5:{
                /*
                    Calcular KNN
                */
                int userA;
                int n;
                string metric;
                vector<pair<int, float>> knnResults;
                ofstream& log02 = recommendationSystem.getCoutDebugFile02CalcularKNN();
                log02 << "[KNN] knn(n, user, metrica) BEGIN" << endl;
                cout << "\tInsert user id, n (number of neighbors) and metric (euclidean, manhattan, cosine, pearson): " << endl;
                cin >> userA >> n >> metric;

                cout << "\tCalculating KNN for user " << userA << " with n = " << n << " and metric = " << metric << endl;
                log02 << "\t[KNN] Calculating KNN for user " << userA << " with n = " << n << " and metric = " << metric << endl;
                knnResults.clear();
                knnResults = recommendationSystem.knn(n, userA, metric);
                if(knnResults.empty()){
                    cout << "\tNo hay usuarios con peliculas en comun o no hay usuarios registrados.\n\n" << endl;
                    log02 << "\t[KNN] No hay usuarios con peliculas en comun o no hay usuarios registrados.\n\n" << endl;

                } else {
                    cout << "\tKNN Results for user " << userA << ":" << endl;
                    log02 << "\tKNN Results for user " << userA << ":" << endl;
                    string str = (metric == "euclidean" || metric == "manhattan") ? "Distance" : (metric == "cosine" ? "Similaridad": "Correlacion");
                    for(const auto& [userId, distance] : knnResults){
                        // cout << "\tUser ID: " << userId << ", Distance: " << distance << endl;
                        log02 << "\t\tUser ID: " << userId << ", " << str <<": "<< fixed << setprecision(8) << distance << endl;
                    }
                }
                log02 << "[KNN] knn(n, user, metrica) END\n\n" << endl;
                break;
            }
            default:
                cout << "\tOpción inválida. Intente nuevamente." << endl << endl;
                break;
        } // end switch case
    }
}

int main(){
    // ios_base::sync_with_stdio(false);
    // cin.tie(0);
    // #ifdef DEBUG
    //     // freopen("input.txt","r",stdin);
    //     freopen("output.txt","w",stdout);
    // #endif
    startRecommendationSystem();
    return 0;
}