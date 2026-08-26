import io

import pandas as pd
from flask import Blueprint, Response, render_template, send_file

from services import export_service
from services.model_service import is_trained
from services.nav import get_nav_context

download_bp = Blueprint("download", __name__, url_prefix="/download")


@download_bp.route("/")
def index():
    if not is_trained():
        return render_template("model_missing.html", nav=get_nav_context("download.index"))
    exports = [dict(key=k, label=label) for k, (label, _) in export_service.EXPORTS.items()]
    return render_template("download.html", exports=exports, nav=get_nav_context("download.index"))


@download_bp.route("/<key>.csv")
def csv(key):
    if key not in export_service.EXPORTS:
        return "Unknown export", 404
    _, builder = export_service.EXPORTS[key]
    df = builder()
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={key}.csv"},
    )


@download_bp.route("/<key>.xlsx")
def xlsx(key):
    if key not in export_service.EXPORTS:
        return "Unknown export", 404
    label, builder = export_service.EXPORTS[key]
    df = builder()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=label[:31])
    buf.seek(0)
    return send_file(
        buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True, download_name=f"{key}.xlsx",
    )
