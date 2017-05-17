from flask_wtf import Form
from wtforms import StringField, BooleanField, PasswordField, SelectField, RadioField
from wtforms.validators import DataRequired, Length, ValidationError

def validate_user(form, field):
    if field.data != 'nakul':
        raise ValidationError('Incorrect username')        

def validate_pw(form, field):
    if field.data != '12345':
        raise ValidationError('Incorrect password')   

# form class for login
class LoginForm(Form):
    username = StringField('username',
                            validators = [
                            DataRequired(),
                            validate_user,
                            Length(max = 10, 
                            message='Max username is 10 characters')])
    password = PasswordField('password',
                             validators = [
                             DataRequired(),
                             validate_pw,
                             Length(min = 5,
                             message='Min password length is 5')])

# form class to choose types of sensors
class IndexForm(Form):
    temperature = BooleanField('temperature', default = False)
    humidity = BooleanField('humidity', default = False)
    gas = BooleanField('gas', default = False)
    flame = BooleanField('flame', default = False)
    raindrop = BooleanField('raindrop', default = False)
    emergency = BooleanField('emergency', default = True)
    motion = BooleanField('motion', default = False)

# form class to choose types of sensors
class GraphForm(Form):
    temperature = BooleanField('temperature', default = False)
    humidity = BooleanField('humidity', default = False)
    
# form class for logout
class LogoutForm(Form):
    logout = BooleanField('logout', default = False)
    
