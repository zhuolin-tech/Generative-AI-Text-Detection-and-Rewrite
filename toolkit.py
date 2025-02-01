import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.inspection import inspect
from decimal import Decimal
import json
import logging
import re
from bson import ObjectId
import random

class LoggerManager:
    def __init__(self, name: str, log_file: str, level: int = logging.INFO):
        """
        Initialize logger manager
        Parameters:
            - name (str): Name of the logger
            - log_file (str): Path to the log file
            - level (int): Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        handler = logging.FileHandler(log_file)
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def get_logger(self):
        """Get the logger instance"""
        return self.logger


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class InputProcessing:
    # Calculate word count in a string, using regex to remove punctuation
    @staticmethod
    def word_count(text: str) -> int:
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        words = text.split()  # Split into word list
        return len(words)  # Return word count

    # Calculate humanization service cost using coefficients: 1.0 for easy, 1.2 for medium, 1.5 for aggressive
    @staticmethod
    def humanized_spend(word_count: int, mode: str) -> float:

        price_rate_map = {
            'easy': 1.0,
            'medium': 1.2,
            'aggressive': 1.5
        }

        humanized_price_rate = price_rate_map.get(mode, 1.0)  # Get humanization cost coefficient
        return float(word_count) * humanized_price_rate  # Return humanization cost

    # Calculate detection service cost using coefficient 0.1
    @staticmethod
    def check_spend(word_count: int) -> float:
        check_price_rate = 0.1
        return float(word_count) * check_price_rate  # Return detection cost

    # Get current time, timezone set to Beijing time (UTC+8)
    @staticmethod
    def get_current_time():
        hour = 8
        return datetime.now(timezone(timedelta(hours=hour)))  # Return current time

    # Generate time-based UUID (UUID1), ensuring uniqueness within specific time and space
    @staticmethod
    def user_id() -> str:
        return str(uuid.uuid1())  # Return UUID1

    # Generate password hash using hashlib
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()  # Return hash value

    # Serialize database model object to JSON format
    @staticmethod
    def serialize(model_instance) -> dict:
        return {c.key: getattr(model_instance, c.key) for c in inspect(model_instance).mapper.column_attrs}  # Return serialized dictionary

    # Convert Unix timestamp to datetime object
    @staticmethod
    def convert_unix_time(unix_time: int) -> datetime:
        return datetime.fromtimestamp(unix_time)

    # Convert timezone string time to Unix timestamp
    @staticmethod
    def convert_time_unix(time: str) -> int:
        # Fix timezone format, change `+0000` to `+00:00`
        if '+' in time:
            time = time[:-2] + ':' + time[-2:]
        return int(datetime.strptime(time, '%Y-%m-%dT%H:%M:%S%z').timestamp())
    
    @staticmethod
    def convert_format_datetime(input_time_str: str) -> str:
        # Parse input string to datetime object using '%Y-%m-%dT%H:%M:%S%z' format
        return datetime.strptime(input_time_str, '%Y-%m-%dT%H:%M:%S%z')

    # Convert payment amount from cents to dollars and to float
    @staticmethod
    def convert_amount(credit: int) -> float:
        return float(credit / 100)

    @staticmethod
    def convert_result_to_dict_list(result, history_type):
        """
        Convert results to dictionary list
        Input:
          - result (list): Input result list, each element is a tuple (history, spend_id, spend_credit)
          - history_type (str): String indicating history type ('check_history' or 'humanized_history')
        Output:
          - list: Converted dictionary list
        """

        def to_dict(obj):
            """
            Convert SQLAlchemy object to dictionary
            """
            if obj is None:
                return None
            return {c.key: getattr(obj, c.key) for c in inspect(obj.__class__).columns}

        result_list = []

        for item in result:
            history, spend_id, spend_credit = item
            history_dict = to_dict(history)

            # Handle Decimal type
            if isinstance(spend_credit, Decimal):
                spend_credit = float(spend_credit)

            # Handle JSON string
            if 'after_json' in history_dict and history_dict['after_json']:
                try:
                    history_dict['after_json'] = json.loads(history_dict['after_json'])
                except (TypeError, json.JSONDecodeError) as e:
                    history_dict['after_json'] = None
                    print(f"Error parsing JSON for 'after_json': {e}")

            history_dict['spend_id'] = spend_id
            history_dict['spend_credit'] = spend_credit

            if history_type == 'check_history':
                history_dict['check_id'] = history_dict.get('check_id')
            elif history_type == 'humanized_history':
                history_dict['humanized_id'] = history_dict.get('humanized_id')

            result_list.append(history_dict)

        return result_list

    @staticmethod
    def get_amount_to_credit_map(currency: str) -> dict:
        """
        Return mapping of recharge amounts to credit points for different currency types.
        Parameters:
           - currency: Currency type, supports 'cny', 'usd', 'cad'
        Returns:
           - Mapping of recharge amounts to credit points for different currency types.
        """

        # Exchange rates reference 2024.10.19 16:50 EDT (UTC-5)
        # usd_cny_rate = 7.10  # USD/CNY
        # cny_usd_rate = 0.14  # CNY/USD
        # cad_cny_rate = 5.14  # CAD/CNY
        # cny_cad_rate = 0.19  # CNY/CAD

        # CNY mapping table (in cents)
        cny_map = {
            2900: 500,
            4900: 1000,
            9900: 2000,
            19900: 4500,
            49900: 12000,
            99900: 25000
        }

        # USD mapping table (in cents)
        usd_map = {
            400: 500,
            700: 1000,
            1400: 2000,
            2800: 4500,
            7000: 12000,
            14000: 25000
        }

        # CAD mapping table (in cents)
        cad_map = {
            700: 500,
            1240: 1000,
            2480: 2000,
            4960: 4500,
            12400: 12000,
            24800: 25000
        }

        # Return corresponding mapping table based on currency type
        if currency.lower() == 'cny':
            return cny_map
        elif currency.lower() == 'usd':
            return usd_map
        elif currency.lower() == 'cad':
            return cad_map
        else:
            # Return empty mapping if currency type is not supported
            return {}

    @staticmethod
    def get_credit(amount: int, currency: str) -> float:
        """
        Get corresponding credit points based on recharge amount.
        Parameters:
           - amount: Recharge amount (in cents)
           - currency: Currency type, default is 'usd'
        Returns:
           - Corresponding credit points, returns 0 if amount is not in mapping table.
        """
        # Get amount to credit mapping for current currency type
        amount_to_credit_map = InputProcessing.get_amount_to_credit_map(currency)

        # Return corresponding credit points based on recharge amount, default to 0
        credit = amount_to_credit_map.get(amount, 0)

        return credit

