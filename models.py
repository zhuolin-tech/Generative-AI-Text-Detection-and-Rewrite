from sqlalchemy import Column, Integer, String, DateTime, Text, DECIMAL, Index
from sqlalchemy.orm import declarative_base

# ############ Define Database Models ####################################################

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    user_id = Column(String(255), primary_key=True, comment='Primary key user ID, unique identifier for user')
    user_name = Column(String(255), nullable=False, comment='Username')
    user_email = Column(String(255), nullable=False, unique=True, comment='User email address')
    password_hash = Column(String(255), nullable=False, comment='Password hash value')
    created_at = Column(DateTime, nullable=False, comment='Creation time')
    updated_at = Column(DateTime, nullable=False, comment='Update time')

    __table_args__ = (
        Index('ix_user_user_id', 'user_id'),
        Index('ix_user_user_email', 'user_email'),
    )

    def __repr__(self):
        return f"<User(user_name='{self.user_name}', user_email='{self.user_email}')>"

class HumanizedHistory(Base):
    __tablename__ = 'humanized_history'
    humanized_id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto-increment primary key ID')
    user_id = Column(String(255), nullable=False, comment='User ID who uploaded')
    time = Column(DateTime, nullable=False, comment='Upload time')
    origin_text = Column(Text, nullable=False, comment='Original text')
    after_json = Column(Text, nullable=False, comment='Processed text')
    humanized_words = Column(Integer, nullable=False, comment='Text length')
    humanized_type = Column(String(255), nullable=False, comment='Processing type (free, paid, gifted)')

    __table_args__ = (
        Index('ix_humanized_history_user_id', 'user_id'),
        Index('ix_humanized_history_time', 'time'),
    )

    def __repr__(self):
        return f"<HumanizedHistory(user_id='{self.user_id}', time='{self.time}')>"

class CheckHistory(Base):
    __tablename__ = 'check_history'
    check_id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto-increment primary key ID')
    user_id = Column(String(255), nullable=False, comment='User ID who uploaded')
    time = Column(DateTime, nullable=False, comment='Upload time')
    origin_text = Column(Text, nullable=False, comment='Original text')
    after_json = Column(Text, nullable=False, comment='Returned JSON')
    check_words = Column(Integer, nullable=False, comment='Text length')
    check_type = Column(String(255), nullable=False, comment='Processing type (free, paid, gifted)')

    __table_args__ = (
        Index('ix_check_history_user_id', 'user_id'),
        Index('ix_check_history_time', 'time'),
    )

    def __repr__(self):
        return f"<CheckHistory(user_id='{self.user_id}', time='{self.time}')>"

class RechargeHistory(Base):
    __tablename__ = 'recharge_history'
    recharge_id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto-increment primary key ID')
    user_id = Column(String(255), nullable=False, comment='User ID who recharged')
    time = Column(DateTime, nullable=False, comment='Recharge time')
    amount = Column(DECIMAL(10, 2), nullable=False, comment='Recharge amount')
    currency = Column(String(255), nullable=False, comment='Currency type')
    recharge_credit = Column(DECIMAL(10, 2), nullable=False, comment='Credit points received')
    recharge_type = Column(String(255), nullable=False, comment='Recharge type (free gift, paid)')

    __table_args__ = (
        Index('ix_recharge_history_user_id', 'user_id'),
        Index('ix_recharge_history_time', 'time'),
    )

    def __repr__(self):
        return f"<RechargeHistory(user_id='{self.user_id}', time='{self.time}', amount={self.amount})>"

class SpendHistory(Base):
    __tablename__ = 'spend_history'
    spend_id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto-increment primary key ID')
    user_id = Column(String(255), nullable=False, comment='User ID who spent')
    time = Column(DateTime, nullable=False, comment='Spending time')
    spend_credit = Column(DECIMAL(10, 2), nullable=False, comment='Credit points spent')
    spend_type = Column(String(255), nullable=False, comment='Spending type (AI rewrite, AI detection)')

    __table_args__ = (
        Index('ix_spend_history_user_id', 'user_id'),
        Index('ix_spend_history_time', 'time'),
    )

    def __repr__(self):
        return f"<SpendHistory(user_id='{self.user_id}', time='{self.time}', spend_credit={self.spend_credit})>"

