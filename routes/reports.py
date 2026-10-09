import csv
import io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, Response, jsonify, g
from sqlalchemy import func
from models import db
from models.income import Income
from models.expense import Expense
from routes.auth import login_required

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def index():
    user_id = g.user.id
    now = datetime.utcnow().date()

    period = request.args.get('period', 'monthly')  # daily, weekly, monthly, yearly, custom
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    if period == 'daily':
        start_date = now
        end_date = now
    elif period == 'weekly':
        start_date = now - timedelta(days=now.weekday())
        end_date = now
    elif period == 'yearly':
        start_date = now.replace(month=1, day=1)
        end_date = now
    elif period == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = now.replace(day=1)
            end_date = now
    else:  # default monthly
        period = 'monthly'
        start_date = now.replace(day=1)
        end_date = now

    # Queries
    income_sum = db.session.query(func.coalesce(func.sum(Income.amount), 0))\
        .filter(Income.user_id == user_id, Income.income_date >= start_date, Income.income_date <= end_date).scalar()
    
    expense_sum = db.session.query(func.coalesce(func.sum(Expense.amount), 0))\
        .filter(Expense.user_id == user_id, Expense.expense_date >= start_date, Expense.expense_date <= end_date).scalar()

    total_income = float(income_sum)
    total_expenses = float(expense_sum)
    period_savings = total_income - total_expenses

    # Days count for avg daily calculation
    days_count = max((end_date - start_date).days + 1, 1)
    avg_daily_spending = total_expenses / days_count

    # Highest spending category
    highest_cat_q = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('cat_total')
    ).filter(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).first()

    highest_spending_category = highest_cat_q[0] if highest_cat_q else 'N/A'
    highest_spending_amount = float(highest_cat_q[1]) if highest_cat_q else 0.0

    return render_template(
        'reports.html',
        period=period,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        total_income=total_income,
        total_expenses=total_expenses,
        period_savings=period_savings,
        avg_daily_spending=round(avg_daily_spending, 2),
        highest_spending_category=highest_spending_category,
        highest_spending_amount=highest_spending_amount
    )

@reports_bp.route('/api/reports/chart-data')
@login_required
def chart_data():
    user_id = g.user.id
    now = datetime.utcnow().date()

    period = request.args.get('period', 'monthly')
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    if period == 'daily':
        start_date = now
        end_date = now
    elif period == 'weekly':
        start_date = now - timedelta(days=now.weekday())
        end_date = now
    elif period == 'yearly':
        start_date = now.replace(month=1, day=1)
        end_date = now
    elif period == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = now.replace(day=1)
            end_date = now
    else:
        start_date = now.replace(day=1)
        end_date = now

    # 1. Category Pie Chart
    cat_expenses = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(Expense.category).all()

    category_labels = [c[0] for c in cat_expenses]
    category_values = [float(c[1]) for c in cat_expenses]

    # 2. Timeline Line Chart (daily timeline within date range)
    timeline_labels = []
    timeline_expenses = []
    timeline_income = []

    curr = start_date
    while curr <= end_date:
        d_str = curr.strftime('%Y-%m-%d')
        inc_val = db.session.query(func.coalesce(func.sum(Income.amount), 0))\
            .filter(Income.user_id == user_id, Income.income_date == curr).scalar()
        exp_val = db.session.query(func.coalesce(func.sum(Expense.amount), 0))\
            .filter(Expense.user_id == user_id, Expense.expense_date == curr).scalar()

        timeline_labels.append(d_str)
        timeline_income.append(float(inc_val))
        timeline_expenses.append(float(exp_val))
        curr += timedelta(days=1)

    return jsonify({
        'category_pie': {
            'labels': category_labels,
            'values': category_values
        },
        'timeline': {
            'labels': timeline_labels,
            'income': timeline_income,
            'expenses': timeline_expenses
        }
    })

@reports_bp.route('/reports/export-csv')
@login_required
def export_csv():
    user_id = g.user.id
    now = datetime.utcnow().date()
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    query_inc = Income.query.filter_by(user_id=user_id)
    query_exp = Expense.query.filter_by(user_id=user_id)

    if start_date_str:
        try:
            s_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query_inc = query_inc.filter(Income.income_date >= s_dt)
            query_exp = query_exp.filter(Expense.expense_date >= s_dt)
        except ValueError:
            pass

    if end_date_str:
        try:
            e_dt = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query_inc = query_inc.filter(Income.income_date <= e_dt)
            query_exp = query_exp.filter(Expense.expense_date <= e_dt)
        except ValueError:
            pass

    incomes = query_inc.all()
    expenses = query_exp.all()

    # Create CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Type', 'Date', 'Title / Source', 'Category', 'Payment Method', 'Amount (INR)', 'Description'])

    for inc in incomes:
        cw.writerow(['Income', inc.income_date.strftime('%Y-%m-%d'), inc.source, 'Income', 'N/A', f'{float(inc.amount):.2f}', inc.description or ''])

    for exp in expenses:
        cw.writerow(['Expense', exp.expense_date.strftime('%Y-%m-%d'), exp.title, exp.category, exp.payment_method, f'{float(exp.amount):.2f}', exp.description or ''])

    output = si.getvalue()
    filename = f"financial_report_{now.strftime('%Y%m%d')}.csv"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
