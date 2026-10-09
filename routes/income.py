from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models import db
from models.income import Income
from routes.auth import login_required

income_bp = Blueprint('income', __name__)

INCOME_SOURCES = ['Salary', 'Freelancing', 'Business', 'Other']

@income_bp.route('/income', methods=['GET'])
@login_required
def index():
    user_id = g.user.id
    source_filter = request.args.get('source', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    query = Income.query.filter_by(user_id=user_id)

    if source_filter:
        query = query.filter(Income.source == source_filter)

    if start_date:
        try:
            s_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Income.income_date >= s_dt)
        except ValueError:
            pass

    if end_date:
        try:
            e_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Income.income_date <= e_dt)
        except ValueError:
            pass

    income_records = query.order_by(Income.income_date.desc(), Income.id.desc()).all()
    total_filtered_income = sum(float(inc.amount) for inc in income_records)

    return render_template(
        'income.html',
        income_records=income_records,
        sources=INCOME_SOURCES,
        total_income=total_filtered_income,
        selected_source=source_filter,
        start_date=start_date,
        end_date=end_date
    )

@income_bp.route('/income/add', methods=['POST'])
@login_required
def add():
    source = request.form.get('source', '').strip()
    amount_str = request.form.get('amount', '').strip()
    income_date_str = request.form.get('income_date', '').strip()
    description = request.form.get('description', '').strip()

    if not source or not amount_str or not income_date_str:
        flash('Source, amount, and date are required.', 'danger')
        return redirect(url_for('income.index'))

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Income amount must be greater than zero.', 'danger')
            return redirect(url_for('income.index'))
    except ValueError:
        flash('Invalid amount entered.', 'danger')
        return redirect(url_for('income.index'))

    try:
        income_date = datetime.strptime(income_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
        return redirect(url_for('income.index'))

    new_income = Income(
        user_id=g.user.id,
        source=source,
        amount=amount,
        income_date=income_date,
        description=description
    )

    try:
        db.session.add(new_income)
        db.session.commit()
        flash('Income record added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Database error while adding income.', 'danger')

    return redirect(url_for('income.index'))

@income_bp.route('/income/edit/<int:income_id>', methods=['POST'])
@login_required
def edit(income_id):
    income_record = Income.query.filter_by(id=income_id, user_id=g.user.id).first_or_404()

    source = request.form.get('source', '').strip()
    amount_str = request.form.get('amount', '').strip()
    income_date_str = request.form.get('income_date', '').strip()
    description = request.form.get('description', '').strip()

    if not source or not amount_str or not income_date_str:
        flash('Source, amount, and date are required.', 'danger')
        return redirect(url_for('income.index'))

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Income amount must be greater than zero.', 'danger')
            return redirect(url_for('income.index'))
    except ValueError:
        flash('Invalid amount entered.', 'danger')
        return redirect(url_for('income.index'))

    try:
        income_date = datetime.strptime(income_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'danger')
        return redirect(url_for('income.index'))

    income_record.source = source
    income_record.amount = amount
    income_record.income_date = income_date
    income_record.description = description

    try:
        db.session.commit()
        flash('Income record updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Database error while updating income.', 'danger')

    return redirect(url_for('income.index'))

@income_bp.route('/income/delete/<int:income_id>', methods=['POST'])
@login_required
def delete(income_id):
    income_record = Income.query.filter_by(id=income_id, user_id=g.user.id).first_or_404()

    try:
        db.session.delete(income_record)
        db.session.commit()
        flash('Income record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Database error while deleting income.', 'danger')

    return redirect(url_for('income.index'))
