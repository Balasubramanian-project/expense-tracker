from datetime import datetime
from models import db

class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    payment_method = db.Column(db.String(50), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    CATEGORIES = [
        'Food', 'Transportation', 'Education', 'Shopping',
        'Healthcare', 'Entertainment', 'Bills and Utilities',
        'Rent', 'Travel', 'Other'
    ]

    PAYMENT_METHODS = [
        'Cash', 'UPI', 'Debit Card', 'Credit Card', 'Bank Transfer'
    ]

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'amount': float(self.amount),
            'category': self.category,
            'payment_method': self.payment_method,
            'expense_date': self.expense_date.strftime('%Y-%m-%d') if self.expense_date else None,
            'description': self.description or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<Expense {self.title}: {self.amount}>'
