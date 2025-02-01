import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from toolkit import LoggerManager
import logging
from datetime import datetime
from models import Base, ReferHistory, ReferCode
from sqlalchemy.orm import Session
from dotenv import load_dotenv

class ReferForm:
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

    def get_refer_code_by_user_id(self, user_id: str) -> str:
        """
        Query the refer_code table by user_id and return the corresponding refer_code.
        Input:
          - user_id: string, user ID.
        Output:
          - string, user's referral code (if exists).
        """
        try:
            session = self.Session()
            refer_code = session.query(ReferCode).filter_by(refer_from_user_id=user_id).first()
            session.close()
            if refer_code:
                return refer_code.refer_code
            else:
                return None
        except Exception as e:
            self.forms_logger.error(f"get_refer_code_by_user_id error: {e}")
            return None

    def get_user_id_by_refer_code(self, refer_code: str) -> str or None:
        """
        Query the corresponding user_id by refer_code.
        Input:
          - refer_code: string, referral code.
        Output:
          - Returns the corresponding user_id (string) if exists, otherwise returns None.
        """
        try:
            session = self.Session()
            # Query ReferCode table where refer_code equals the input referral code
            refer_code_record = session.query(ReferCode).filter_by(refer_code=refer_code).first()
            session.close()

            # If matching referral code is found, return user_id
            if refer_code_record:
                return refer_code_record.refer_from_user_id
            else:
                return None
        except Exception as e:
            self.forms_logger.error(f"Error fetching user_id for refer_code {refer_code}: {e}")
            return None

    def create_new_refer_code(self, session: Session, user_id: str, refer_code: str, user_type: str,
                              created_at: datetime) -> bool:
        """
        Write a new refer_code.
        Input:
          - user_id: string, user ID.
          - refer_code: string, referral code to be generated.
          - user_type: string, user type (regular user or sales personnel).
          - created_at: datetime object, creation time.
        Output:
          - boolean, indicates whether the operation was successful.
        """
        try:
            new_refer_code = ReferCode(
                refer_from_user_id=user_id,
                refer_user_type=user_type,
                refer_code=refer_code,
                created_at=created_at
            )
            session.add(new_refer_code)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"create_new_refer_code error: {e}")
            session.rollback()
            return False

    def check_refer_history_exists(self, user_id: str) -> bool:
        """
        Check if there is a usage record for the specified user in refer_history, i.e., check if it's the first use.
        Input:
          - user_id: string, ID of the user using the referral code.
        Output:
          - boolean, indicates whether the record exists (returns True if used before, False if never used).
        """
        try:
            session = self.Session()
            history_record = session.query(ReferHistory).filter_by(refer_to_user_id=user_id).first()
            session.close()

            if history_record:  # Return True if record is found, otherwise return False
                return True
            else:
                return False
        except Exception as e:
            self.forms_logger.error(f"check_refer_history_exists error: {e}")
            return False

    def get_refer_history_by_user_id(self, user_id: str) -> list:
        """
        Query refer_history usage records by user_id.
        Input:
          - user_id: string, user ID.
        Output:
          - list, containing the user's referral usage records.
        """
        try:
            session = self.Session()
            history_records = session.query(ReferHistory).filter_by(refer_from_user_id=user_id).all()
            session.close()
            return history_records if history_records else []  # Return empty list if none exist, otherwise return list object
        except Exception as e:
            self.forms_logger.error(f"get_refer_history_by_user_id error: {e}")
            return []

    def create_new_refer_history(self, session: Session, from_user_id: str, to_user_id: str, refer_code: str,
                                 refer_time: datetime, recharge_credit: float) -> bool:
        """
        Write a new refer_history record.
        Input:
          - from_user_id: string, referrer's user ID.
          - to_user_id: string, referred user's ID.
          - refer_code: string, referral code used.
          - refer_time: datetime object, time when referral code was used.
          - recharge_credit: float, credits recharged.
        Output:
          - boolean, indicates whether the operation was successful.
        """
        try:
            new_refer_history = ReferHistory(
                refer_from_user_id=from_user_id,
                refer_to_user_id=to_user_id,
                refer_code=refer_code,
                refer_time=refer_time,
                recharge_credit=recharge_credit
            )
            session.add(new_refer_history)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"create_new_refer_history error: {e}")
            session.rollback()
            return False
