import logging
from forms.form_user import UserForm
from forms.form_main import MainForm
from toolkit import InputProcessing, LoggerManager

class UserService:
    def __init__(self):
        # Import input processing module
        self.input_processing = InputProcessing()
        # Import user form module
        self.user_form = UserForm()
        # Import main form module
        self.main_form = MainForm()

        # Configure logger manager
        logging.basicConfig(filename='logs/services.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.services_logger = LoggerManager('services_logger', 'logs/services.log').get_logger()  # Create logger object

    def register_user(self, user_name, user_email, password):
        """
        Register a new user
        Input parameters:
            - user_name: Username
            - user_email: User email
            - password: Password
        Output parameters:
            - Returns registration result and HTTP status code
            - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """

        # ####### Data Processing Section #####################
        user_id = self.input_processing.user_id()  # Generate user ID
        password_hash = self.input_processing.hash_password(password)  # Hash password
        current_time = self.input_processing.get_current_time()  # Get current time
        user_email = user_email.lower()  # Convert to lowercase
        recharge_type = "gift"

        # ####### Data Validation Section #####################
        # Check if parameters are empty
        if not user_name or not user_email or not password:
            return {"error": "valid input are required"}, 400

        # Check if user email already exists
        if self.user_form.check_user_email_exists(user_email):
            return {"error": "user_email is already exists"}, 400

        session = self.main_form.Session()
        # ####### Main Form Query and Logic Processing Section #####################
        try:
            if not self.user_form.add_user(user_id, user_name, user_email, password_hash, current_time):
                raise Exception("Database insert user failed")

            if not self.main_form.add_recharge_history(session, user_id, current_time, 0,
                                                       'USD', 500, recharge_type):
                raise Exception("Database insert recharge_history failed")


            return {"user_id": user_id, "message": "register success"}, 200

        # ####### Exception Handling Section #####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def login_user(self, user_email, password):
        """
        User login
        Input parameters:
            - user_email: User email
            - password: Password
        Output parameters:
            - Returns login result and HTTP status code
            - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """
        # ####### Data Processing Section #####################

        password_hash = self.input_processing.hash_password(password)  # Hash password
        user_email = user_email.lower()  # Convert to lowercase

        # ####### Data Validation Section #####################
        # Check if parameters are empty
        if not user_email or not password:
            return {"error": "valid input are required"}, 400

        # Check if user email exists
        if not self.user_form.check_user_email_exists(user_email):
            return {"error": "user_email is not exists"}, 400

        # ####### Main Form Query and Logic Processing Section ##############
        try:
            user_id = self.user_form.verify_user(user_email, password_hash)
            print(user_id, password_hash, user_email)
            if not user_id:
                return {"error": "user_email or password is not correct"}, 400
            return {"user_id": user_id, "message": "login success"}, 200

        # ####### Exception Handling Section ####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def update_user(self, user_id, update_type, new_value):
        """
        Update user information
        Input parameters:
            - user_id: User ID
            - update_type: Update type, such as email, password, etc.
            - new_value: New value
        Output parameters:
            - Returns update result and HTTP status code
            - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """
        # ####### Data Processing Section #####################
        current_time = self.input_processing.get_current_time()  # Get current time

        # ####### Data Validation Section #####################

        # Check if parameters are empty
        if not user_id or not update_type or not new_value:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # ####### Main Form Query and Logic Processing Section ##########
        try:
            if not self.user_form.update_user(user_id, update_type, new_value, current_time):
                raise Exception("Database update user failed")
            return {"user_id": user_id, "message": "update success"}, 200

        # ####### Exception Handling Section #####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def delete_user(self, user_id):
        """
        Delete user
        Input parameters:
            - user_id: User ID
        Output parameters:
            - Returns deletion result and HTTP status code
            - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """
        # ####### Data Processing Section ####################

        # ####### Data Validation Section #####################
        # Check if parameters are empty
        if not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # ####### Main Form Query and Logic Processing Section ##########
        try:
            if not self.user_form.delete_user(user_id):
                raise Exception("Database delete user failed")
            return {"user_id": user_id, "message": "delete success"}, 200
        # ####### Exception Handling Section #####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def update_password(self, user_email, new_password):
        """
        Update user password
        Input parameters:
            - user_email: User email
            - new_password: New password
        Output parameters:
            - Returns update result and HTTP status code
            - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """
        # ####### Data Processing Section ####################
        password_hash = self.input_processing.hash_password(new_password)  # Hash password
        current_time = self.input_processing.get_current_time()  # Get current time
        user_email = user_email.lower()  # Convert to lowercase

        # ####### Data Validation Section ####################
        # Check if parameters are empty
        if not user_email or not new_password:
            return {"error": "valid input are required"}, 400

        # Check if user email exists
        if not self.user_form.check_user_email_exists(user_email):
            return {"error": "user_email is not exists"}, 400

        # ####### Main Form Query and Logic Processing Section ##########
        try:
            if not self.user_form.update_password_email(user_email, password_hash, current_time):
                raise Exception("Database update password failed")
            return {"user_email": user_email, "message": "update password success"}, 200

        # ####### Exception Handling Section ####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def get_user_info(self, user_id):
        """
        Get user information
        Input parameters:
            - user_id: User ID
        Output parameters:
            - Returns user information and HTTP status code
            - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """
        # ####### Data Processing Section ####################

        # ####### Data Validation Section #####################
        # Check if parameters are empty
        if not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # ####### Main Form Query and Logic Processing Section ##########
        try:
            user_info = self.user_form.get_user_by_id(user_id)
            if not user_info:
                raise Exception("Database get user failed")
            return user_info, 200
        # ####### Exception Handling Section #####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def check_user_email(self, user_email):
        """
        Check if user email exists
        Input parameters:
            - user_email: User email
        Output parameters:
            - Returns whether email exists and HTTP status code
            - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """

        # ####### Data Validation Section ##########
        # Check if parameters are empty
        if not user_email:
            return {"error": "valid input are required"}, 400


        # ####### Data Processing Section ####################
        user_email = user_email.lower()  # Convert to lowercase


        # ####### Main Form Query and Logic Processing Section ##########
        try:
            if self.user_form.check_user_email_exists(user_email):
                return {"message": "user_email is already exists"}, 200
            else:
                return {"message": "user_email is not exists"}, 200

        # ####### Exception Handling Section ########
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500
