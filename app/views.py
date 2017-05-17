#!flask/bin/python

from flask import render_template, redirect, url_for, flash
from app import app
from .forms import LoginForm # import LoginForm class from forms.py

#@app.route('/login', methods = ["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if((form.username.data == 'nakul') and (form.password.data == '12345')):
            flash('Login successful')
            #return redirect(url_for(ask use to select sensor types to display))
            return redirect(url_for('sensor_data'))
    # incorrect login credentials, display login form again!
    return render_template('login.html', title='Sign In', form=form)
