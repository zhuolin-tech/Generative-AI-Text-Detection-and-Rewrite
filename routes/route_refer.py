from flask import Blueprint, request, jsonify
from services.service_refer import ReferService

refer_service = ReferService()

refer_bp = Blueprint('refer', __name__)

"""
refer_bp: Referral Code Related APIs
    /get_refer_code Post
       get_refer_code()
       User queries referral code. Input user ID, generates a new referral code if none exists, or returns existing code.
       
    /use_refer_code Post
       use_refer_code()
       User uses referral code for recharge. Input user ID, referral code, and recharge credits. System validates code, records usage, and awards credits according to rules.
       
    /get_refer_history Post
       get_refer_history()
       Query referral history. Input user ID, returns user's referral history including referral time, used code, and recharge credits.
"""

@refer_bp.route('/get_refer_code', methods=['POST'])
def get_refer_code():
    # Get request parameters
    data = request.get_json()
    user_id = data['user_id']

    # Call service layer
    response, status = refer_service.process_get_refer_code(user_id)
    return jsonify(response), status

@refer_bp.route('/use_refer_code', methods=['POST'])
def use_refer_code():
    # Get request parameters
    data = request.get_json()
    user_id = data['user_id']
    refer_code = data['refer_code']
    recharge_credit = data['recharge_credit']

    # Call service layer
    response, status = refer_service.process_use_refer_code(user_id, refer_code, recharge_credit)
    return jsonify(response), status

@refer_bp.route('/get_refer_history', methods=['POST'])
def get_refer_history():
    # Get request parameters
    data = request.get_json()
    user_id = data['user_id']

    # Call service layer
    response, status = refer_service.process_get_refer_history(user_id)
    return jsonify(response), status

@refer_bp.route('/refer_code_check', methods=['POST'])
def get_refer_check():
    # Get request parameters
    data = request.get_json()
    user_id = data['user_id']
    refer_code = data['refer_code']

    # Call service layer
    response, status = refer_service.process_refer_code_check(user_id, refer_code)
    return jsonify(response), status

