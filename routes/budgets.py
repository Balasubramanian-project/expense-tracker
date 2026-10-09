from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from sqlalchemy import func
from models import db
from models.budget import Budget
from models.expense import Expense
from routes.auth import login_required

budgets_bp = Blueprint('budgets', __name__)

BUDGET_CATEGORIES = ['Overall'] + Expense.CATEGORIES

@budgets_bp.route('/budgets', methods=['GET'])
@login_required
def index():
    user_id = g.user.id
    now = datetime.utcnow()
    selected_month = request.args.get('month', now.strftime('%Y-%m')).strip()

    # Parse selected month date range
    try:
        month_start = datetime.strptime(selected_month, '%Y-%m').date()
    except ValueError:
        selected_month = now.strftime('%Y-%m')
        month_start = now.replace(day=1).date()

    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1, day=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1, day=1)
    month_end = next_month - timedelta(days=1)

    # Fetch budgets for user & month
    budget_records = Budget.query.filter_by(user_id=user_id, budget_month=selected_month).all()

    # Fetch expenses for user in this month by category
    expense_aggregates = db.session.query(
        Expense.category,
        func.coalesce(func.sum(Expense.amount), 0).label('total_spent')
    ).filter(
        Expense.user_id == user_id,
        Expense.expense_date >= month_start,
        Expense.expense_date <= month_end
    ).group_by(Expense.category).all()

    category_spent_map = {cat: float(spent) for cat, spent in expense_aggregates}
    total_monthly_spent = sum(category_spent_map.values())

    # Build rich budget item metadata list
    budget_items = []
    for b in budget_records:
        if b.category == 'Overall':
            spent = total_monthly_spent
        else:
            spent = category_spent_map.get(b.category, 0.0)

        budget_amt = float(b.amount)
        remaining = budget_amt - spent
        utilization = (spent / budget_amt * 100) if budget_amt > 0 else 0.0

        # Status: normal (<80%), warning (80%-100%), exceeded (>100%)
        if utilization > 100:
            status = 'danger'
            status_text = 'Exceeded'
        elif utilization >= 80:
            status = 'warning'
            status_text = 'Near Limit (≥80%)'
        else:
            status = 'success'
            status_text = 'On Track'

        budget_items.append({
            'id': b.id,
            'category': b.category,
            'budget_amount': budget_amt,
            'spent_amount': spent,
            'remaining_amount': remaining,
            'utilization': round(utilization, 1),
            'status': status,
            'status_text': status_text,
            'budget_month': b.budget_month
        })

    return render_template(
        'budgets.html',
        budget_items=budget_items,
        categories=BUDGET_CATEGORIES,
        selected_month=selected_month
    )

@budgets_bp.route('/budgets/set', methods=['POST'])
@login_required
def set_budget():
    category = request.form.get('category', '').strip()
    amount_str = request.form.get('amount', '').strip()
    budget_month = request.form.get('budget_month', '').strip()

    if not category or not amount_str or not budget_month:
        flash('Category, amount, and month are required.', 'danger')
        return redirect(url_for('budgets.index', month=budget_month))

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Budget amount must be greater than zero.', 'danger')
            return redirect(url_for('budgets.index', month=budget_month))
    except ValueError:
        flash('Invalid amount entered.', 'danger')
        return redirect(url_for('budgets.index', month=budget_month))

    existing = Budget.query.filter_by(
        user_id=g.user.id,
        category=category,
        budget_month=budget_month
    ).first()

    if existing:
        existing.amount = amount
        flash(f'Budget for {category} in {budget_month} updated!', 'success')
    else:
        new_b = Budget(
            user_id=g.user.id,
            category=category,
            amount=amount,
            budget_month=budget_month
        )
        db.session.add(new_b)
        flash(f'Budget for {category} in {budget_month} set successfully!', 'success')

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('Database error setting budget.', 'danger')

    return redirect(url_for('budgets.index', month=budget_month))

@budgets_bp.route('/budgets/delete/<int:budget_id>', methods=['POST'])
@login_required
def delete(budget_id):
    budget_record = Budget.query.filter_by(id=budget_id, user_id=g.user.id).first_or_404()
    month = budget_record.budget_month

    try:
        db.session.delete(budget_record)
        db.session.commit()
        flash('Budget deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Database error deleting budget.', 'danger')

    return redirect(url_for('budgets.index', month=month))
