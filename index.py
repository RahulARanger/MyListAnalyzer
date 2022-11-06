from sanic import Sanic
from sanic.response import text
from sanic_ext import Extend
from MyListAnalyzerAPI.routes import my_list_analyzer

app = Sanic(__name__)
Extend(app)

origins = [
    "http://127.0.0.1:6969"
]

app.config.CORS_ORIGINS = ";".join(origins)
app.config.CORS_ALLOW_HEADERS = ["*"]

app.blueprint(my_list_analyzer)


@app.get("/MLA", name="Entry for MLA API")
async def greet(_):
    return text("Hello There, Welcome to MLA API")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=6966, debug=True, auto_reload=True)
