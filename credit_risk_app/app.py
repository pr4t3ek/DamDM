from flask import Flask

from config import Config
from routes.academic import academic_bp
from routes.account import account_bp
from routes.collection import collection_bp
from routes.costbenefit import costbenefit_bp
from routes.data import data_bp
from routes.download import download_bp
from routes.eda import eda_bp
from routes.explain import explain_bp
from routes.features import features_bp
from routes.governance import governance_bp
from routes.journey import journey_bp
from routes.model_advanced import model_advanced_bp
from routes.model_baseline import model_baseline_bp
from routes.model_ks import model_ks_bp
from routes.model_lift import model_lift_bp
from routes.model_roc import model_roc_bp
from routes.model_screening import model_screening_bp
from routes.overview import overview_bp
from routes.quality import quality_bp
from routes.recommendation import recommendation_bp
from routes.risk_metrics import risk_metrics_bp
from routes.scenario import scenario_bp
from routes.simulator import simulator_bp
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
    app.register_blueprint(model_baseline_bp)
    app.register_blueprint(model_advanced_bp)
    app.register_blueprint(model_screening_bp)
    app.register_blueprint(model_roc_bp)
    app.register_blueprint(model_ks_bp)
    app.register_blueprint(model_lift_bp)
    app.register_blueprint(simulator_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(scenario_bp)
    app.register_blueprint(explain_bp)
    app.register_blueprint(collection_bp)
    app.register_blueprint(risk_metrics_bp)
    app.register_blueprint(academic_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(costbenefit_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
