from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from toolkit import LoggerManager
import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_
from datetime import datetime
from models import Base, HumanizedHistory, CheckHistory, SpendHistory, RechargeHistory, ApiHistory
import os
from dotenv import load_dotenv


class MainForm:
    def __init__(self):

        # Load .env file
        load_dotenv()
        # Read environment variables
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

    # ############ History tables - only allow query and insert operations, no delete or update ####################################################
    def add_humanized_history(self, session: Session, user_id: str, time: datetime, origin_text: str,
                              after_json: str, humanized_words: int, humanized_type: str) -> bool:
        """
        Write a record to the humanized_history table.
        Input:
          - session: SQLAlchemy Session object for database operations.
          - user_id: string, uploading user ID.
          - time: datetime object, upload time.
          - origin_text: string, original text.
          - after_text: string, processed text.
          - humanized_words: integer, text length.
          - humanized_type: string, processing type (free, paid, gifted).
        Output:
          - boolean, indicates whether the operation was successful.
        """
        try:
            new_record = HumanizedHistory(
                user_id=user_id,
                time=time,
                origin_text=origin_text,
                after_json=after_json,
                humanized_words=humanized_words,
                humanized_type=humanized_type
            )
            session.add(new_record)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"add_humanized_history error: {e}")
            return False

    def add_check_history(self, session: Session, user_id: str, time: datetime, origin_text: str, after_json: str,
                          check_words: int, check_type: str) -> bool:
        """
        Write a record to the check_history table.
        Input:
          - session: SQLAlchemy Session object for database operations.
          - user_id: string, uploading user ID.
          - time: datetime object, upload time.
          - origin_text: string, original text.
          - after_json: string, returned JSON.
          - check_words: integer, text length.
          - check_type: string, processing type (free, paid, gifted).
        Output:
          - boolean, indicates whether the operation was successful.
        """
        try:
            new_record = CheckHistory(
                user_id=user_id,
                time=time,
                origin_text=origin_text,
                after_json=after_json,
                check_words=check_words,
                check_type=check_type
            )
            session.add(new_record)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"add_check_history error: {e}")
            return False

    def add_spend_history(self, session: Session, user_id: str, time: datetime, spend_credit: float,
                          spend_type: str) -> bool:
        """
        Write a record to the spend_history table.
        Input:
          - session: SQLAlchemy Session object for database operations.
          - user_id: string, consuming user ID.
          - time: datetime object, consumption time.
          - spend_credit: float, consumed Credits.
          - spend_type: string, consumption type (check AI, detect AI).
        Output:
          - boolean, indicates whether the operation was successful.
        """
        try:
            new_record = SpendHistory(
                user_id=user_id,
                time=time,
                spend_credit=spend_credit,
                spend_type=spend_type
            )
            session.add(new_record)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"add_spend_history error: {e}")
            return False

    def add_recharge_history(self, session: Session, user_id: str, time: datetime, amount: float,
                             currency: str, recharge_credit: float, recharge_type: str) -> bool:
        """
        Write a record to the recharge_history table.
        Input:
          - session: SQLAlchemy Session object for database operations.
          - user_id: string, recharging user ID.
          - recharge_time: datetime object, recharge time.
          - amount: float, recharge amount.
          - currency: string, currency type (USD, CNY).
          - recharge_credit: float, Credits received.
          - recharge_type: string, recharge type (free gift, paid).
        Output:
          - boolean, indicates whether the operation was successful.
        """
        try:
            new_record = RechargeHistory(
                user_id=user_id,
                time=time,
                amount=amount,
                currency=currency,
                recharge_credit=recharge_credit,
                recharge_type=recharge_type
            )
            session.add(new_record)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"add_recharge_history error: {e}")
            return False

    def add_api_history(self, session: Session, user_id: str, time: datetime, usage_type: str, spend_words: float,
                        balance_api: float) -> bool:
        """
        Write a record to the api_history table.
        Input:
          - session: SQLAlchemy Session object for database operations.
          - user_id: string, using user ID.
          - time: datetime object, usage time.
          - usage_type: string, consumption type (check AI, detect AI).
          - spend_words: float, amount consumed.
          - balance_api: float, current remaining balance in the system.
        Output:
          - boolean, indicates whether the operation was successful.
        """
        try:
            new_record = ApiHistory(
                user_id=user_id,
                time=time,
                usage_type=usage_type,
                spend_words=spend_words,
                balance_api=balance_api
            )
            session.add(new_record)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"add_api_history error: {e}")
            return False

    def get_balance(self, user_id: str) -> float:
        """
        Read spend_history and recharge_history tables to check if balance is sufficient.
        Input:
          - user_id: string, user ID.
        Output:
          - float, indicates the balance
        """
        try:
            session = self.Session()
            spend_total = session.query(func.sum(SpendHistory.spend_credit)).filter_by(user_id=user_id).scalar() or 0
            recharge_total = session.query(func.sum(RechargeHistory.recharge_credit)).filter_by(user_id=user_id).scalar() or 0
            session.close()
            return recharge_total - spend_total  # Balance is recharge minus consumption
        except Exception as e:
            self.forms_logger.error(f"check_balance error: {e}")
            return False

    def get_history(self, user_id: str, history_type: str) -> list or None:
        """
        Read various history table records for the corresponding user_id, including recharge, consumption, and API usage.
        Input:
          - user_id: string, user ID.
          - history_type: string, record type (RechargeHistory, SpendHistory, ApiHistory).
        Output:
          - list, containing all matching records; returns empty list if none exist.
        """
        try:
            session = self.Session()

            history_map = {
                'spend_history': SpendHistory,
                'recharge_history': RechargeHistory,
                'api_history': ApiHistory
            }

            # Add a map here to map history_type to corresponding model
            result = session.query(history_map.get(history_type)).filter_by(user_id=user_id).all()

            session.close()
            return result if result else []  # Return empty list if none exist, otherwise return list object
        except Exception as e:
            self.forms_logger.error(f"get_history error: {e}")
            return []


    def get_history_with_spend(self, user_id: str, history_type: str):
        """
        Read CheckHistory or HumanizedHistory table records for the corresponding user_id, and add corresponding spend_credit and spend_id fields.
        Input:
          - user_id: string, user ID.
          - history_type: string (HumanizedHistory, CheckHistory)
        Output:
          - list, containing all matching records; returns empty list if none exist.
        """
        try:
            session = self.Session()

            history_map = {
                'humanized_history': HumanizedHistory,
                'check_history': CheckHistory
            }
            # Add a map here to map history_type to corresponding model
            model = history_map.get(history_type)

            # Add spend_credit and spend_id fields to query results
            result = (
                session.query(model, SpendHistory.spend_id, SpendHistory.spend_credit)
                .outerjoin(SpendHistory, and_(     # Join condition is check_time equals spend_time, so can join directly
                    model.user_id == SpendHistory.user_id,
                    model.time == SpendHistory.time
                ))
                .filter(model.user_id == user_id)
                # TODO Why is there a warning?
                .all()
            )

            session.close()
            return result if result else []  # Return empty list if none exist, otherwise return list object
        except Exception as e:
            self.forms_logger.error(f"get_history error: {e}")
            print(f"get_history error: {e}")
            return []
