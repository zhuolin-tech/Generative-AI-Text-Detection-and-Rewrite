import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from toolkit import LoggerManager
import logging
from datetime import datetime
from models import Base, PaymentIntent, PaymentResult
from sqlalchemy.orm import Session
from dotenv import load_dotenv

class PaymentForm:
    def __init__(self):
        # Read environment variables
        # Load .env file
        load_dotenv()
        self.database_url = os.getenv("MYSQL_ALI_SINGAPORE")

        # Create database engine
        self.engine = create_engine(self.database_url, echo=False)

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)

        # Create all tables
        Base.metadata.create_all(self.engine)

        # Configure logger
        logging.basicConfig(filename='logs/forms.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.forms_logger = LoggerManager('forms_logger', 'logs/forms.log').get_logger()  # Create logger instance

    # ############ Payment table operations CRUD ####################################################

    def add_payment_intent(self, session: Session, user_id: str, amount: int, currency: str, client_secret: str, time: datetime) -> bool:
        """
        Write a new payment intent record to the payment_intent table.
        Input:
          - user_id: string, primary key ID that uniquely identifies the user.
          - amount: integer, payment amount (in cents).
          - currency: string, currency type, e.g. 'cny'.
          - client_secret: string, generated client secret for the payment intent.
          - time: datetime object, generation time.
        Output:
          - boolean, indicates whether the operation was successful.
        """
        try:
            new_payment_intent = PaymentIntent(
                user_id=user_id,
                amount=amount,
                currency=currency,
                client_secret=client_secret,
                time=time
            )
            session.add(new_payment_intent)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"add_payment_intent error: {e}")
            session.rollback()
            return False


    def add_payment_result(self, session: Session, user_id: str, result_id: str, amount: int, amount_received: int, client_secret: str,
                           currency: str, status: str, created: int, created_time: datetime, time: datetime,
                           payment_types: str) -> bool:
        """
        Write a new payment result record to the payment_result table.
        Input:
          - session: Session object, database session.
          - user_id: string, primary key ID that uniquely identifies the user.
          - result_id: string, payment result ID that uniquely identifies the payment result.
          - amount: integer, payment amount (in cents).
          - amount_received: integer, received payment amount (in cents).
          - client_secret: string, generated client secret for the payment intent.
          - currency: string, currency type, e.g. 'cny'.
          - status: string, payment status.
          - created: integer, UNIX timestamp of creation time.
          - created_time: datetime object, UNIX timestamp converted to time.
          - time: datetime object, API response time.
          - payment_types: string, payment method.
        Output:
          - boolean, indicates whether the operation was successful.
        """
        try:
            new_payment_result = PaymentResult(
                user_id=user_id,
                result_id=result_id,
                amount=amount,
                amount_received=amount_received,
                client_secret=client_secret,
                currency=currency,
                status=status,
                created=created,
                created_time=created_time,
                time=time,
                payment_types=payment_types
            )

            session.add(new_payment_result)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"add_payment_result error: {e}")
            session.rollback()
            return False

    def check_client_secret_exists(self, client_secret: str) -> bool:
        """
        Check if client_secret exists in the payment_intent table.
        Input:
          - client_secret: string, client secret of the payment intent.
        Output:
          - boolean, indicates whether it exists.
        """
        try:
            session = self.Session()
            payment_intent = session.query(PaymentIntent).filter_by(client_secret=client_secret).first()
            session.close()
            if payment_intent:
                return True
            else:
                return False
        except Exception as e:
            self.forms_logger.error(f"check_intent_client_secret error: {e}")
            return False


    def check_payment_result_id_exists(self, payment_result_id: str) -> bool:
        """
        Check if payment_result_id exists in the payment_result table.
        Input:
          - payment_result_id: string, ID of the payment result.
        Output:
          - boolean, indicates whether it exists.
        """
        try:
            session = self.Session()
            payment_result = session.query(PaymentResult).filter_by(result_id=payment_result_id).first()
            session.close()
            if payment_result:
                return True
            else:
                return False
        except Exception as e:
            self.forms_logger.error(f"check_payment_result_id error: {e}")
            return False

