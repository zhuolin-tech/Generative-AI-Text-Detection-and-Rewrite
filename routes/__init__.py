# Import blueprint modules
from routes.route_main import main_bp
from routes.route_user import user_bp
from routes.route_payment import payment_bp
from routes.route_refer import refer_bp

def init_app(app):
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(refer_bp)

    return app

"""
Route path definitions and interface function descriptions for each blueprint

main_bp:
    /humanize Post API
       humanize_text() 
       Calls service layer humanize_text() function, returns AI text beautification result
    /check Post API
       detection_text() 
       Calls service layer detection_text() function, returns AI text detection result
    /history Post API
       user_history() 
       Calls service layer user_history() function, returns user history records
    /history_spend Post API
       user_history_with_spend() 
       Calls service layer user_history_with_spend() function, returns user history records
    /recharge Post API
        user_recharge() 
        Calls service layer user_recharge() function, returns user recharge result

user_bp: API Overview
    /register Post API
       user_register() 
       Gets request parameters user_name, user_email, password, calls service layer register_user() function, returns registration result
    /login Post API
       user_login() 
       Gets request parameters user_email, password, calls service layer login_user() function, returns login result
    /replace Post API
       user_replace() 
       Gets request parameters user_id, update_type, new_value, calls service layer update_user() function, returns user information update result
    /delete Post API
       user_delete() 
       Gets request parameters user_id, calls service layer delete_user() function, returns user deletion result
    /update_password Post API
       update_password() 
       Gets request parameters user_email, new_password, calls service layer update_password() function, returns password update result
    /user_info Post API
       user_information() 
       Gets request parameters user_id, calls service layer get_user_info() function, returns user information


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

refer_bp: API Overview


from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
user_bp = Blueprint('user', __name__)
payment_bp = Blueprint('payment', __name__)
refer_bp = Blueprint('refer', __name__)


"""