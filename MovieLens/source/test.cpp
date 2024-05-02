#include <bits/stdc++.h>
#define all(x) x.begin(),x.end()
#define msg(str,str2) cout << str << str2<< endl
using namespace std;

using ll = long long;
using ld = long double;
using uint = unsigned int;
using ull = unsigned long long;
template<typename T>
using pair2 = pair<T, T>;
using pii = pair<int, int>;
using pli = pair<ll, int>;
using pll = pair<ll, ll>;

#define pb push_back
#define mp make_pair

int gcd(int a,int b){
	if(a%b==0) return b;
	else return gcd(b,a%b);
}

clock_t startTime;
double getCurrentTime() {
	return (double)(clock() - startTime) / CLOCKS_PER_SEC;
}
void solve(){
	int choice;

    // Display the menu initially
    cout << "\nMenu Principal:\n";
    cout << "1. Opción 1\n";
    cout << "2. Opción 2\n";
    cout << "3. Opción 3\n";
    cout << "4. Salir\n";

    while (true) {
        // Get user input
        cout << "Ingrese su opción: ";
        cin >> choice;

        // Process user choice
        switch (choice) {
            case 1:
                // Implement option 1 functionality
                cout << "Ejecutando Opción 1...\n";
                break;
            case 2:
                // Implement option 2 functionality
                cout << "Ejecutando Opción 2...\n";
                break;
            case 3:
                // Implement option 3 functionality
                cout << "Ejecutando Opción 3...\n";
                break;
            case 4:
                // Exit the program
                cout << "Saliendo del programa...\n";
                exit(0);
            default:
                // Handle invalid input
                cout << "Opción inválida. Intente nuevamente.\n";
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
	solve();
	return 0;
}