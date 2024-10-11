from app import app
from flask import render_template, redirect, url_for, request, session, flash

# Mock database to store user data temporarily (for now)
users = {}


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            flash('Username already exists! Please try a different one.',
                  'error')
        else:
            users[username] = password
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        flash('You need to log in to access the dashboard.', 'error')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


# Global dictionary to store employees (make sure it's initialized properly)
employees = {}


@app.before_request
def initialize_session_data():
    # Ensure that the employees dictionary is properly initialized when a user session begins
    if 'username' in session and session['username'] not in employees:
        employees[session['username']] = []


import uuid


@app.route('/employees', methods=['GET', 'POST'])
def employees_list():
    if 'username' not in session:
        flash('You need to log in to manage employees.', 'error')
        return redirect(url_for('login'))

    username = session['username']

    # Handle adding a new employee
    if request.method == 'POST':
        employee_name = request.form['employee_name']
        department = request.form['department']

        if username not in employees:
            employees[username] = []

        # Check if the employee already exists to avoid duplicates
        existing_employee = next((e for e in employees[username] if e['name'] == employee_name), None)
        if existing_employee is None:
            employees[username].append({
                'id': str(uuid.uuid4()),  # Generate a unique ID for each employee
                'name': employee_name,
                'department': department,
                'full_points': 0,
                'partial_points': 0,
                'occurrences': []
            })
            flash(f'Employee {employee_name} added successfully.', 'success')
        else:
            flash(f'Employee {employee_name} already exists.', 'error')

        return redirect(url_for('employees_list'))

    # Search and filter functionality
    search_query = request.args.get('search', '').lower()
    department_filter = request.args.get('department', '').lower()
    flagged_only = request.args.get('flagged', False)

    # Retrieve and sort all employees
    all_employees = sorted(employees.get(username, []), key=lambda e: e['name'].lower())

    # Filter employees based on search query and department filter
    filtered_employees = [
        emp for emp in all_employees
        if search_query in emp['name'].lower() and (
            not department_filter or department_filter in emp['department'].lower())
    ]

    if flagged_only:
        filtered_employees = [
            emp for emp in filtered_employees
            if emp['full_points'] >= 7 or emp['partial_points'] >= 5
        ]

    # Calculate department statistics
    department_stats = {}
    for employee in all_employees:
        dept = employee['department']
        if dept not in department_stats:
            department_stats[dept] = {'total': 0, 'flagged': 0}
        department_stats[dept]['total'] += 1
        if employee['full_points'] >= 7 or employee['partial_points'] >= 5:
            department_stats[dept]['flagged'] += 1

    # Pagination logic
    page = int(request.args.get('page', 1))
    per_page = 20
    total_pages = (len(filtered_employees) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_employees = filtered_employees[start:end]

    # Pass the total number of employees to the template
    total_employees = len(all_employees)

    return render_template(
        'employees.html',
        employees=paginated_employees,
        department_stats=department_stats,
        page=page,
        total_pages=total_pages,
        search_query=search_query,
        department_filter=department_filter,
        total_employees=total_employees
    )



@app.route('/employee/delete/<employee_id>', methods=['GET'])
def delete_employee(employee_id):
    if 'username' not in session:
        flash('You need to log in to manage employees.', 'error')
        return redirect(url_for('login'))

    username = session['username']
    # Find the employee by their unique ID and remove them
    employees[username] = [
        emp for emp in employees.get(username, []) if emp['id'] != employee_id
    ]

    flash('Employee has been successfully deleted.', 'success')
    return redirect(url_for('employees_list'))


import traceback


@app.route('/employee/add_occurrence/<employee_id>', methods=['POST'])
def add_occurrence(employee_id):
    if 'username' not in session:
        flash('You need to log in to manage employees.', 'error')
        return redirect(url_for('login'))

    username = session['username']
    occurrence_date = request.form['occurrence_date']
    occurrence_type = request.form['occurrence_type']
    exception = 'exception' in request.form
    exception_reason = request.form.get('exception_reason', '')

    # Debug statements to check form values
    print(f"Occurrence Date: {occurrence_date}")
    print(f"Occurrence Type: {occurrence_type}")
    print(f"Exception: {exception}")
    print(f"Exception Reason: {exception_reason}")

    # Find the employee by their unique ID
    employee = next(
        (emp
         for emp in employees.get(username, []) if emp['id'] == employee_id),
        None)

    if employee:
        occurrence = {
            'date': occurrence_date,
            'type': occurrence_type,
            'exception': exception,
            'reason': exception_reason
        }
        employee['occurrences'].append(occurrence)

        # Update points only if it's not an exception
        if not exception:
            if occurrence_type == 'Call In':
                employee['full_points'] += 1
            elif occurrence_type in ['Early Out', 'Tardy', 'Early In'
                                     ]:  # Updated to include Early In
                employee['partial_points'] += 1

        flash(f"Occurrence added for {employee['name']}.", 'success')
    else:
        flash('Employee not found.', 'error')

    return redirect(url_for('employees_list'))


@app.route('/employee/delete_occurrence/<employee_id>/<int:occurrence_index>',
           methods=['GET'])
def delete_occurrence(employee_id, occurrence_index):
    if 'username' not in session:
        flash('You need to log in to manage employees.', 'error')
        return redirect(url_for('login'))

    username = session['username']
    employee = next(
        (emp
         for emp in employees.get(username, []) if emp['id'] == employee_id),
        None)

    if employee:
        if 0 <= occurrence_index < len(employee['occurrences']):
            del employee['occurrences'][occurrence_index]
            flash('Occurrence successfully deleted.', 'success')
        else:
            flash('Occurrence not found.', 'error')
    else:
        flash('Employee not found.', 'error')

    return redirect(url_for('employees_list'))


# Edit occurrence route (implementation depends on requirements)

from datetime import datetime, timedelta


@app.route('/update_employees', methods=['POST'])
def update_employees():
    if 'username' not in session:
        flash('You need to log in to update employees.', 'error')
        return redirect(url_for('login'))

    username = session['username']

    try:
        today = datetime.now().date()
        one_year_ago = today - timedelta(days=365)
        one_month_ago = today - timedelta(days=30)

        # Loop through all employees for the logged-in user
        if username in employees:
            for employee in employees[username]:
                # Initialize points to zero before recalculating
                employee['full_points'] = 0
                employee['partial_points'] = 0

                # Filter occurrences based on the date criteria and update points accordingly
                updated_occurrences = []
                for occ in employee['occurrences']:
                    occurrence_date = datetime.strptime(
                        occ['date'], '%Y-%m-%d').date()
                    if occ['type'] == 'Call In' and occurrence_date >= one_year_ago:
                        updated_occurrences.append(occ)
                        if not occ['exception']:
                            employee['full_points'] += 1
                    elif occ['type'] in [
                            'Early Out', 'Tardy'
                    ] and occurrence_date >= one_month_ago:
                        updated_occurrences.append(occ)
                        if not occ['exception']:
                            employee['partial_points'] += 1

                # Update the occurrences list with the valid occurrences
                employee['occurrences'] = updated_occurrences

        flash('Employee occurrences have been updated successfully.',
              'success')
    except Exception as e:
        print(f'Error during update: {e}')
        flash('An error occurred while updating employee occurrences.',
              'error')

    return redirect(url_for('employees_list'))


from flask import send_file
import pandas as pd


@app.route('/export_employees', methods=['GET'])
def export_employees():
    if 'username' not in session:
        flash('You need to log in to export employee data.', 'error')
        return redirect(url_for('login'))

    username = session['username']

    # Prepare the data for export
    data = []
    for employee in employees.get(username, []):
        if not employee[
                'occurrences']:  # If no occurrences, add the employee with empty values
            data.append({
                'Employee Name': employee['name'],
                'Department':
                employee['department'],  # Include department data
                'Full Points': employee['full_points'],
                'Partial Points': employee['partial_points'],
                'Occurrence Date': '',
                'Occurrence Type': '',
                'Exception': '',
                'Reason': ''
            })
        else:  # Add employee's occurrences to the data list
            for occurrence in employee['occurrences']:
                data.append({
                    'Employee Name': employee['name'],
                    'Department':
                    employee['department'],  # Include department data
                    'Full Points': employee['full_points'],
                    'Partial Points': employee['partial_points'],
                    'Occurrence Date': occurrence['date'],
                    'Occurrence Type': occurrence['type'],
                    'Exception': 'Yes' if occurrence['exception'] else 'No',
                    'Reason': occurrence['reason']
                })

    # Create a DataFrame and save it to an Excel file
    df = pd.DataFrame(data)
    file_path = '/tmp/employee_data.xlsx'
    df.to_excel(file_path, index=False)

    return send_file(file_path,
                     as_attachment=True,
                     download_name='employee_data.xlsx')


from werkzeug.utils import secure_filename
import os

import traceback


@app.route('/import_employees', methods=['POST'])
def import_employees():
    if 'username' not in session:
        flash('You need to log in to import employee data.', 'error')
        return redirect(url_for('login'))

    username = session['username']
    file = request.files['file']

    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        file_path = os.path.join('/tmp', filename)
        file.save(file_path)

        try:
            # Clear existing employees for the user before importing
            employees[username] = []

            # Load the Excel file and read the data
            df = pd.read_excel(file_path)

            # Add the employees and occurrences from the Excel file
            for _, row in df.iterrows():
                employee_name = row['Employee Name']
                department = row[
                    'Department'] if 'Department' in row else 'Unknown'  # Handle missing department data
                employee_id = str(
                    uuid.uuid4())  # Generate a unique ID for each employee

                existing_employee = next((e
                                          for e in employees.get(username, [])
                                          if e['name'] == employee_name), None)

                if not existing_employee:
                    # Add a new employee if it doesn't exist
                    existing_employee = {
                        'id':
                        employee_id,  # Ensure each employee has a unique ID
                        'name':
                        employee_name,
                        'department':
                        department,
                        'full_points':
                        row['Full Points']
                        if pd.notna(row['Full Points']) else 0,
                        'partial_points':
                        row['Partial Points']
                        if pd.notna(row['Partial Points']) else 0,
                        'occurrences': []
                    }
                    employees[username].append(existing_employee)

                # Add occurrence only if valid data exists
                if pd.notna(row['Occurrence Date']) and pd.notna(
                        row['Occurrence Type']):
                    existing_employee['occurrences'].append({
                        'date':
                        row['Occurrence Date'],
                        'type':
                        row['Occurrence Type'],
                        'exception':
                        row['Exception'] == 'Yes',
                        'reason':
                        row['Reason'] if pd.notna(row['Reason']) else ''
                    })

            # Sort employees by name alphabetically
            employees[username] = sorted(employees[username],
                                         key=lambda e: e['name'].lower())

            flash(
                'Employee data has been successfully imported and points have been updated!',
                'success')
        except Exception as e:
            print(f"Error during import: {e}")
            traceback.print_exc(
            )  # This will print a full traceback of the error to help with debugging
            flash(
                'An error occurred while importing the file. Please check the file format and try again.',
                'error')

    else:
        flash('Please upload a valid Excel file.', 'error')

    return redirect(url_for('employees_list'))


@app.route('/employee/edit_department/<employee_id>', methods=['POST'])
def edit_department(employee_id):
    if 'username' not in session:
        flash('You need to log in to edit employee details.', 'error')
        return redirect(url_for('login'))

    username = session['username']
    new_department = request.form['new_department']
    employee = next((emp for emp in employees.get(username, []) if emp['id'] == employee_id), None)

    if employee:
        employee['department'] = new_department
        flash(f"Department for {employee['name']} updated successfully.", 'success')
    else:
        flash('Employee not found.', 'error')

    return redirect(url_for('employees_list'))
