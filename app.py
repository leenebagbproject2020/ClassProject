import os



from flask import Flask, render_template, request, redirect, session, flash

from flask_bootstrap import Bootstrap

from functools import wraps



from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate



project_dir = os.path.dirname(os.path.abspath(__file__))

database_file = "sqlite:///{}".format(os.path.join(project_dir, "gradebook.db"))



app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = database_file



bootstrap = Bootstrap(app)

db = SQLAlchemy(app)

migrate = Migrate(app, db)



student_identifier = db.Table('student_identifier',

                              db.Column('class_id', db.Integer, db.ForeignKey('class.id')),

                              db.Column('student_id', db.Integer, db.ForeignKey('student.id'))

                              )





class User(db.Model):

    username = db.Column(db.String(80), primary_key=True, unique=True)

    password = db.Column(db.String(80), nullable=False)




#Emmanuel Neba
class Student(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    first_name = db.Column(db.String(80), nullable=False)

    last_name = db.Column(db.String(80), nullable=True)

    student_id = db.Column(db.String(80), nullable=False, unique=True)

    student_major = db.Column(db.String(80), nullable=True)

    email = db.Column(db.String(80), nullable=True)

    grades = db.relationship('Grade', backref='student', lazy=True)




#Emmanuel Neba
class Class(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(80), nullable=False, unique=True)

    students = db.relationship("Student",

                               secondary=student_identifier)

    assignments = db.relationship('Assignment', backref='class', lazy=True)




#Emmanuel Neba
class Assignment(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(80), nullable=False, unique=True)

    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)

    grades = db.relationship('Grade', backref='assignment', lazy=True)




#Emmanuel Neba
class Grade(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    grade = db.Column(db.Integer)

    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)




#Kang Lee
def login_required(f):

    @wraps(f)

    def wrap(*args, **kwards):

        if 'logged_in' in session:

            return f(*args, **kwards)

        else:

            error="You need to login first"

            return redirect("/login/")

    return wrap


#Kang Lee
@app.route("/register/", methods=['POST', 'GET'])

def register():

    error = None

    if request.method == 'POST':

        user = User.query.filter_by(username=request.form['username']).first()

        if user is not None:

            error = "Username already exist"

            return render_template("register.html", error=error)

        else:

            user = User(username=request.form['username'], password=request.form['password'])

            db.session.add(user)

            db.session.commit()

            return render_template("login.html", error=error)

    return render_template("register.html", error=error)




#Kang Lee
@app.route("/login/", methods=['GET', 'POST'])

def login():

    error = None

    if request.method == 'POST':

        user = User.query.filter_by(username=request.form['username']).first()



        if user is None or user.password != request.form['password']:

            error = 'Invalid Credentials. Please try again.'

        else:

            session['logged_in'] = True

            return redirect("/")

    return render_template("login.html", error=error)


#Kang Lee
@app.route("/logout/")

def logout():

    session.pop('logged_in', None)

    return redirect("/login/")


#Kang Lee
@app.route("/", methods=["GET"])

@login_required

def home(error=None):

    classes = Class.query.all()

    students = Student.query.all()

    return render_template("home.html", classes=classes, students=students, error=error)


#Kang Lee
@app.route("/", methods=["POST"])

@login_required

def add_class():

    clas = Class.query.filter_by(name=request.form.get("name")).first()



    if clas:

        return home(error="Class with same name exists")

    new_class = Class(name=request.form.get("name"))

    db.session.add(new_class)

    db.session.commit()

    return home()




#Kang Lee
@app.route("/<id>/", methods=["GET"])

@login_required

def get_class(id, error=None):

    cl = Class.query.filter_by(id=id).first()

    grades = db.session.query(Grade, Assignment, Student) \

        .outerjoin(Assignment, Grade.assignment_id == Assignment.id) \

        .filter_by(class_id=id) \

        .outerjoin(Student, Grade.student_id == Student.id) \

        .order_by(Student.first_name) \

        .all()



    return render_template("class.html", clas=cl, grades=grades, error=error)




#Kang Lee
@app.route("/<id>/addstudent/", methods=["POST"])

@login_required

