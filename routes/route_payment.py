from flask import Blueprint, request, jsonify
from services.service_payment import PaymentService

payment_service = PaymentService()

payment_bp = Blueprint('payment', __name__)

"""
payment_bp: API Overview
    /create_payment Post 
       create_payment() 
       Create payment order and return client payment intent key
    /payment_result Post API
       payment_result() 
       Receive payment result and update order status
    /create_payment_airwallex Post API (Australian Payment Company)
       create_payment_airwallex() 
       Create payment order and return client payment intent key
    /payment_result_airwallex Post API (Australian Payment Company)
       payment_result_airwallex() 
       Receive payment result and update order status
"""

@payment_bp.route('/create_payment', methods=['POST'])
def create_payment():
    # Get request parameters
    data = request.get_json()
    user_id = data['user_id']
    amount = data['amount']
    currency = data['currency']

    # Call service layer
    response, status = payment_service.get_payment_intent_key(user_id, amount, currency, 'stripe')
    return jsonify(response), status

@payment_bp.route('/payment_result', methods=['POST'])
def payment_result():
    # Get request parameters
    data = request.get_json()
    payment_result_id = data['payment_result_id']

    # Call service layer
    response, status = payment_service.process_payment_result(payment_result_id, 'stripe')
    return jsonify(response), status


@payment_bp.route('/create_payment_airwallex', methods=['POST'])
def create_payment_airwallex():
    # Get request parameters
    data = request.get_json()
    user_id = data['user_id']
    amount = data['amount']
    currency = data['currency']

    # Call service layer
    response, status = payment_service.get_payment_intent_key(user_id, amount, currency, 'airwallex')
    return jsonify(response), status

@payment_bp.route('/payment_result_airwallex', methods=['POST'])
def payment_result_airwallex():
    # Get request parameters
    data = request.get_json()
    payment_result_id = data['intent_id']

    # Call service layer
    response, status = payment_service.process_payment_result(payment_result_id, 'airwallex')
    return jsonify(response), status

@payment_bp.route('/payment_rate', methods=['GET'])
def payment_rate():
    # No parameters required

    # Call service layer
    response, status = payment_service.get_payment_rate()
    return jsonify(response), status

