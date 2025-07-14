from flask import Flask, render_template, flash, redirect, request, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
import random
from functools import wraps

app = Flask(__name__)
app.secret_key='some secret key'


app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='123456'
app.config['MYSQL_DB']='Bloodbank'
app.config['MYSQL_CURSORCLASS']='DictCursor'

mysql =  MySQL(app)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        bgroup = request.form["bgroup"]
        bpackets = request.form["bpackets"]
        fname = request.form["fname"]
        adress = request.form["adress"]

        
        cur = mysql.connection.cursor()

      
        cur.execute("INSERT INTO CONTACT(B_GROUP,C_PACKETS,F_NAME,ADRESS) VALUES(%s, %s, %s, %s)",(bgroup, bpackets, fname, adress))
        cur.execute("INSERT INTO NOTIFICATIONS(NB_GROUP,N_PACKETS,NF_NAME,NADRESS) VALUES(%s, %s, %s, %s)",(bgroup, bpackets, fname, adress))
      
        mysql.connection.commit()

        cur.close()
        flash('Your request is successfully sent to the Blood Bank','success')
        return redirect(url_for('index'))

    return render_template('contact.html')

class RegisterForm(Form):
    name = StringField('Name', [validators.DataRequired(),validators.Length(min=1,max=25)])
    email = StringField('Email',[validators.DataRequired(),validators.Length(min=10,max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Password do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method  == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        password = sha256_crypt.hash(str(form.password.data))

        e_id = name+str(random.randint(1111,9999))
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO RECEPTION(E_ID,NAME,EMAIL,PASSWORD) VALUES(%s, %s, %s, %s)",(e_id, name, email, password))
        
        mysql.connection.commit()
        
        cur.close()
        flashing_message = "Success! You can log in with Employee ID " + str(e_id)
        flash( flashing_message,"success")

        return redirect(url_for('login'))

    return render_template('register.html',form = form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        e_id = request.form["e_id"]
        password_candidate = request.form["password"]

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM RECEPTION WHERE E_ID = %s", [e_id])

        if result > 0:

            data = cur.fetchone()
            password = data['PASSWORD']

            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['e_id'] = e_id

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            cur.close()
        else:
            error = 'Employee ID not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login!', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM BLOODBANK")
    details = cur.fetchall()
    result = len(details)

    if result>0:
        return render_template('dashboard.html',details=details)
    else:
        msg = ' Blood Bank is Empty '
        return render_template('dashboard.html',msg=msg)

    cur.close()

@app.route('/donate', methods=['GET', 'POST'])
@is_logged_in
def donate():
    if request.method  == 'POST':

        dname = request.form["dname"]
        sex = request.form["sex"]
        age = request.form["age"]
        weight = request.form["weight"]
        address = request.form["address"]
        disease =  request.form["disease"]
        demail = request.form["demail"]

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO DONOR(DNAME,SEX,AGE,WEIGHT,ADDRESS,DISEASE,DEMAIL) VALUES(%s, %s, %s, %s, %s, %s, %s)",(dname , sex, age, weight, address, disease, demail))

        mysql.connection.commit()

        cur.close()
        flash('Success! Donor details Added.','success')
        return redirect(url_for('donorlogs'))

    return render_template('donate.html')

@app.route('/donorlogs')
@is_logged_in
def donorlogs():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM DONOR")
    logs = cur.fetchall()

    if result>0:
        return render_template('donorlogs.html',logs=logs)
    else:
        msg = ' No logs found '
        return render_template('donorlogs.html',msg=msg)
    cur.close()

@app.route('/bloodform',methods=['GET','POST'])
@is_logged_in
def bloodform():
    if request.method  == 'POST':

        d_id = request.form["d_id"]
        blood_group = request.form["blood_group"]
        packets = request.form["packets"]

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO BLOOD(D_ID,B_GROUP,PACKETS) VALUES(%s, %s, %s)",(d_id , blood_group, packets))
        cur.execute("SELECT * FROM BLOODBANK")
        records = cur.fetchall()
        cur.execute("UPDATE BLOODBANK SET TOTAL_PACKETS = TOTAL_PACKETS+%s WHERE B_GROUP = %s",(packets,blood_group))

        mysql.connection.commit()

        cur.close()
        flash('Success! Donor Blood details Added.','success')
        return redirect(url_for('dashboard'))

    return render_template('bloodform.html')

@app.route('/notifications')
@is_logged_in
def notifications():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM CONTACT")
    requests = cur.fetchall()

    if result>0:
        return render_template('notification.html',requests=requests)
    else:
        msg = ' No requests found '
        return render_template('notification.html',msg=msg)

    cur.close()

@app.route('/notifications/accept')
@is_logged_in
def accept():
    flash('Request Accepted','success')
    return redirect(url_for('notifications'))

@app.route('/notifications/decline')
@is_logged_in
def decline():
    msg = 'Request Declined'
    flash(msg,'danger')
    return redirect(url_for('notifications'))

if __name__ == '__main__':
    app.run(debug=True)