def add_student_to_class(id):

    cl = Class.query.filter_by(id=id).first()



    student_id = request.form.get("student_id")

    student = Student.query.filter_by(student_id=student_id).first()



    if not student:

        return get_class(id, error="Student does not exist")



    if student in cl.students:

        return get_class(id, error="Student already added to class")



    cl.students.append(student)

    for assignment in Assignment.query.filter_by(class_id=id).all():

        db.session.add(Grade(assignment_id=assignment.id, student_id=student.id, class_id=id, grade=0))

    db.session.commit()

    return redirect("/" + id + "/")



@app.route("/<id>/deletestudent/", methods=["POST"])
@login_required
def delete_student_from_class(id):

    cl = Class.query.filter_by(id=id).first()
    student_id = request.form.get("student_id")
    student = Student.query.filter_by(id=student_id).first()
    grades = Grade.query.filter_by(class_id=id).filter_by(student_id=student_id).all()


    cl.students.remove(student)
    for grade in grades:
    db.session.delete(grade)
    db.session.commit()
    return redirect("/" + id + "/")



@app.route("/<id>/addassignment/", methods=["POST"])
@login_required
def add_assignment_to_class(id):

    cl = Class.query.filter_by(id=id).first()

    name = request.form.get("name")
    assignment = Assignment.query.filter_by(name=name).first()
    if assignment and assignment in cl.assignments:

        return get_class(id, error="Assignment already added to class")

    assignment = Assignment(name=request.form.get("name"), class_id=id)
    cl.assignments.append(assignment)
    for student in Student.query.all():
        if student in cl.students:
    db.session.add(Grade(assignment_id=assignment.id, student_id=student.id, class_id=id, grade=0))
    db.session.commit()
    return redirect("/" + id + "/")



#Emmanuel Neba
@app.route("/<id>/deleteassignment/", methods=["POST"])
@login_required
def delete_assignment_from_class(id):
    assignment_id = request.form.get("id")
    assignment = Assignment.query.filter_by(id=assignment_id).first()
    grades = Grade.query.filter_by(class_id=id).filter_by(assignment_id=assignment_id).all()
    for grade in grades:
    db.session.delete(grade)
    db.session.delete(assignment)
    db.session.commit()
    return redirect("/" + id + "/")



#Kang Lee
@app.route("/student/", methods=["POST"])
@login_required
def add_student():
    student = Student.query.filter_by(student_id=request.form.get("student_id")).first()
    if student:
        return home("Student Id already exists")
    student = Student(
        first_name=request.form.get("first_name"),
        last_name=request.form.get("last_name"),
        student_id=request.form.get("student_id"),
        student_major=request.form.get("major"),
        email=request.form.get("email")
    )
    db.session.add(student)
    db.session.commit()
    return home()

#Kang Lee
@app.route("/student/<id>/", methods=["POST"])
@login_required
def update_student(id):
    newname = request.form.get("newname")
    student = Student.query.filter_by(id=id).first()
    student.first_name = newname
    db.session.commit()

    return redirect("/")

#Kang Lee
@app.route("/student/<id>/delete/", methods=["POST"])
@login_required
def delete_student(id):
    student = Student.query.filter_by(id=id).first()
    db.session.delete(student)
    db.session.commit()
    return redirect("/")

#Emmanuel Neba
@app.route("/<id>/<stdid>/", methods=["GET"])
@login_required
def get_student_grades(id, stdid):
    clas = Class.query.filter_by(id=id).first()
    student = Student.query.filter_by(id=stdid).first()
    grades = db.session.query(Grade, Assignment)\
        .filter_by(student_id=stdid)\
        .outerjoin(Assignment, Grade.assignment_id == Assignment.id) \
        .filter_by(class_id=id) \
        .all()


    db.session.commit()
    return render_template("student.html", grades=grades, student=student, clas=clas)



#Emmanuel Neba
@app.route("/<id>/<stdid>/", methods=["POST"])
@login_required
def update_student_grades(id, stdid):
    grade_id = request.form.get("grade_id")
    grade = Grade.query.filter_by(id=grade_id).first()
    grade.grade = request.form.get("grade")

    db.session.commit()

    return redirect("/" + id + "/" + stdid  + "/")


if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True)
