from flask import jsonify


def register_error_handlers(bp):
    @bp.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Nieprawidłowe żądanie", "message": str(e)}), 400

    @bp.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Brak autoryzacji"}), 401

    @bp.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Brak dostępu"}), 403

    @bp.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Nie znaleziono"}), 404

    @bp.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "Plik za duży", "message": "Maksymalny rozmiar: 16 MB"}), 413

    @bp.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Błąd serwera"}), 500
