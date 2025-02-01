import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from toolkit import LoggerManager
import logging
from datetime import datetime
from models import Base, User
from dotenv import load_dotenv

class UserForm:
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
        self.forms_logger = LoggerManager('models_logger', 'logs/forms.log').get_logger()  # Create logger instance

    # ############ User table CRUD operations ####################################################

    def add_user(self, user_id: str, user_name: str, user_email: str, password_hash: str,
                 issue_time: datetime) -> bool:
        """
        Add a new user record to the user table.
        Input:
          - user_id: string, primary key ID that uniquely identifies the user.
          - user_name: string, user's name.
          - user_email: string, user's email address.
          - password_hash: string, hash value of user's password.
          - issue_time: datetime object, user registration time.
        Output:
          - boolean, indicates whether the operation was successful.
        """
        session = self.Session()
        try:
            new_user = User(
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                password_hash=password_hash,
                created_at=issue_time,
                updated_at=issue_time
            )
            session.add(new_user)
            session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"add_user error: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a record from the user table.
        Input:
          - user_id: string, user's primary key ID.
        Output:
          - boolean, indicates whether the operation was successful.
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                session.delete(user)
                session.commit()
            return True
        except Exception as e:
            self.forms_logger.error(f"delete_user error: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def check_user_id_exists(self, user_id: str) -> bool:
        """
        Check if a user_id exists in the user table.
        Input:
          - user_id: string, user's primary key ID.
        Output:
          - boolean, indicates whether the user_id exists.
        """
        try:
            session = self.Session()
            result = session.query(User).filter_by(user_id=user_id).count() > 0
            session.close()
            return result  # Return boolean
        except Exception as e:
            self.forms_logger.error(f"check_user_id_exists error: {e}")
            return False

    def check_user_email_exists(self, user_email: str) -> bool:
        """
        Check if an email already exists in the user table.
        Input:
          - user_email: string, user's email address.
        Output:
          - boolean, indicates whether the email exists.
        """
        try:
            session = self.Session()
            result = session.query(User).filter_by(user_email=user_email).count() > 0
            session.close()
            return result  # Return boolean
        except Exception as e:
            self.forms_logger.error(f"check_user_email_exists error: {e}")
            return False


    # TODO I think the form functions here are too complex, they should be simpler with each function doing only one simple task, then combine them in the service layer
    def verify_user(self, user_email: str, password_hash: str) -> str or None:
        """
        Verify if the user's email and password hash match.
        Input:
          - user_email: string, user's email address.
          - password_hash: string, user's password hash.
        Output:
          - User_ID: user's unique identifier ID (if login successful) or None
        """
        session = self.Session()
        try:
            user_id = session.query(User.user_id).filter_by(user_email=user_email, password_hash=password_hash).scalar()
            return user_id
        except Exception as e:
            self.forms_logger.error(f"verify_user error: {e}")
            return None
        finally:
            session.close()

    def get_user_by_id(self, user_id: str) -> dict or None:
        """
        Read user table record by user_id.
        Input:
          - user_id: string, user's primary key ID.
        Output:
          - dictionary containing all user record information; returns None if not found.
        """
        try:
            session = self.Session()

            user = session.query(User).filter_by(user_id=user_id).first()

            session.close()

            if user:
                return {
                    "user_id": user.user_id,
                    "user_name": user.user_name,
                    "user_email": user.user_email,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                }
            return None
        except Exception as e:
            self.forms_logger.error(f"get_user_by_id error: {e}")
            return None

    def update_user(self, user_id: str, field: str, new_value: str, updated_time: datetime) -> bool:
        """
        Update a record in the user table.
        Input:
          - user_id: string, user's primary key ID.
          - field: string, field name to update (user_name, user_email, password_hash)
          - new_value: new value.
          - updated_time: datetime object, update time.
        Output:
          - boolean, indicates whether the operation was successful.
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                setattr(user, field, new_value)
                user.updated_at = updated_time
                session.commit()
                return True
            return False
        except Exception as e:
            self.forms_logger.error(f"update_user error: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def update_password_email(self, user_email: str, password_hash: str, updated_time: datetime) -> bool:
        """
        Update password in the user table based on email address.
        Input:
          - user_email: string, user's email address.
          - password: string, new password.
          - updated_time: datetime object, update time.
        Output:
          - boolean, indicates whether the operation was successful.
        """
        session = self.Session()
        try:
            user = session.query(User).filter_by(user_email=user_email).first()
            if user:
                user.password_hash = password_hash
                user.updated_at = updated_time
                session.commit()
                return True
            return False
        except Exception as e:
            self.forms_logger.error(f"update_password_email error: {e}")
            session.rollback()
            return False
        finally:
            session.close()
