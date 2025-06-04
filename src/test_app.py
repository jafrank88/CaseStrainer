from flask import Flask, jsonify


def create_test_app():
    app = Flask(__name__)

    @app.route("/")
    def hello():
        return jsonify({"message": "Hello, World!"})

    return app


if __name__ == "__main__":
    app = create_test_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
