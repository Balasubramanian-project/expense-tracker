from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, g
from sqlalchemy import func, extract
from models import db
from models.income import Income
from models.expense import Expense
from models.budget import Budget
from routes.auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_id = g.user.id
    now = datetime.utcnow()
    current_month_str = now.strftime('%Y-%m')

    # Total Lifetime Income & Expenses
    total_income_q = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(Income.user_id == user_id).scalar()
    total_expense_q = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.user_id == user_id).scalar()

    total_income = float(total_income_q)
    total_expenses = float(total_expense_q)
    current_balance = total_income - total_expenses

    # Current Month Income & Expenses
    first_day_current_month = now.replace(day=1)
    if now.month == 12:
        last_day_current_month = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day_current_month = now.replace(month=now.month + 1, day=1) - timedelta(days=1)

    monthly_income_q = db.session.query(func.coalesce(func.sum(Income.amount), 0))\
        .filter(Income.user_id == user_id, Income.income_date >= first_day_current_month, Income.income_date <= last_day_current_month).scalar()
    
    monthly_expense_q = db.session.query(func.coalesce(func.sum(Expense.amount), 0))\
        .filter(Expense.user_id == user_id, Expense.expense_date >= first_day_current_month, Expense.expense_date <= last_day_current_month).scalar()

    monthly_income = float(monthly_income_q)
    monthly_expenses = float(monthly_expense_q)
    monthly_savings = monthly_income - monthly_expenses

    # Monthly Budget for Current Month (Overall)
    overall_budget_obj = Budget.query.filter_by(user_id=user_id, category='Overall', budget_month=current_month_str).first()
    monthly_budget = float(overall_budget_obj.amount) if overall_budget_obj else 0.0

    remaining_budget = monthly_budget - monthly_expenses
    budget_utilization = (monthly_expenses / monthly_budget * 100) if monthly_budget > 0 else 0.0

    # Recent Transactions (Combined 5 latest income + expenses)
    recent_incomes = Income.query.filter_by(user_id=user_id).order_by(Income.income_date.desc(), Income.id.desc()).limit(5).all()
    recent_expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.expense_date.desc(), Expense.id.desc()).limit(5).all()

    combined = []
    for inc in recent_incomes:
        combined.append({
            'type': 'Income',
            'title': inc.source,
            'category': 'Income',
            'amount': float(inc.amount),
            'date': inc.income_date,
            'description': inc.description or ''
        })
    for exp in recent_expenses:
        combined.append({
            'type': 'Expense',
            'title': exp.title,
            'category': exp.category,
            'amount': float(exp.amount),
            'date': exp.expense_date,
            'description': exp.description or ''
        })
    
    combined.sort(key=lambda x: x['date'], reverse=True)
    recent_transactions = combined[:5]

    return render_template(
        'dashboard.html',
        total_income=total_income,
        total_expenses=total_expenses,
        current_balance=current_balance,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_savings=monthly_savings,
        monthly_budget=monthly_budget,
        remaining_budget=remaining_budget,
        budget_utilization=round(budget_utilization, 1),
        current_month_str=current_month_str,
        recent_transactions=recent_transactions
    )

@dashboard_bp.route('/api/dashboard/chart-data')
@login_required
def chart_data():
    user_id = g.user.id
    now = datetime.utcnow()
    current_month_str = now.strftime('%Y-%m')

    # Category Breakdown for Current Month Expenses
    first_day = now.replace(day=1)
    if now.month == 12:
        last_day = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = now.replace(month=now.month + 1, day=1) - timedelta(days=1)

    cat_expenses = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        Expense.expense_date >= first_day,
        Expense.expense_date <= last_day
    ).group_by(Expense.category).all()

    category_labels = [c[0] for c in cat_expenses]
    category_values = [float(c[1]) for c in cat_expenses]

    # Monthly Trend for Last 6 Months
    trend_labels = []
    trend_income = []
    trend_expenses = []

    for i in range(5, -1, -1):
        target_month_date = now - timedelta(days=i*30)
        m_str = target_month_date.strftime('%b %Y')
        month_start = target_month_date.replace(day=1)
        if target_month_date.month == 12:
            month_end = target_month_date.replace(year=target_month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = target_month_date.replace(month=target_month_date.month + 1, day=1) - timedelta(days=1)

        inc_val = db.session.query(func.coalesce(func.sum(Income.amount), 0))\
            .filter(Income.user_id == user_id, Income.income_date >= month_start, Income.income_date <= month_end).scalar()
        exp_val = db.session.query(func.coalesce(func.sum(Expense.amount), 0))\
            .filter(Expense.user_id == user_id, Expense.expense_date >= month_start, Expense.expense_date <= month_end).scalar()

        trend_labels.append(m_str)
        trend_income.append(float(inc_val))
        trend_expenses.append(float(exp_val))

    return jsonify({
        'category_chart': {
            'labels': category_labels,
            'datasets': [{'data': category_values}]
        },
        'trend_chart': {
            'labels': trend_labels,
            'income': trend_income,
            'expenses': trend_expenses
        }
    })
