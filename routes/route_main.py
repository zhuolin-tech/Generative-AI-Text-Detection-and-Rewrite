from flask import Blueprint, request, jsonify
from services.service_main import MainService

main_service = MainService()

main_bp = Blueprint('main', __name__)

"""
main_bp: API Overview
    /humanize Post 
       humanize_text() 
       Returns AI text beautification result
    /check Post 
       check_text() 
       Returns AI text detection result
    /history Post 
       history() 
       Returns user history records
    /history_spend Post 
       history_with_spend() 
       Returns user history and spending records
    /recharge Post 
        recharge() 
        User recharge
    /process_file Post 
       process_file() 
       Process file
    /sensitive_words Post 
       sensitive_words() 
       Sensitive word detection
"""

@main_bp.route('/humanize', methods=['POST'])
def humanize_text():
    # Get request parameters
    data = request.json
    user_id = data.get('user_id')
    origin_text = data.get('origin_text')
    mode = data.get('mode', 'medium')

    # Call service layer
    response, status = main_service.process_humanized_text(user_id, origin_text, mode)
    return jsonify(response), status

@main_bp.route('/humanize_chunks', methods=['POST'])
def humanize_chunks():
    # Get request parameters
    data = request.json
    user_id = data.get('user_id')
    origin_text = data.get('origin_text')
    chunks = data.get('chunks')  # Sentences that are already identified as AI-generated
    mode = data.get('mode', 'medium')

    # Call service layer
    response, status = main_service.process_humanize_chunks(user_id, origin_text, chunks, mode)
    return jsonify(response), status

@main_bp.route('/check', methods=['POST'])
def check_text():
    # Get request parameters
    data = request.json
    user_id = data.get('user_id')
    origin_text = data.get('origin_text')

    # Call service layer
    response, status = main_service.process_check_text(user_id, origin_text)
    return jsonify(response), status


@main_bp.route('/history', methods=['POST', 'GET'])
def history():
    # Get request parameters
    data = request.json
    user_id = data.get('user_id')
    history_type = data.get('history_type')

    # Call service layer
    response, status = main_service.get_history(user_id, history_type)
    return jsonify(response), status

@main_bp.route('/history_spend', methods=['POST', 'GET'])
def history_with_spend():
    # Get request parameters
    data = request.json
    user_id = data.get('user_id')
    history_type = data.get('history_type')

    # Call service layer
    response, status = main_service.get_history_with_spend(user_id, history_type)
    return response, status

@main_bp.route('/recharge', methods=['POST'])
def recharge():
    # Get request parameters
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount')
    amount_type = data.get('amount_type')
    recharge_credit = data.get('recharge_credit')
    recharge_type = data.get('recharge_type')

    # Call service layer
    response, status = main_service.process_recharge(user_id, amount, amount_type, recharge_credit, recharge_type)
    return jsonify(response), status


# TODO May need to modify to add user validation for uploads
@main_bp.route('/process_file', methods=['POST'])
def process_file():
    # Check if file exists in request
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # If filename is empty
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Call service layer to process file
    response, status = main_service.process_file(file)
    # Return result
    return jsonify(response), status


@main_bp.route('/sensitive_words', methods=['POST', 'GET'])
def sensitive_words():
    # Get request parameters
    data = request.json
    origin_text = data.get('origin_text')

    # Call service layer to process file
    response, status = main_service.process_sensitive_words(origin_text)
    # Return result
    return jsonify(response), status
