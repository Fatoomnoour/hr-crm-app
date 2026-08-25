import os
import secrets
from functools import wraps

from flask import Flask, abort, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///employees.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
if not app.config['SECRET_KEY'] and os.getenv('FLASK_ENV') == 'production':
    raise RuntimeError('SECRET_KEY must be configured in production')
if not app.config['SECRET_KEY']:
    app.config['SECRET_KEY'] = 'local-development-only-change-me'

db = SQLAlchemy(app)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

@app.context_processor
def inject_csrf_token():
    token = session.setdefault('_csrf_token', secrets.token_urlsafe(32))
    return {'csrf_token': token}

@app.before_request
def protect_state_changing_requests():
    if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        expected = session.get('_csrf_token')
        supplied = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
        if not expected or not supplied or not secrets.compare_digest(expected, supplied):
            abort(400, description='Invalid CSRF token')

def clean_form():
    fields = {}
    for field, limit in [('name', 100), ('email', 100), ('department', 50), ('job_title', 100)]:
        value = request.form.get(field, '').strip()
        if not value or len(value) > limit:
            abort(400, description=f'Invalid {field}')
        fields[field] = value
    if '@' not in fields['email'] or '.' not in fields['email'].rsplit('@', 1)[-1]:
        abort(400, description='Invalid email')
    return fields

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/employees')
def employees():
    return render_template('employees.html', employees=Employee.query.all())

@app.route('/add', methods=['POST'])
def add_employee():
    employee = Employee(**clean_form())
    db.session.add(employee)
    db.session.commit()
    return redirect(url_for('employees'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    if request.method == 'POST':
        for key, value in clean_form().items():
            setattr(employee, key, value)
        db.session.commit()
        return redirect(url_for('employees'))
    return render_template('edit_employee.html', employee=employee)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    return redirect(url_for('employees'))

@app.route('/filter', methods=['POST'])
def filter_employees():
    department = request.form.get('department', '').strip()
    query = Employee.query
    if department:
        query = query.filter_by(department=department)
    return render_template('employees.html', employees=query.all())

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', '0') == '1')
