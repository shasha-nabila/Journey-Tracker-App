# Include what you need here
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, EqualTo, Length

# Form example
# class FormName(FlaskForm):
#   username = StringField(validators=[DataRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Enter username"})
#   submit = SubmitField("Sign Up")