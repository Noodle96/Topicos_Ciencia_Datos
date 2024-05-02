#include "macros.h"

class Timer{
	private:
		clock_t start;
	public:
		Timer(){
			// start = clock();
			;
		}
		// ~Timer(){
		// 	cout << "Total Time: " << getCurrentTime() << endl;
		// }
		void startt(){
			start = clock();
		}
		void reset(){
			start = clock();
		}
		double getCurrentTime(){
			return (double)(clock() - start) / CLOCKS_PER_SEC;
		}
};
// clock_t startTime;
// double getCurrentTime() {
// 	return (double)(clock() - startTime) / CLOCKS_PER_SEC;
// }