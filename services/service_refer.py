import logging
from forms.form_main import MainForm
from forms.form_user import UserForm
from forms.form_refer import ReferForm
from toolkit import InputProcessing, LoggerManager

class ReferService:
    def __init__(self):

        # Import input processing module
        self.input_processing = InputProcessing()
        # Import main form module
        self.main_form = MainForm()
        # Import user form module
        self.user_form = UserForm()
        # Import referral form module
        self.refer_form = ReferForm()

        # Configure logger manager
        logging.basicConfig(filename='logs/services.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.services_logger = LoggerManager('services_logger', 'logs/services.log').get_logger()  # Create logger object

    def process_get_refer_code(self, user_id):
        """
        Get user's referral code
        Input:
          - user_id: User ID
        Output:
          - Returns the created referral code
          - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """

        # ####### Data Processing Section #####################
        current_time = self.input_processing.get_current_time()
        new_refer_code_record = self.input_processing.generate_refer_code(user_id, current_time.strftime("%Y-%m-%d %H:%M:%S"))
        user_type = "normal"

        # ####### Data Validation Section ###############
        # Check if user_id is empty
        if not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id does not exist"}, 400

        # Check if user has already created a referral code
        refer_code = self.refer_form.get_refer_code_by_user_id(user_id)
        if refer_code:
            # If exists, return the existing referral code
            return {"refer_code": refer_code}, 200

        # TODO Check if referral code exists, avoid conflicts, generate a new one if exists

        # ####### Main Form Query and Logic Processing Section ########

        session = self.refer_form.Session()

        try:
            # If not exists, create new referral code and write to database
            if not self.refer_form.create_new_refer_code(session, user_id, new_refer_code_record, user_type, current_time):
                raise Exception("Database insert refer code failed")

            session.commit()
            return {"refer_code": new_refer_code_record}, 200
        # ####### Exception Handling Section ##################
        except Exception as e:
            session.rollback()
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500
        finally:
            session.close()

    def process_use_refer_code(self, user_id, refer_code, recharge_credit):
        """
        Use referral code, user recharges and receives rewards
        Input:
          - user_id: User ID
          - refer_code: Created referral code
          - recharge_credit: Recharge credits
        Output:
          - Returns success/failure message as boolean
          - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """
        # ####### Data Processing Section ########
        current_time = self.input_processing.get_current_time()

        from_user_reward_credit = recharge_credit * 0.25
        to_user_reward_credit = recharge_credit * 0.50

        recharge_amount = 0
        recharge_currency = "usd"
        recharge_type = "refer"

        # ####### Data Validation Section ####################
        # TODO Too many validation checks, need optimization, also consider sales type
        # Check if user_id is empty
        if not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id does not exist"}, 400

        # Check if referral code exists
        if not self.refer_form.get_user_id_by_refer_code(refer_code):
            return {"error": "refer_code does not exist"}, 400

        # Check if recharge amount is less than or equal to 0
        if recharge_credit <= 0:
            return {"error": "recharge should not below zero"}, 400

        # Check if user has used any referral code before (first-time use check)
        if self.refer_form.check_refer_history_exists(user_id):
            return {"error": "cannot get referred twice"}, 400

        # Check if referral code creator exists
        from_user_id = self.refer_form.get_user_id_by_refer_code(refer_code)
        if not from_user_id:
            return {"error": "creat refer code user does not exist"}, 400

        # Check if user is trying to refer themselves
        if from_user_id == user_id:
            return {"error": "can not refer yourself"}, 400

        # ####### Main Form Query and Logic Processing Section ########
        session = self.refer_form.Session()
        session_main = self.main_form.Session()
        try:
            if not self.refer_form.create_new_refer_history(session, from_user_id, user_id, refer_code, current_time, recharge_credit):
                raise Exception("Database insert refer history failed")

            # Add credits to referred user
            if not self.main_form.add_recharge_history(session_main, user_id, current_time, recharge_amount, recharge_currency, to_user_reward_credit, recharge_type):
                raise Exception("Database insert recharge history failed")

            # Add credits to referrer
            if not self.main_form.add_recharge_history(session_main, from_user_id, current_time, recharge_amount, recharge_currency, from_user_reward_credit, recharge_type):
                raise Exception("Database insert recharge history failed")

            session.commit()
            return {"message":"Referral succeed"}, 200
        # ####### Exception Handling Section ##################
        except Exception as e:
            session.rollback()
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500
        finally:
            session.close()

    def process_get_refer_history(self, user_id):
        """
        Query specific user's referral history
        Input:
          - user_id: User ID
        Output:
          - Returns referral history records
          - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """
        # ####### Data Processing Section #####################

        # ####### Data Validation Section ####################

        # Check if user_id is empty
        if not user_id:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id does not exist"}, 400

        # ####### Main Form Query and Logic Processing Section ########
        try:
            # Query referral history
            history_records = self.refer_form.get_refer_history_by_user_id(user_id)

            # Convert set to list if result is set type
            if isinstance(history_records, set):
                history_records = list(history_records)

            # Serialize history records
            result = [{
                "refer_from_user_name": self.user_form.get_user_by_id(record.refer_from_user_id).get("user_name"),
                "refer_to_user_name": self.user_form.get_user_by_id(record.refer_to_user_id).get("user_name"),
                "refer_code": record.refer_code,
                "refer_time": record.refer_time,
                "recharge_credit": record.recharge_credit
            } for record in history_records]


            return result, 200  # Success, return history records

        # ####### Exception Handling Section ##################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def process_refer_code_check(self, user_id, refer_code):
        """
        Check if referral code is valid
        Input:
          - user_id: User ID
          - refer_code: Created referral code
        Output:
          - Returns boolean indicating if referral code is valid
          - HTTP status codes: 200 for success, 400 for parameter errors, 500 for server errors
        """
        # ####### Data Processing Section #####################

        # ####### Data Validation Section ########

        # Check if user_id is empty
        if not user_id:
            return {"message": False}, 200

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"message": False}, 200

        # Check if referral code exists
        if not self.refer_form.get_user_id_by_refer_code(refer_code):
            return {"message": False}, 200

        # Check if user has used any referral code before (first-time use check)
        if self.refer_form.check_refer_history_exists(user_id):
            return {"message": False}, 200

        # Check if referral code creator exists
        from_user_id = self.refer_form.get_user_id_by_refer_code(refer_code)
        if not from_user_id:
            return {"message": False}, 200

        # Check if user is trying to refer themselves
        if from_user_id == user_id:
            return {"message": False}, 200

        # ####### Main Form Query and Logic Processing Section ########
        try:
            return {"message": True}, 200  # Success, return True

        # ####### Exception Handling Section ########
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

