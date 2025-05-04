from flask import Blueprint, jsonify

health_checks_bp = Blueprint('health_checks', __name__)

@health_checks_bp.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint to verify the application is running.
    """
    return jsonify({"status": "success", "message": "Hello, World!"}), 200
