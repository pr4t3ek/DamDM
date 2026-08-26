from flask import Flask

from config import Config
from routes.data import data_bp
from routes.governance import governance_bp
from routes.overview import overview_bp
from routes.quality import quality_bp
from routes.variables import variables_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(overview_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(variables_bp)
    app.register_blueprint(quality_bp)
    app.register_blueprint(governance_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
