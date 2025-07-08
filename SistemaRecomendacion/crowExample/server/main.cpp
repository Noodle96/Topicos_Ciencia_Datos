// // server/main.cpp
#define CROW_MAIN
#define CROW_USE_BOOST     // 🔴 Fuerza a usar Boost.Asio
#include "crow.h"
#include <vector>
#include <utility>

std::vector<std::pair<int, float>> obtener_knn(int k) {
    std::vector<std::pair<int, float>> vecinos;
    for (int i = 0; i < k; ++i) {
        vecinos.emplace_back(i + 1, 0.1f * i);
    }
    return vecinos;
}

int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/api/knn").methods("GET"_method)([](const crow::request& req){
        int k = 5;
        if (req.url_params.get("k")) {
            k = std::stoi(req.url_params.get("k"));
        }

        auto vecinos = obtener_knn(k);
        crow::json::wvalue response;

        for (int i = 0; i < vecinos.size(); ++i) {
            response[i]["id"] = vecinos[i].first;
            response[i]["distancia"] = vecinos[i].second;
        }

        return response;
    });

    app.port(8080).multithreaded().run();
}




// g++ -std=c++17 main.cpp -o server -lpthread -lboost_system -Iinclude