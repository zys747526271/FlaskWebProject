from datetime import datetime
from sqlalchemy import Enum
from . import db


class Balance(db.Model):
    __tablename__ = 'balances'

    id = db.Column(db.Integer, primary_key=True, comment='余额ID')
    amount = db.Column(db.Float, default=0.0, nullable=False, comment='可用余额')
    frozen_amount = db.Column(db.Float, default=0.0, nullable=False, comment='冻结金额')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True,
                        comment='用户ID')

    # 关系
    transactions = db.relationship('Transaction', backref='balance', lazy='dynamic', cascade='all, delete-orphan')

    def deposit(self, amount, description='充值'):
        """充值"""
        if amount <= 0:
            raise ValueError('充值金额必须大于0')
        self.amount += amount
        transaction = Transaction(balance_id=self.id, amount=amount, type='充值', description=description)
        db.session.add(self)
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def withdraw(self, amount, description='提现'):
        """提现"""
        if amount <= 0:
            raise ValueError('提现金额必须大于0')
        if amount > self.amount:
            raise ValueError('可用余额不足')
        self.amount -= amount
        transaction = Transaction(balance_id=self.id, amount=-amount, type='提现', description=description)
        db.session.add(self)
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def pay(self, amount, order_no, description='支付订单'):
        """支付"""
        if amount <= 0:
            raise ValueError('支付金额必须大于0')
        if amount > self.amount:
            raise ValueError('可用余额不足')
        self.amount -= amount
        transaction = Transaction(balance_id=self.id, amount=-amount, type='支付',
                                  description=f'{description}: {order_no}')
        db.session.add(self)
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def refund(self, amount, order_no, description='订单退款'):
        """退款"""
        if amount <= 0:
            raise ValueError('退款金额必须大于0')
        self.amount += amount
        transaction = Transaction(balance_id=self.id, amount=amount, type='退款',
                                  description=f'{description}: {order_no}')
        db.session.add(self)
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def freeze(self, amount, description='冻结金额'):
        """冻结余额"""
        if amount <= 0:
            raise ValueError('冻结金额必须大于0')
        if amount > self.amount:
            raise ValueError('可用余额不足')
        self.amount -= amount
        self.frozen_amount += amount
        transaction = Transaction(balance_id=self.id, amount=-amount, type='冻结', description=description)
        db.session.add(self)
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def unfreeze(self, amount, description='解冻金额'):
        """解冻余额"""
        if amount <= 0:
            raise ValueError('解冻金额必须大于0')
        if amount > self.frozen_amount:
            raise ValueError('冻结余额不足')
        self.frozen_amount -= amount
        self.amount += amount
        transaction = Transaction(balance_id=self.id, amount=amount, type='解冻', description=description)
        db.session.add(self)
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def to_dict(self, with_transactions=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'frozen_amount': self.frozen_amount,
            'updated_at': self.updated_at.isoformat()
        }
        if with_transactions:
            data['transactions'] = [t.to_dict() for t in
                                    self.transactions.order_by(Transaction.created_at.desc()).limit(10)]
        return data

    def __repr__(self):
        return f'<Balance {self.user_id}: {self.amount}元>'


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True, comment='交易ID')
    amount = db.Column(db.Float, nullable=False, comment='交易金额(正为收入，负为支出)')
    type = db.Column(Enum('充值', '提现', '支付', '退款', '冻结', '解冻'), nullable=False, comment='交易类型')
    description = db.Column(db.String(255), nullable=True, comment='交易描述，最多255字符')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    # 外键
    balance_id = db.Column(db.Integer, db.ForeignKey('balances.id'), nullable=False, index=True, comment='余额ID')

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'type': self.type,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'balance_id': self.balance_id
        }

    def __repr__(self):
        return f'<Transaction {self.id}: {self.type} {self.amount}元>'