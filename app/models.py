from app import db

db.create_all()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    employees = db.relationship('Employee', backref='user', lazy=True)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    full_points = db.Column(db.Integer, default=0)
    partial_points = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    occurrences = db.relationship('Occurrence', backref='employee', lazy=True)


class Occurrence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    occurrence_type = db.Column(db.String(50), nullable=False)
    exception = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(150))
    employee_id = db.Column(db.Integer,
                            db.ForeignKey('employee.id'),
                            nullable=False)
