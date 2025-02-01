from flask import Blueprint, request, jsonify
from services.service_user import UserService

user_service = UserService()

user_bp = Blueprint('user', __name__)

"""
user_bp: API Overview
    /register Post 
       user_register() 
       Returns registration result
    /login Post API
       user_login() 
       Returns login result
    /replace Post 
       user_replace() 
       Returns user information update result
    /delete Post 
       user_delete() 
       Returns user deletion result
    /update_password Post 
       update_password() 
       Returns password update result
    /user_info Post 
       user_information() 
       Returns user information
    /user_email Get 
       check_user_email() 
       Returns whether user email exists
"""

@user_bp.route('/register', methods=['POST'])
def user_register():
    # Get request parameters
    data = request.json
    user_name = data.get('user_name')
    user_email = data.get('user_email')
    password = data.get('password')

    # Call service layer
    response, status = user_service.register_user(user_name, user_email, password)
    return jsonify(response), status

@user_bp.route('/login', methods=['POST', 'GET'])
def user_login():
    # Get request parameters
    data = request.json
    user_email = data.get('user_email')
    password = data.get('password')

    # Call service layer
    response, status = user_service.login_user(user_email, password)
    return jsonify(response), status

@user_bp.route('/replace', methods=['POST', 'PATCH'])
def user_replace():
    # Get request parameters
    data = request.json
    user_id = data.get('user_id')
    update_type = data.get('update_type')
    new_value = data.get('new_value')

    # Call service layer
    response, status = user_service.update_user(user_id, update_type, new_value)
    return jsonify(response), status

@user_bp.route('/delete', methods=['POST', 'DELETE'])
def user_delete():
    # Get request parameters
    data = request.json
    user_id = data.get('user_id')

    # Call service layer
    response, status = user_service.delete_user(user_id)
    return jsonify(response), status

@user_bp.route('/update_password', methods=['POST', 'PATCH'])
def update_password():
    # Get request parameters
    data = request.json
    user_email = data.get('user_email')
    new_password = data.get('new_password')

    # Call service layer
    response, status = user_service.update_password(user_email, new_password)
    return jsonify(response), status

@user_bp.route('/user_info', methods=['POST', 'GET'])
def user_information():
    # Get request parameters
    data = request.json
    user_id = data.get('user_id')

    # Call service layer
    response, status = user_service.get_user_info(user_id)
    return jsonify(response), status

@user_bp.route('/user_email', methods=['GET'])
def user_email():
    # Get request parameters
    data = request.json
    user_email = data.get('user_email')

    # Call service layer
    response, status = user_service.check_user_email(user_email)
    return jsonify(response), status

