from flask import Flask

from config import Config
from routes.data import data_bp
from routes.eda import eda_bp
from routes.features import features_bp
from routes.governance import governance_bp
from routes.journey import journey_bp
from routes.overview import overview_bp
from routes.quality import quality_bp
from routes.split import split_bp
from routes.variables import variables_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(overview_bp)
    app.register_blueprint(journey_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(variables_bp)
    app.register_blueprint(quality_bp)
    app.register_blueprint(eda_bp)
    app.register_blueprint(features_bp)
    app.register_blueprint(governance_bp)
    app.register_blueprint(split_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