class ApiHistory(Base):
    __tablename__ = 'api_history'
    usage_id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto-increment primary key ID')
    user_id = Column(String(255), nullable=False, comment='User ID')
    time = Column(DateTime, nullable=False, comment='Usage time')
    usage_type = Column(String(255), nullable=False, comment='Usage type (AI rewrite, AI detection)')
    spend_words = Column(DECIMAL(10, 2), nullable=False, comment='Number of words consumed')
    balance_api = Column(DECIMAL(10, 2), nullable=False, comment='Current remaining balance in system')

    __table_args__ = (
        Index('ix_api_history_user_id', 'user_id'),
        Index('ix_api_history_time', 'time'),
    )

    def __repr__(self):
        return f"<ApiHistory(user_id='{self.user_id}', time='{self.time}', spend_words={self.spend_words})>"


class PaymentIntent(Base):
    __tablename__ = 'payment_intent'
    payment_intent_id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto-increment primary key ID')
    user_id = Column(String(255), nullable=False, comment='User ID')
    amount = Column(Integer, nullable=False, comment='Payment amount (in cents)')
    currency = Column(String(255), nullable=False, comment='Currency type')
    client_secret = Column(String(1000), nullable=False, comment='Generated payment intent client secret')
    time = Column(DateTime, nullable=False, comment='Generation time')

    __table_args__ = (
        Index('ix_payment_intent_user_id', 'user_id'),
        Index('ix_payment_intent_time', 'time'),
        Index('ix_client_secret', 'client_secret', unique=True),
    )

    def __repr__(self):
        return f"<PaymentIntent(user_id='{self.user_id}', amount={self.amount}, currency='{self.currency}')>"

class PaymentResult(Base):
    __tablename__ = 'payment_result'
    payment_result_id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto-increment primary key ID')
    result_id = Column(String(255), nullable=False, comment='Returned payment result ID')
    user_id = Column(String(255), nullable=False, comment='User ID')
    amount = Column(Integer, nullable=False, comment='Payment amount (in cents)')
    amount_received = Column(Integer, nullable=False, comment='Received payment amount (in cents)')
    client_secret = Column(String(1000), nullable=False, comment='Generated payment intent client secret')
    currency = Column(String(255), nullable=False, comment='Currency type')
    status = Column(String(255), nullable=False, comment='Payment status')
    created = Column(Integer, nullable=False, comment='Creation time as UNIX timestamp')
    created_time = Column(DateTime, nullable=False, comment='Creation time converted from UNIX timestamp')
    time = Column(DateTime, nullable=False, comment='API response time')
    payment_types = Column(String(255), nullable=False, comment='Payment method')

    __table_args__ = (
        Index('ix_payment_result_user_id', 'user_id'),
        Index('ix_payment_result_id', 'result_id', unique=True),
        Index('ix_payment_result_time', 'time'),
    )

    def __repr__(self):
        return f"<PaymentResult(user_id='{self.user_id}', amount={self.amount}, status='{self.status}')>"

class ReferCode(Base):
    __tablename__ = 'refer_code'
    refer_code_id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto-increment primary key ID')
    refer_from_user_id = Column(String(255), nullable=False, comment='Referrer user ID')
    refer_user_type = Column(String(255), nullable=False, comment='Referrer type (regular user, sales personnel, etc.)')
    refer_code = Column(String(255), nullable=False, comment='Referral code')
    created_at = Column(DateTime, nullable=False, comment='Referral code creation time')

    __table_args__ = (
        Index('ix_refer_code_from_user_id', 'refer_from_user_id', unique=True),
        Index('ix_refer_code_code', 'refer_code', unique=True),
    )

    def __repr__(self):
        return f"<ReferCode(refer_from_user_id='{self.refer_from_user_id}', refer_code='{self.refer_code}')>"

class ReferHistory(Base):
    __tablename__ = 'refer_history'
    refer_history_id = Column(Integer, primary_key=True, autoincrement=True, comment='Auto-increment primary key ID')
    refer_from_user_id = Column(String(255), nullable=False, comment='Referrer user ID')
    refer_to_user_id = Column(String(255), nullable=False, comment='Referred user ID')
    refer_code = Column(String(255), nullable=False, comment='Used referral code')
    refer_time = Column(DateTime, nullable=False, comment='Referral code usage time')
    recharge_credit = Column(DECIMAL(10, 2), nullable=False, comment='Credited points')

    __table_args__ = (
        Index('ix_refer_history_to_user_id', 'refer_to_user_id', unique=True),
        Index('ix_refer_history_from_user_id', 'refer_from_user_id'),
        Index('ix_refer_history_code', 'refer_code'),
    )

    def __repr__(self):
        return f"<ReferHistory(refer_from_user_id='{self.refer_from_user_id}', refer_to_user_id='{self.refer_to_user_id}', refer_code='{self.refer_code}')>"
