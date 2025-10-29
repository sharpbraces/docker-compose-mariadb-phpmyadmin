from flask import Flask, request, jsonify
import mysql.connector, os

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host=os.environ['MCP_DB_HOST'],
        port=int(os.environ.get('MCP_DB_PORT', 3306)),
        user=os.environ['MCP_DB_USER'],
        password=os.environ['MCP_DB_PASSWORD'],
        database=os.environ['MCP_DB_NAME']
    )

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.post("/query")
def query():
    # próbáljuk kinyerni a body-t biztonságosan
    data = request.get_json(silent=True) or {}
    sql = data.get("sql")

    # ha nincs SQL megadva → usage info visszaadása
    if not sql:
        return jsonify({
            "usage": "POST JSON to this endpoint with {'sql': 'SELECT ...'}",
            "example": {
                "sql": "SELECT table_name FROM information_schema.tables LIMIT 5"
            },
            "status": "ready"
        }), 200

    # normál működés, ha van SQL
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)

        if cursor.with_rows:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = {"affected_rows": cursor.rowcount}

        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/")
def mcp_entrypoint():
    data = request.get_json(silent=True) or {}
    method = data.get("method")

    # 1️⃣ initialize
    if method == "initialize":
        return jsonify({
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {
                "serverInfo": {"name": "MariaDB MCP Proxy", "version": "1.0"},
                "capabilities": {"tools": True}
            }
        })

    # 2️⃣ getTools  →  a Copilot ezzel kérdezi le a használható funkciókat
    if method == "getTools":
        return jsonify({
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "run_query",
                        "description": "Run an SQL query on the MariaDB database and return the results.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "sql": {"type": "string", "description": "SQL query to execute"}
                            },
                            "required": ["sql"]
                        }
                    }
                ]
            }
        })

    # 3️⃣ run_tool  →  a Copilot ezzel hívja a toolt ténylegesen
    if method == "run_tool":
        params = data.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "run_query":
            sql = args.get("sql", "")
            try:
                conn = get_db()
                cur = conn.cursor(dictionary=True)
                cur.execute(sql)
                rows = cur.fetchall() if cur.with_rows else []
                cur.close()
                conn.close()
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {"rows": rows}
                })
            except Exception as e:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "error": {"code": 500, "message": str(e)}
                })

    # 4️⃣ minden másra standard válasz
    return jsonify({
        "jsonrpc": "2.0",
        "id": data.get("id"),
        "error": {"code": -32601, "message": f"Method '{method}' not implemented"}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
