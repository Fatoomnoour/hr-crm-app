from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'

db = SQLAlchemy(app)

# نموذج الموظف
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)

# إنشاء قاعدة البيانات
with app.app_context():
    db.create_all()

# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template('index.html')

# عرض جميع الموظفين
@app.route('/employees')
def employees():
    all_employees = Employee.query.all()
    return render_template('employees.html', employees=all_employees)

# إضافة موظف جديد
@app.route('/add', methods=['POST'])
def add_employee():
    name = request.form['name']
    email = request.form['email']
    department = request.form['department']
    job_title = request.form['job_title']
    
    new_employee = Employee(name=name, email=email, department=department, job_title=job_title)
    db.session.add(new_employee)
    db.session.commit()
    
    return redirect('/employees')

# تعديل موظف
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        employee.name = request.form['name']
        employee.email = request.form['email']
        employee.department = request.form['department']
        employee.job_title = request.form['job_title']
        db.session.commit()
        return redirect('/employees')
    
    return render_template('edit_employee.html', employee=employee)

# حذف موظف
@app.route('/delete/<int:id>', methods=['POST'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    return redirect('/employees')

# تصفية الموظفين حسب القسم
@app.route('/filter', methods=['POST'])
def filter_employees():
    department = request.form['department']
    if department:
        filtered_employees = Employee.query.filter_by(department=department).all()
    else:
        filtered_employees = Employee.query.all()
    return render_template('employees.html', employees=filtered_employees)

if __name__ == '__main__':
    app.run(debug=True)