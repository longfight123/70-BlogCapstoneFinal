"""The final part in a 'Blog Capstone' project

This 'Flask' app website is the final part of a 'Blog Capstone' project.
In the final part, the ability for a user to register with the blog and authenticate themselves was implemented.
The user's information is hashed and stored securely in a database.
When logged in, the user is able to comment on blog posts.
Only the admin is able to create new blog posts and certain parts of the website are restricted to the admin.
A relational database is used to relate the users to their comments, and comments to the blog posts.
It has 7 pages: The index, about, contact, register, login, make-post and an individual blog post page.
There are 2 HTML templates used in inheritance to keep specific elements on each page.
The blog posts data are obtained from a Postgres/SQLite database. 'Jinja' templating is used
to render 'Python' code inside the HTML templates. The static files (CSS, img, JS) were provided
by the instructor.

This script requires that 'Flask', 'Flask-Bootstrap', 'Flask-SQLAlchemy', 'Flask-WTF',
'flask-ckeditor', and 'werkzeug' be installed within the Python
environment you are running this script in.
"""

from flask import Flask, render_template, redirect, url_for, flash, abort #import abort for the admin_only decorator
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, UserForm, LoginForm, CommentForm # Import the new UserForm and LoginForm and CommentForm
from flask_gravatar import Gravatar
from functools import wraps # this is required for the admin_only decorator
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '8BYkEfBA6O6donzWlSihBXox7C0sKR6b')
ckeditor = CKEditor(app)
Bootstrap(app)

# Initiate gravatar with flask application and default parameters
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None
                    )


# Initiate the login manager and then use it on the app
login_manager = LoginManager()
login_manager.init_app(app)
# Create the user_loader callback


@login_manager.user_loader
def load_user(user_id):
    """a user_loader call back function that Flask-Login users to create
    a User object from the stored user_id

    Parameters
    ----------
    user_id: int
        the id of the user in the Users database

    Returns
    -------
    the User object from the stored user_id
    """
    return User.query.get(user_id)


## CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


## CONFIGURE TABLES

class User(UserMixin, db.Model): # Create a new User table in the same database
    """
    A class used to represent a users record in a users table.
    ...
    Attributes
    ----------
    __tablename__: str
        the name of the table
    id: db.Column
        a integer column representing the id of the user
    email: db.Column
        a string column representing the email of the user
    name: db.Column
        a string column representing the name of the user
    password: db.Column
        a string column representing the hashed password of the user
    children: Relationship
        creates a bidirectional one to many relationship with BlogPost table
    children_comment: Relationship
        creates a bidirectional one to many relationship with the Comment table
    """

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    # create a bidirectional one to many relationship with BlogPost
    # this will act like a list of BlogPost objects attached to each User
    # The 'parent' refers to the parent property in the Blogpost class
    children = relationship('BlogPost', back_populates='parent')
    # Create a bidirectional one to many relationship with Comment
    # this will act like a list of Comment objects attached to each User
    # The 'parent_user' referse to the parent_user property in the Comment class
    children_comment = relationship('Comment', back_populates='parent_user')

class BlogPost(db.Model):
    """
    A class used to represent a BlogPost record in a blog posts table.
    ...
    Attributes
    ----------
    __tablename__: str
        the name of the table
    id: db.Column
        a integer column representing the id of the blog post
    author_id: db.Column
        a foreign key representing the id of the author of the blog post
    parent: Relationship
        creates a many to one relationship with User
    title: db.Column
        a string column representing the title of the blog post
    subtitle: db.Column
        a string column representing the subtitle of the blog post
    date: db.Column
        a string column representing the date of the blog post's creation
    body: db.Column
        a string column representing the main content of the blog post
    img_url: db.Column
        a string column representing a URL relevant to the blog post
    children_comment: db.Column
        creates a one to many relationship with the Comment table
    """

    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # create a foreign key, 'users.id' the users refers to the tablename of User
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # create a bidirectional many to one relationship with User
    # create a reference to the User object, the 'children' refers to the children property in the User class
    parent = relationship('User', back_populates='children')
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # create a bidirectional one to many relationship with Comment
    # create a reference to the Comment object, the 'parent_blog' refers to the parent_blog property in the Comment class
    children_comment = relationship('Comment', back_populates='parent_blog')


