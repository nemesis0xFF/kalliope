#include "crow.h"          // comes from /crow/include
#include <sqlite3.h>
#include <mutex>
#include <vector>
#include <string>

/* ---------------- helpers ---------------- */
std::mutex db_mutex;

std::vector<std::string> query_prefix(sqlite3* db,
                                      const std::string& prefix,
                                      std::size_t limit = 20)
{
    std::vector<std::string> results;
    std::lock_guard<std::mutex> lock(db_mutex);

    const char* sql =
        "SELECT lemma "
        "FROM word_fts "
        "WHERE word_fts MATCH ? || '*' "
        "LIMIT ?;";

    sqlite3_stmt* stmt = nullptr;
    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        CROW_LOG_ERROR << "SQL prepare error: " << sqlite3_errmsg(db);
        return results;
    }

    sqlite3_bind_text(stmt, 1, prefix.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int (stmt, 2, static_cast<int>(limit));

    while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
        const unsigned char* text = sqlite3_column_text(stmt, 0);
        if (text) {
            results.emplace_back(reinterpret_cast<const char*>(text));
        }
    }
    if (rc != SQLITE_DONE) {
        CROW_LOG_ERROR << "SQL step error: " << sqlite3_errmsg(db);
    }

    sqlite3_finalize(stmt);
    return results;
}

/* ---------------- main ---------------- */
int main()
{
    const char* db_path = "data/dict.db";   // mounted by docker‑compose
    sqlite3* db = nullptr;

    if (sqlite3_open_v2(db_path, &db, SQLITE_OPEN_READONLY, nullptr) != SQLITE_OK)
    {
        CROW_LOG_ERROR << "Cannot open dict.db at " << db_path;
        return 1;
    }

    crow::SimpleApp app;    // lighter than App<>

    CROW_ROUTE(app, "/health")([] {
        return crow::response{R"({"status":"ok"})"};
    });

    CROW_ROUTE(app, "/lookup/<string>")
    ([&](const std::string& q) {
        auto words = query_prefix(db, q, 30);
        crow::json::wvalue res;
        for (size_t i = 0; i < words.size(); ++i)
            res[i] = words[i];
        return res;
    });

    uint16_t port = std::getenv("LISTEN_PORT")
                    ? static_cast<uint16_t>(std::stoi(std::getenv("LISTEN_PORT")))
                    : 8080;
    app.port(port).multithreaded().run();
    sqlite3_close(db);
}
