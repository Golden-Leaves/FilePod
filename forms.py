from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField,FileField
from wtforms.validators import InputRequired, URL,Email,Length,DataRequired

class UploadFileForm(FlaskForm):
    files = FileField("File",validators=[DataRequired("No files selected")])
    