class Comment(db.Model):
    """
    A class used to represent a Comment record in a Comments table.
    ...
    Attributes
    ----------
    __tablename__: str
        the name of the table
    id: db.Column
        a integer column representing the id of the comment
    blog_id: db.Column
        a foreign key representing the id of the blog post the comment has a relationship to
    parent_blog: Relationship
        creates a many to one relationship with the blog post table
    author_id: db.Column
        a foreign key representing the id of the author of the blog post
    parent_user: Relationship
        creates a many to one relationship with the User table
    comment: db.Column
        a string column representing the main content of the comment
    """

    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_blog = relationship('BlogPost', back_populates='children_comment')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    parent_user = relationship('User', back_populates='children_comment')
    comment = db.Column(db.String(250), nullable=False)
    # parent_blog and parent_user will act like lists of User and BlogPost objects attached to each Comment


# db.create_all() # Comment this out after creating the new User table

# create python decorator called admin_only so that only if the current_user's id is 1 they can access these routes
# otherwise, they should get a 403 error (not authorised)


def admin_only(function):
    """a decorator function"""
    @wraps(function)
    def decorator_function(*args, **kwargs):
        """
        a decorator function that can be used to ensure that the current user that is logged in is the admin
        when a restricted route is accessed
        """

        if current_user.is_anonymous:
            return abort(status=403)
        elif current_user.id != 1:
            return abort(status=403)
        return function(*args, **kwargs)
    return decorator_function


@app.route('/')
def get_all_posts():
    """the landing page of the website, displays all of the blog posts

    GET: displays all of the blog posts
    """

    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """the registration page, displays a form for the user to register with the website

    GET: displays the registration form
    POST: submits a request to register the user with the website, redirects to the landing page is successful.
            redirects to the login page if the user previously registered
    """

    form = UserForm() # Create a new UserForm and then send it to the template
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first(): # This block will check if an email exists and flash a message
            flash(message='A user with that email already exists. Please try logging in instead.')
            return redirect(url_for('login'))
        new_user = User( # Create a new user to add to the User database, hash the password
            email=form.email.data,
            name=form.name.data,
            password=generate_password_hash(
                password=form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user) # login the newly registered user
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


# Implement everything in the login route, make the wtfform, login the user
@app.route('/login', methods=['GET', 'POST'])
def login():
    """the login page, allows the user to login with their credentials

    GET: displays the form allowing the user to login
    POST: submits a request to login the user, if the information was incorrect, sends a flash displaying the error.
            if the login is successful, redirects the user to the landing page
    """

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # flash them a message if email does not exist and redirect back to login route
        if not user:
            flash(message='This email does not exist. Please try registering.')
            return redirect(url_for('login'))
        if check_password_hash(pwhash=user.password, password=form.password.data):
            login_user(user)
            return redirect(url_for('get_all_posts'))
        # flash them a message if email exists, but password is wrong and redirect to login route
        else:
            flash(message='Incorrect password. Please try again.')
            return redirect(url_for('login'))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    """allows the user to log out of the website
    """

    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
    """displays the individual blog post page and a form that allows a logged in user to comment on the post

    GET: displays the individual blog post page and a form that allows a logged in user to comment on the post
    POST: submits a request to add a comment to the blog post, if the user is not logged in, it redirects them to
            the login page and asks them to login
    """

    requested_post = BlogPost.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash(message='Please login before commenting.')
            return redirect(url_for('login'))
        new_comment = Comment(
            comment=form.comment.data,
            author_id=current_user.id,
            blog_id=post_id
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))
    return render_template("post.html", post=requested_post, form=form)


@app.route("/about")
def about():
    """displays the about page"""

    return render_template("about.html")


@app.route("/contact")
def contact():
    """displays the contact page"""

    return render_template("contact.html")


@app.route("/new-post", methods=['GET', 'POST'])
@admin_only
def add_new_post():
    """displays the page and form to allow the admin to create new blog posts.
        this route is restricted to the admin

    GET: displays the form to allow the admin to create new blog posts
    POST: submits a request to add a new blog post to the database, redirects to the landing page if successful
    """

    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id, # author_id is now an integer that is a foreign key reference to users table
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    """displays the page and form that allows the admin to edit the information of a blog post
        this route is restricted to the admin only

    GET: displays the form that allows the admin to edit the information of a blog post
    POST: submits a request to update the information for the blog post in the database, redirects to the individual blog
            posts page

    Parameters
    ----------
    post_id: int
        the primary key of the blog post
    """

    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.parent.name, #change from post.author to post.parent.name as post.parent is now a user object
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author_id = current_user.id # change from post.author = edit_form.author.data to post.author_id=current_user.id as author_id
        # is now a foreign key reference to user table
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    """deletes the specified blog post, only the admin can delete the blog post

    GET: sends a request to delete the specified blog post

    Parameters:
    -----------
    post_id: int
        the primary key of the blog post
    """
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
