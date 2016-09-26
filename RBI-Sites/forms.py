from flask_wtf import Form
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.fields.html5 import EmailField
from wtforms import TextField
from wtforms import StringField
from wtforms import SelectField
from wtforms import SelectMultipleField
from wtforms import validators


class RegistrationForm(Form):
    email = EmailField('email', validators=[validators.DataRequired(), validators.Email()])
    password = PasswordField('password', validators=[validators.DataRequired(), 
                              validators.Length(min=8, message="Please choose a password of at least 8 characters")])
    password2 = PasswordField('password2', validators=[validators.DataRequired(), 
                               validators.EqualTo('password', message='Passwords must match')])
    submit = SubmitField('submit', [validators.DataRequired()])


class LoginForm(Form):
    loginemail = EmailField('email', validators=[validators.DataRequired(), validators.Email()])
    loginpassword = PasswordField('password', validators=[validators.DataRequired(message="Password field is required")])
    submit = SubmitField('submit', [validators.DataRequired()]) 


class SearchForm(Form):
    site_name = StringField('site_name')
    site_number = StringField('site_number')
    regionChoices = [('','Any Region'),('CENTRAL','CENTRAL'),('EASTERN','EASTERN'),('LIMPOPO','LIMPOPO'),
                     ('MPUMALANGA','MPUMALANGA'),('GAUTENG-North','GAUTENG-North'),('GAUTENG-South','GAUTENG-South'),
                     ('GAUTENG-Central','GAUTENG-Central'),('KZN-NORTH','KZN-NORTH'),('KZN-SOUTH','KZN-SOUTH'),
                     ('WESTERN CAPE','WESTERN CAPE')]
    region = SelectField(u'Region', choices = regionChoices)
    typeChoices = [('','Any type'),('Lattice','Lattice'),('Monopole','Monopole'),('Mono-Lattice','Mono-lattice')]
    tower_type = SelectField(u'Tower Type', choices = typeChoices)
    date_of_inspection = StringField(u'date_of_inspection')
    date_of_inspection_before = StringField(u'date_of_inspection')
    date_of_inspection_after = StringField(u'date_of_inspection')
    submit = SubmitField('searchsubmit', validators=[validators.DataRequired()])


class UpdateForm(Form):
    site_name = StringField('Site Classification')
    site_release_date = StringField(u'site_release_date')
    as_built_choices = [('','Not known'),('Yes','Yes'),('No','No')]
    as_built_available = StringField('as_built_available')
    fault_description = StringField('Fault Description')
    mast_engineer = StringField('Mast Engineer')
    mast_upgraded_choices = [('','Not known'),('Yes','Yes'),('No','No')]
    mast_upgraded = StringField('Mast Upgraded')
    mast_upgraded_date = StringField('Date Mast Upgraded')
    capacity_top = StringField('Capacity at top')
    capacity_10_from_top = StringField('Capacity 10m from top')

    submit = SubmitField('updatesubmit', validators=[validators.DataRequired()])

#

