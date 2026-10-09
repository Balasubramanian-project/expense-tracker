from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models import db
from models.expense import Expense
from routes.auth import login_required

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/expenses', methods=['GET'])
@login_required
def index():
    user_id = g.user.id
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    payment_filter = request.args.get('payment_method', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    sort_by = request.args.get('sort_by', 'date_desc').strip()

    query = Expense.query.filter_by(user_id=user_id)

    if search_query:
        query = query.filter(Expense.title.ilike(f'%{search_query}%'))

    if category_filter:
        query = query.filter(Expense.category == category_filter)

    if payment_filter:
        query = query.filter(Expense.payment_method == payment_filter)

    if start_date:
        try:
            s_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expense.expense_date >= s_dt)
        except ValueError:
            pass

    if end_date:
        try:
            e_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expense.expense_date <= e_dt)
        except ValueError:
            pass

    # Sorting logic
    if sort_by == 'amount_asc':
        query = query.order_by(Expense.amount.asc())
    elif sort_by == 'amount_desc':
        query = query.order_by(Expense.amount.desc())
    elif sort_by == 'date_asc':
        query = query.order_by(Expense.expense_date.asc(), Expense.id.asc())
    else:  # default 'date_desc'
        query = query.order_by(Expense.expense_date.desc(), Expense.id.desc())

    expense_records = query.all()
    total_filtered_expense = sum(float(exp.amount) for exp in expense_records)

    return render_template(
        'expenses.html',
        expense_records=expense_records,
        categories=Expense.CATEGORIES,
        payment_methods=Expense.PAYMENT_METHODS,
        total_expense=total_filtered_expense,
        search_query=search_query,
        selected_category=category_filter,
        selected_payment=payment_filter,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by
    )

@expenses_bp.route('/expenses/add', methods=['POST'])
@login_required
def add():
    title = request.form.get('title', '').strip()
    amount_str = request.form.get('amount', '').strip()
    category = request.form.get('category', '').strip()
    payment_method = request.form.get('payment_method', '').strip()
    expense_date_str = request.form.get('expense_date', '').strip()
    description = request.form.get('description', '').strip()

    if not title or not amount_str or not category or not payment_method or not expense_date_str:
        flash('Title, amount, category, payment method, and date are required.', 'danger')
        return redirect(url_for('expenses.index'))

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Expense amount must be greater than zero.', 'danger')
            return redirect(url_for('expenses.index'))
    except ValueError:
        flash('Invalid amount entered.', 'danger')
        return redirect(url_for('expenses.index'))

    try:
        expense_date = datetime.strptime(expense_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
        return redirect(url_for('expenses.index'))

    new_expense = Expense(
        user_id=g.user.id,
        title=title,
        amount=amount,
        category=category,
        payment_method=payment_method,
        expense_date=expense_date,
        description=description
    )

    try:
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense record added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Database error while adding expense.', 'danger')

    return redirect(url_for('expenses.index'))

@expenses_bp.route('/expenses/edit/<int:expense_id>', methods=['POST'])
@login_required
def edit(expense_id):
    expense_record = Expense.query.filter_by(id=expense_id, user_id=g.user.id).first_or_404()

    title = request.form.get('title', '').strip()
    amount_str = request.form.get('amount', '').strip()
    category = request.form.get('category', '').strip()
    payment_method = request.form.get('payment_method', '').strip()
    expense_date_str = request.form.get('expense_date', '').strip()
    description = request.form.get('description', '').strip()

    if not title or not amount_str or not category or not payment_method or not expense_date_str:
        flash('Title, amount, category, payment method, and date are required.', 'danger')
        return redirect(url_for('expenses.index'))

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Expense amount must be greater than zero.', 'danger')
            return redirect(url_for('expenses.index'))
    except ValueError:
        flash('Invalid amount entered.', 'danger')
        return redirect(url_for('expenses.index'))

    try:
        expense_date = datetime.strptime(expense_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
        return redirect(url_for('expenses.index'))

    expense_record.title = title
    expense_record.amount = amount
    expense_record.category = category
    expense_record.payment_method = payment_method
    expense_record.expense_date = expense_date
    expense_record.description = description

    try:
        db.session.commit()
        flash('Expense record updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Database error while updating expense.', 'danger')

    return redirect(url_for('expenses.index'))

@expenses_bp.route('/expenses/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete(expense_id):
    expense_record = Expense.query.filter_by(id=expense_id, user_id=g.user.id).first_or_404()

    try:
        db.session.delete(expense_record)
        db.session.commit()
        flash('Expense record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Database error while deleting expense.', 'danger')

    return redirect(url_for('expenses.index'))
