from datetime import datetime
from models import db

class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, default='Overall')
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    budget_month = db.Column(db.String(7), nullable=False)  # Format: 'YYYY-MM'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', 'budget_month', name='unique_user_cat_month'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'amount': float(self.amount),
            'budget_month': self.budget_month,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<Budget {self.category} ({self.budget_month}): {self.amount}>'
