import logging
from forms.form_payment import PaymentForm
from forms.form_user import UserForm
from forms.form_main import MainForm
from toolkit import InputProcessing, LoggerManager
from external_api import StripeAPI, AirwallexAPI


class PaymentService:
    def __init__(self):

        # Import and instantiate related modules
        self.input_processing = InputProcessing()  # Import input processing module
        self.payment_form = PaymentForm()  # Import payment form module
        self.user_form = UserForm()  # Import user form module
        self.main_form = MainForm()  # Import main form module
        self.stripe_api = StripeAPI()  # Import Stripe API module
        self.airwallex_api = AirwallexAPI()  # Import Airwallex API module

        # Configure logger manager
        logging.basicConfig(filename='logs/services.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.services_logger = LoggerManager('services_logger', 'logs/services.log').get_logger()  # Create logger object


    def get_payment_intent_key(self, user_id, amount, currency, payment_servers_type: str = "stripe"):
        """
        Get payment intent key for generating payment link in frontend and save related data in database
        Input parameters:
            - user_id: User ID
            - amount: Payment amount
            - currency: Payment currency
            - payment_servers_type: Payment server type (stripe or airwallex)
        Output parameters:
            - Returns payment intent key result and HTTP status code
            - HTTP status code: 200 for success, 400 for parameter error, 500 for server error
        """
        # ####### External API Interface Call Section #####################
        try:
            # Call API interface to get client secret
            if payment_servers_type == "stripe":
                client_secret = self.stripe_api.get_client_secret(user_id, amount, currency)  # Get client secret

            elif payment_servers_type == "airwallex":
                airwallex_api_result = self.airwallex_api.get_client_secret(user_id, amount, currency)  # Get client secret
                # Use airwallex_id as client_secret in database, as airwallex_id corresponds to stripe's client_secret
                client_secret = airwallex_api_result.get("airwallex_id")
                secret_jwt = airwallex_api_result.get("secret_jwt")  # secret_jwt is still needed as return result during payment
            else:
                raise ValueError("Unsupported payment server type")

        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

        # ####### Data Processing Section #####################

        current_time = self.input_processing.get_current_time()  # Get current time

        currency = currency.upper()  # Convert payment currency to uppercase

        # ####### Data Validation Section #####################
        # Check if parameters are empty
        if not user_id or not amount or not currency:
            return {"error": "valid input are required"}, 400

        # Check if user ID exists
        if not self.user_form.check_user_id_exists(user_id):
            return {"error": "user_id is not exists"}, 400

        # ####### Main Form Query Section and Logic Processing #####################

        try:

            session = self.payment_form.Session()  # Get session object
            try:
                # Insert payment intent data into database
                if not self.payment_form.add_payment_intent(session, user_id, amount, currency, client_secret,
                                                            current_time):
                    raise Exception("Database insert payment_intent failed")
                session.commit()

            except Exception as e:
                session.rollback()  # Rollback
                raise e  # Raise exception for logging and return 500 HTTP status code
            finally:
                session.close()
            if payment_servers_type == "stripe":
                return {"clientSecret": client_secret}, 200  # Success, return client secret 200
            elif payment_servers_type == "airwallex":
                return {"intent_id": client_secret, "client_secret": secret_jwt}, 200  # Success, return intent_id and client_secret 200

        # ####### Exception Handling Section #####################
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def process_payment_result(self, payment_result_id, payment_servers_type: str = "stripe"):
        """
        Process payment result, get payment result by payment result ID and perform related operations
        Input parameters:
            - payment_result_id: Payment result ID
            - payment_servers_type: Payment server type (stripe or airwallex)
        Output parameters:
            - Returns processed payment result and HTTP status code
            - HTTP status code: 200 for success, 400 for parameter error, 500 for server error
        """
        # ####### External API Interface Call Section #####################

        try:
            # Call API interface to get payment result
            if payment_servers_type == "stripe":
                payment_result = self.stripe_api.get_payment_result(payment_result_id)  # Get payment result

            elif payment_servers_type == "airwallex":
                payment_result = self.airwallex_api.get_payment_result(payment_result_id)  # Get payment result
            else:
                raise ValueError("Unsupported payment server type")

        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

        # ####### Data Processing Section #####################

        current_time = self.input_processing.get_current_time()  # Get current time
        recharge_type = "payment"  # Recharge type

        # ####### Data Validation Section ###############
        # Check if parameters are empty
        if not payment_result_id:
            return {"error": "valid input are required"}, 400

        # ####### Main Form Query Section and Logic Processing ########

        try:
            # Parse JSON string to Python dictionary
            response_dict = payment_result
            # Access dictionary fields
            user_id = response_dict["user_id"]  # User ID
            client_secret = response_dict["client_secret"]  # Client secret
            amount = response_dict["amount"]  # Payment amount
            amount_received = response_dict["amount_received"]  # Actual received amount
            currency = response_dict["currency"]  # Payment currency
            status = response_dict["status"]  # Payment status
            payment_types = response_dict["payment_types"]  # Payment method

            amount_converted = self.input_processing.convert_amount(amount_received)  # Convert payment amount from cents to dollars and to float
            recharge_credit = self.input_processing.get_credit(amount, currency)  # Get recharge credits
            currency = currency.upper()  # Convert payment currency to uppercase

            # Convert payment time format based on different payment systems
            if payment_servers_type == "stripe":
                created = response_dict["created"]  # Payment creation time
                created_time = self.input_processing.convert_unix_time(created)  # Convert payment creation time from unix
            elif payment_servers_type == "airwallex":
                created_time = self.input_processing.convert_format_datetime(response_dict["created"])  # Payment creation time
                created = self.input_processing.convert_time_unix(response_dict["created"])  # Convert payment creation time to unix

            payment_status = "failed"  # Payment status
            if status == "succeeded" and amount == amount_received:
                payment_status = "succeeded"

            # TODO Validate payment amount, currency, status, creation time, and payment method

            # Validate if user ID exists
            if not self.user_form.check_user_id_exists(user_id):
                return {"error": "user_id is not exists"}, 400

            # Validate if client secret exists
            if not self.payment_form.check_client_secret_exists(client_secret):
                return {"error": "client_secret is not exists"}, 400

            # Validate if result ID exists
            if self.payment_form.check_payment_result_id_exists(payment_result_id):
                return {"error": "payment is already exists"}, 400


            session = self.payment_form.Session()
            try:
                # Only insert payment result data into main form if status is successful
                if status == "succeeded" and amount == amount_received:
                    if not self.main_form.add_recharge_history(session, user_id, current_time, amount_converted,
                                                               currency, recharge_credit, recharge_type):
                        raise Exception("Database insert recharge_history failed")

                if not self.payment_form.add_payment_result(session, user_id, payment_result_id, amount, amount_received, client_secret,
                                                            currency, status, created, created_time, current_time, payment_types):
                    raise Exception("Database insert payment_result failed")

                session.commit()

            except Exception as e:
                session.rollback()  # Rollback
                raise e  # Raise exception for logging and return 500 HTTP status code
            finally:
                session.close()

            # Success, return processed payment result 200
            return {"user_id": user_id, "status": payment_status, "amount": amount_converted,
                    "currency": currency,"payment_types": payment_types, "created": created_time.strftime('%Y-%m-%d %H:%M:%S')}, 200

        # ####### Exception Handling Section ########
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500

    def get_payment_rate(self):
        """
        Get payment rate table for various currencies
        Input parameters:
            - None
        Output parameters:
            - Returns payment rate table for various currencies and HTTP status code
            - HTTP status code: 200 for success, 500 for server error
        """
        try:

            package_titles = [
                "Entry Package",
                "Basic Package",
                "Standard Package",
                "Premium Package",
                "Diamond Package",
                "Enterprise Package"
            ]

            amount_to_credit_map_cny = self.input_processing.get_amount_to_credit_map('CNY')  # Get CNY recharge credit table
            amount_to_credit_map_usd = self.input_processing.get_amount_to_credit_map('USD')  # Get USD recharge credit table
            amount_to_credit_map_cad = self.input_processing.get_amount_to_credit_map('CAD')  # Get CAD recharge credit table

            # Use package_titles for mapping
            def format_payment_data(amount_to_credit_map):
                formatted_data = []
                for i, (price, credit) in enumerate(amount_to_credit_map.items()):
                    package = {
                        "name": package_titles[i] if i < len(package_titles) else f"Package {i+1}",
                        "price": int(price),  # Convert to integer
                        "credits": credit
                    }
                    formatted_data.append(package)
                return formatted_data

            # Format payment data for different currencies
            payment_rate_data = {
                "CNY": format_payment_data(amount_to_credit_map_cny),
                "USD": format_payment_data(amount_to_credit_map_usd),
                "CAD": format_payment_data(amount_to_credit_map_cad)
            }

            # Return payment rate table in JSON format and status code 200
            return payment_rate_data, 200

        # ####### Exception Handling Section ########
        except Exception as e:
            self.services_logger.error(f"Internal Server Error: {e}")
            return {"error": "Internal Server Error"}, 500


