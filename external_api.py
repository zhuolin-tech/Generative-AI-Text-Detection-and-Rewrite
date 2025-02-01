import requests
from toolkit import LoggerManager, InputProcessing
import logging
import stripe
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.pool import PoolOptions

class DocumentProcess:
    def __init__(self):

        self.url_fastapi = "https://document-6meya.ondigitalocean.app"

        # Configure logger
        logging.basicConfig(filename='logs/api.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.api_logger = LoggerManager('api_logger', 'logs/api.log').get_logger()  # Create strategy logger object

    def trans_to_human(self, original_text: str, mode: str) -> dict:
        """
        Process a single text humanization request.
        Parameters:
            - original_text (str): The original text to be processed.
            - mode (str): Humanization mode. Available values: 'aggressive', 'medium', 'easy'.
        Returns:
            - dict: Dictionary containing the processed text.
        """
        url = f"{self.url_fastapi}/humanize"

        # Map mode to strength value
        mode_to_strength = {
            "aggressive": "More Human",
            "medium": "Balanced",
            "easy": "Quality"
        }

        # Get mapped strength value, default to "Balanced" if mode is invalid
        strength = mode_to_strength.get(mode.lower(), "Balanced")

        payload = {
            "content": original_text,
            "readability": "University",  # Can be adjusted as needed
            "purpose": "Essay",           # Can be adjusted as needed
            "strength": strength
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            self.api_logger.info("Single humanization request successful.")
            return result
        except requests.RequestException as e:
            self.api_logger.error(f"Single humanization request failed: {e}")
            return {"error": str(e)}

    def trans_to_human_list(self, original_text_list: list, mode: str) -> dict:
        """
        Process a list of texts for humanization.
        Parameters:
            - original_text_list (list): List of texts to be processed.
            - mode (str): Humanization mode. Available values: 'aggressive', 'medium', 'easy'.
        Returns:
            - dict: Dictionary containing the processed text list.
        """
        url = f"{self.url_fastapi}/humanize_list"

        # Map mode to strength value
        mode_to_strength = {
            "aggressive": "More Human",
            "medium": "Balanced",
            "easy": "Quality"
        }

        # Get mapped strength value, default to "Balanced" if mode is invalid
        strength = mode_to_strength.get(mode.lower(), "Balanced")

        payload = {
            "content_list": original_text_list,
            "readability": "University",
            "purpose": "Essay",
            "strength": strength
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.api_logger.error(f"List humanization request failed: {e}")
            return {"error": str(e)}

    def get_balance(self) -> dict:
        """
        Get the API key balance.
        Returns:
            - dict: Balance in JSON format.
        """
        url = f"{self.url_fastapi}/balance"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.api_logger.error(f"Balance check request failed: {e}")
            return {"error": str(e)}

    def ai_detection(self, original_text: str) -> dict:
        """
        Perform AI detection on input text.
        Parameters:
            - original_text (str): Text to be analyzed.
        Returns:
            - dict: AI detection results in JSON format.
        """
        url = f"{self.url_fastapi}/check"
        payload = {"content": original_text}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.api_logger.error(f"AI detection request failed: {e}")
            return {"error": str(e)}


class StripeAPI:
    def __init__(self):

        load_dotenv()
        # Load Stripe environment variables
        self.pay_key = os.getenv("STRIPE_PAY")

        # Connect and configure MongoDB database and collections
        mongo_url = os.getenv('MONGO_DB_CLOUD')  # Database connection URI
        client = MongoClient(   # Database connection using connection pool
            mongo_url,
            maxPoolSize=10,  # Maximum connections
            minPoolSize=5,   # Minimum connections
            socketTimeoutMS=20000,  # Socket timeout (milliseconds)
            serverSelectionTimeoutMS=5000  # Server selection timeout (milliseconds)
        )
        db = client['external_api']  # Select database
        self.collection_intent = db['stripe_intent']  # Collection for storing Stripe payment intent data
        self.collection_result = db['stripe_result']  # Collection for storing Stripe payment result data

        # Configure logger
        logging.basicConfig(filename='logs/api.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.api_logger = LoggerManager('api_logger', 'logs/api.log').get_logger()


    def get_client_secret(self, user_id: str, amount: int, currency: str) -> str or None:
        """
        This function returns a client secret for payment intent given user ID, amount, and currency.
        Parameters:
           - user_id: User ID
           - amount: Amount
           - currency: Currency
        Returns:
           - client_secret: Client secret
        """
        try:
            stripe.api_key = self.pay_key

            # Create Stripe payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata={"user_id": user_id}
            )

        except Exception as e:
            self.api_logger.error(f"Request to Stripe API failed get_client_secret : {e}")
            return None

        # Save data to MongoDB database
        self.collection_intent.insert_one(payment_intent)

        return payment_intent.client_secret

    def get_payment_result(self, payment_result_id: str):
        """
        This function returns payment result data given a payment ID.
        Parameters:
           - payment_id: Payment ID
        Returns:
           - payment_intent: Payment intent data
        """
        try:
            stripe.api_key = self.pay_key

            # Get payment result details from Stripe
            payment_result = stripe.PaymentIntent.retrieve(payment_result_id)
            user_id = payment_result.metadata.get('user_id', 'N/A')  # Get user ID
            amount = payment_result.amount  # Get payment amount
            amount_received = payment_result.amount_received  # Get received payment amount
            client_secret = payment_result.client_secret  # Get client secret
            currency = payment_result.currency  # Get currency
            status = payment_result.status  # Get payment status
            created = payment_result.created  # Get creation time (Unix timestamp, needs conversion)
            payment_types = payment_result.payment_method_types[0] if payment_result.payment_method_types else 'N/A'

            # Raise exception if no user ID
            if user_id == 'N/A':
                raise Exception("Invalid payment result without user_id")

            # Raise exception if no payment method
            if payment_types == 'N/A':
                raise Exception("Invalid payment result without payment_method_types")

        except Exception as e:
            self.api_logger.error(f"Request to Stripe API failed get_payment_result : {e}")
            return None

        # Save data to MongoDB database
        self.collection_result.insert_one(payment_result)

        return {
            "user_id": user_id,
            "amount": amount,
            "amount_received": amount_received,
            "client_secret": client_secret,
            "currency": currency,
            "status": status,
            "created": created,
            "payment_types": payment_types
        }


class AirwallexAPI:
    def __init__(self):
        """
        Initialize Airwallex API client, load environment variables, connect to MongoDB database,
        set base URL and configure logger
        """
        load_dotenv()

        # Load Airwallex environment variables
        self.client_id = os.getenv("AIRWALLEX_CLIENT_ID")
        self.api_key = os.getenv("AIRWALLEX_API_KEY")

        # Connect to MongoDB and configure collections
        mongo_uri = os.getenv('MONGO_DB_CLOUD')  # Database connection URI
        client = MongoClient(mongo_uri)  # Connect to MongoDB
        db = client['external_api']  # Select database
        self.collection_intent = db['airwallex_intent']  # Collection for payment intent data
        self.collection_result = db['airwallex_result']  # Collection for payment result data

        self.token = None
        self.expires_at = None  # Store token expiration time

        # Base URL configuration (Switch between Demo and Production)
        self.base_url = "https://api.airwallex.com"  # Production API URL
        # self.base_url = "https://api-demo.airwallex.com"  # Demo API URL (for testing)
        self.auth_url = f"{self.base_url}/api/v1/authentication/login"  # URL for login and token retrieval
        self.create_url = f"{self.base_url}/api/v1/pa/payment_intents/create"  # URL for creating payment intent
        self.result_url = f"{self.base_url}/api/v1/pa/payment_intents"  # Base URL for payment results

        # Configure logger
        logging.basicConfig(filename='logs/api.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.api_logger = logging.getLogger('api_logger')

        # Import input processing module
        self.input_processing = InputProcessing()

    def get_access_token(self) -> str or None:
        """
        Get access token using client_id and api_key for Airwallex API

        Returns:
        - token: Returns token if successful, None otherwise
        """
        if self.token and self.expires_at and self.input_processing.is_expires(self.expires_at):
            return self.token

        try:
            # ######################### Send Request ##################
            # Set request headers
            headers = {
                'x-client-id': self.client_id,
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }

            # Send POST request to get access token
            response = requests.post(self.auth_url, headers=headers, json={})

        # ######################### Exception Handling ######################

        except Exception as e:
            self.api_logger.error(f"Exception while fetching access token: {e}")
            return None

        # ######################### Process Response ##################

        # Check if request was successful
        if response.status_code in [200, 201]:
            response_data = response.json()  # Parse response to get token
            self.token = response_data.get('token')
            self.expires_at = self.input_processing.get_airwallex_token_expires()  # Token valid for 30 minutes
            return self.token
        else:
            self.api_logger.error(f"Failed to get access token: {response.status_code} {response.text}")
            return None

    def get_client_secret(self, user_id: str, amount: int, currency: str) -> str or None:
        """
        Create payment intent and return client_secret
        Use user ID, amount, and currency type to create payment intent and return client_secret for frontend payment processing
        Parameters:
            - user_id: Unique identifier for the user
            - amount: Payment amount (in smallest currency unit, e.g., 1000 means $10.00)
            - currency: Currency type, e.g., USD, CNY
        Returns:
            - client_secret: Returns payment intent's client_secret if successful, None otherwise
        """
        try:
            # ######################### Send Request ##################

            # Get access token
            token = self.get_access_token()
            if not token:
                raise Exception("Failed to retrieve access token")

            # Set request headers including Bearer token
            headers = {
                'Authorization': f"Bearer {token}",
                'Content-Type': 'application/json'
            }

            # Prepare request payload
            payload = {
                "amount": float(amount) / 100,  # Payment amount, smallest unit, automatically divided by 100 and converted to float
                "currency": currency,  # Currency type
                "request_id": self.input_processing.get_airwallex_request_id(user_id),  # Request ID to identify each payment request
                "merchant_order_id": user_id  # Merchant order ID to identify the payment request order
            }

            # Send POST request to create payment intent
            response = requests.post(self.create_url, headers=headers, json=payload)

        # ######################### Exception Handling ######################

        except Exception as e:
            self.api_logger.error(f"Exception while creating payment intent: {e}")
            return None

        # ######################### Process Response ##################

        # Check if request was successful and return result
        if response.status_code in [200, 201]:
            payment_intent = response.json()
            # Optional: Save payment intent to MongoDB
            # self.collection_intent.insert
