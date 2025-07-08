#define CROW_MAIN
#define CROW_USE_BOOST
#include "crow.h"

#include "../header/recommendationSystem.h"
#include "../header/timer.h"

struct CORS {
    struct context {};

    void before_handle(crow::request& req, crow::response& res, context&) {
        res.add_header("Access-Control-Allow-Origin", "*");
        res.add_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        res.add_header("Access-Control-Allow-Headers", "Content-Type");
        if (req.method == "OPTIONS"_method) {
            res.end();
        }
    }

    void after_handle(crow::request& /*req*/, crow::response& res, context&) {
        res.add_header("Access-Control-Allow-Origin", "*");
    }
};

int main() {
    // crow::SimpleApp app;
    crow::App<CORS> app;

    // 🔹 Instanciar el sistema de recomendación UNA sola vez
    RecommendationSystem sistema;
    // Esto ya carga ratings.csv, movies.csv y deja todo en RAM

    CROW_ROUTE(app, "/api/knn").methods("GET"_method)
    ([&sistema](const crow::request& req){
        crow::json::wvalue response;
        int user = 1, k = 5;
        std::string metric = "euclidean";

        if (req.url_params.get("user")) user = std::stoi(req.url_params.get("user"));
        if (req.url_params.get("k"))     k = std::stoi(req.url_params.get("k"));
        if (req.url_params.get("metric")) metric = req.url_params.get("metric");

        auto vecinos = sistema.knn(k, user, metric);
        for (int i = 0; i < vecinos.size(); ++i) {
            response[i]["id"] = vecinos[i].first;
            response[i]["score"] = vecinos[i].second;
        }

        return response;
    });

    CROW_ROUTE(app, "/api/add_user").methods("GET"_method)
    ([&sistema]() {
        crow::json::wvalue response;

        int nuevo_id = sistema.addUser();  // función modificada que retorna el ID
        response["user_id"] = nuevo_id;

        return crow::response(200, response);
    });

    // Puedes agregar más endpoints aquí: /api/recomendar, /api/user, etc.
    CROW_ROUTE(app, "/api/verify_user").methods("GET"_method)
    ([&sistema](const crow::request& req){
        crow::json::wvalue response;

        // Leer el parámetro desde la URL
        const char* id_str = req.url_params.get("user_id");
        if (!id_str) {
            response["error"] = "Falta el parámetro user_id";
            return crow::response(400, response);
        }

        int user_id = std::stoi(id_str);
        
        // Verificar si el usuario existe
        bool existe = sistema.userExists(user_id);
        response["exists"] = existe;

        return crow::response(200, response);
    });

    std::cout << "Servidor corriendo en http://localhost:8080" << std::endl;
    app.port(8080).multithreaded().run();
}
// with crow -Iinclude
//g++ -std=c++17 mainInterfaz.cpp recommendationSystem.cpp -o server -lpthread -lboost_system -I../include