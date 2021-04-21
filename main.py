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

#Initiate gravatar with flask application and default parameters
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# Initiate the login manager and then use it on the app
login_manager = LoginManager()
login_manager.init_app(app)
# Create the user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES

class User(UserMixin, db.Model): # Create a new User table in the same database
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    #create a bidirectional one to many relationship with BlogPost
    #this will act like a list of BlogPost objects attached to each User
    #The 'parent' refers to the parent property in the Blogpost class
    children = relationship('BlogPost', back_populates='parent')
    #Create a bidirectional one to many relationship with Comment
    #this will act like a list of Comment objects attached to each User
    #The 'parent_user' referse to the parent_user property in the Comment class
    children_comment = relationship('Comment', back_populates='parent_user')

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    #create a foreign key, 'users.id' the users refers to the tablename of User
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    #create a bidirectional many to one relationship with User
    #create a reference to the User object, the 'children' refers to the children property in the User class
    parent = relationship('User', back_populates='children')
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    #create a bidirectional one to many relationship with Comment
    #create a reference to the Comment object, the 'parent_blog' refers to the parent_blog property in the Comment class
    children_comment = relationship('Comment', back_populates='parent_blog')

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_blog = relationship('BlogPost', back_populates='children_comment')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    parent_user = relationship('User', back_populates='children_comment')
    comment = db.Column(db.String(250), nullable=False)
    # parent_blog and parent_user will act like lists of User and BlogPost objects attached to each Comment





db.create_all() # Comment this out after creating the new User table

#create python decorator called admin_only so that only if the current_user's id is 1 they can access these routes
#otherwise, they should get a 403 error (not authorised)

def admin_only(function):
    @wraps(function)
    def decorator_function(*args, **kwargs):
        if current_user.is_anonymous:
            return abort(status=403)
        elif current_user.id != 1:
            return abort(status=403)
        return function(*args, **kwargs)
    return decorator_function

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
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
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def show_post(post_id):
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
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=['GET', 'POST'])
@admin_only
def add_new_post():
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
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
