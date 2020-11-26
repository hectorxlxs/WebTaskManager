from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Databases/mainDatabase.db'
db = SQLAlchemy(app)


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer)
    content = db.Column(db.String(300))
    done = db.Column(db.Boolean)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(300))
    password = db.Column(db.String(50))


db.create_all()
db.session.commit()


@app.route('/<_register_error>')
def redirected_initial_page(_register_error):
    return render_template("Index.html", redirected=True, register_error=_register_error)


@app.route('/')
def initial_page():
    print(request.cookies.get('email'))
    return render_template("Index.html", _redirected=False)


@app.route('/register-user', methods=['POST'])
def register_user():
    _email = request.form['email']
    _password = request.form['password']
    _repeated_password = request.form['repeatedPassword']

    for user in User.query.all():
        if user.email == _email:
            return redirect(url_for('redirected_initial_page', _register_error="ExistentEmail"))

    if _password != _repeated_password:
        return redirect(url_for('redirected_initial_page', _register_error="DifferentPasswords"))

    new_user = User(email=_email, password=_password)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('redirected_initial_page', _register_error="None"))


@app.route('/log-user-in', methods=['POST'])
def log_user_in():
    _email = request.form['email']
    _password = request.form['password']

    for user in User.query.all():
        if user.email == _email:
            if user.password == _password:
                resp = make_response(redirect(url_for('home')))
                resp.set_cookie('user_id', str(user.id))
                resp.set_cookie('email', str(_email))
                resp.set_cookie('password', str(_password))
                return resp
            else:
                return redirect(url_for('redirected_login', _login_error="InvalidPassword"))

    return redirect(url_for('redirected_login', _login_error="EmailNotFound"))


@app.route('/login/<_login_error>')
def redirected_login(_login_error):
    return render_template('Login.html', login_error=_login_error)


@app.route('/login')
def login():
    return render_template("Login.html")


@app.route('/logout')
def logout():

    resp = make_response(redirect(url_for('initial_page')))
    resp.set_cookie('user_id', '', max_age=0)
    resp.set_cookie('email', '', max_age=0)
    resp.set_cookie('password', '', max_age=0)

    return resp


@app.route('/home')
def home():
    # Lo vuelvo a comprobar que esté correcto para que nadie inserte cookies si es que
    # se puede y luego entre en la cuenta de otra persona metiendo su email o un id aleatorio
    _user_id = request.cookies.get('user_id')
    _email = request.cookies.get('email')
    _password = request.cookies.get('password')

    if not(_user_id and _email and _password):
        return redirect(url_for('logout'))

    for user in User.query.all():
        if str(user.id) == _user_id and user.email == _email and user.password == _password:
            return render_template("Home.html", tasks=Task.query.filter_by(userId=int(_user_id)))

    return redirect(url_for('logout'))


@app.route('/contact')
def contact():
    return render_template("Contact.html")


@app.route('/create-task', methods=['POST'])
def create_task():
    task_name = request.form['task_name']
    if task_name:
        task = Task(content=task_name, done=False, userId=int(request.cookies.get('user_id')))
        db.session.add(task)
        db.session.commit()

    return redirect(url_for('home'))


@app.route('/change-task-status/<task_id>')
def change_task_status(task_id):
    task = Task.query.filter_by(id=int(task_id)).first()
    task.done = not task.done

    db.session.commit()
    return redirect(url_for('home'))


@app.route('/delete-task/<task_id>')
def delete_task(task_id):
    task = Task.query.filter_by(id=int(task_id)).first()
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
