from flask import Blueprint

api_bp = Blueprint("api", __name__)

from api import auth_routes, profile_routes, praktyki_routes, dziennik_routes  # noqa
from api import dokumenty_routes, pdf_routes, wnioski_routes  # noqa
from api import zmiana_terminu_routes, przedluzenie_routes  # noqa
from api.errors import register_error_handlers

register_error_handlers(api_bp)
