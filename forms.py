from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField


##WTForm
class CreatePostForm(FlaskForm):
    """
    A class used to create a form to allow the admin to create new blog posts
    ...
    Attributes
    ----------
    title: StringField
        the title of the blog post
    subtitle: StringField
        the subtitle of the blog post
    img_url: StringField
        a URL to an image relevant to the blog post
    body: StringField
        the main content of the blog post
    submit: SubmitField
        submit button to submit the data
    """

    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


## Create a WTForm for new users
class UserForm(FlaskForm):
    """
    A class used to create a form to allow the user to register
    ...
    Attributes
    ----------
    email: StringField
        the user's email
    name: StringField
        the user's name
    password: StringField
        the user's password
    submit: SubmitField
        submit button to submit the data
    """

    email = StringField(label='Email:', validators=[DataRequired()]) # Note you need to install wtforms[email] something to use email validator
    name = StringField(label='Name:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Sign me up!')


# Create a WTForm for logging in
class LoginForm(FlaskForm):
    """
    A class used to create a form to allow the user to login
    ...
    Attributes
    ----------
    email: StringField
        the user's email
    password: StringField
        the user's password
    submit: SubmitField
        submit button to submit the data
    """
    email = StringField(label='Email:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Log me in!')


# create a wtform for adding comments to a blog post
class CommentForm(FlaskForm):
    """
    A class used to create a form to allow the user to add comments to a blog post
    ...
    Attributes
    ----------
    comment: StringField
        the main content of the comment
    submit: SubmitField
        submit button to submit the data
    """

    comment = CKEditorField(label='Comment', validators=[DataRequired()])
    submit = SubmitField(label='Submit Comment')