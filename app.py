from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort
from config import Config
from models import db, User, Blog, Comment
from forms import RegisterForm, LoginForm, BlogForm, CommentForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config.from_object(Config)

# Rasm yuklash uchun sozlamalar
UPLOAD_FOLDER = os.path.join('static', 'uploads')
PROFILE_FOLDER = os.path.join(UPLOAD_FOLDER, 'profiles')
BLOG_FOLDER = os.path.join(UPLOAD_FOLDER, 'blogs')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# papkalarni yaratib qo‘yish
for folder in [UPLOAD_FOLDER, PROFILE_FOLDER, BLOG_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROFILE_FOLDER'] = PROFILE_FOLDER
app.config['BLOG_FOLDER'] = BLOG_FOLDER

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# create DB if not exists
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Faqat ruxsat berilgan fayl turini tekshiradi
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home / All blogs
@app.route('/')
def index():
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()
    return render_template('index.html', blogs=blogs)

# Register
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter((User.email==form.email.data)|(User.username==form.username.data)).first():
            flash("User with that email or username already exists", "danger")
            return redirect(url_for('register'))
        
        filename = None
        if form.profile_image.data and allowed_file(form.profile_image.data.filename):
            filename = secure_filename(form.profile_image.data.filename)
            form.profile_image.data.save(os.path.join(app.config['PROFILE_FOLDER'], filename))

        hashed = generate_password_hash(form.password.data)
        u = User(
            username=form.username.data, 
            email=form.email.data, 
            password=hashed,
            profile_image=filename  # modelga qo‘shgan bo‘lishingiz kerak
        )
        db.session.add(u)
        db.session.commit()
        flash("Registered! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Logged in successfully", "success")
            return redirect(url_for('index'))
        flash("Invalid credentials", "danger")
    return render_template('login.html', form=form)

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for('index'))

# Profile
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# Create blog
@app.route('/create_blog', methods=['GET', 'POST'])
@login_required
def create_blog():
    form = BlogForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data and allowed_file(form.image.data.filename):
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config['BLOG_FOLDER'], filename))

        new_blog = Blog(
            title=form.title.data,
            content=form.content.data,
            image=filename,
            author=current_user
        )
        db.session.add(new_blog)
        db.session.commit()
        flash('Blog created successfully!', 'success')
        return redirect(url_for('my_blogs'))
    return render_template('update_blog.html', form=form)

# My blogs
@app.route('/myblogs')
@login_required
def my_blogs():
    blogs = Blog.query.filter_by(user_id=current_user.id).order_by(Blog.created_at.desc()).all()
    return render_template('my_blogs.html', blogs=blogs)

# All blogs (others included)
@app.route('/allblogs')
def all_blogs():
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()
    return render_template('all_blogs.html', blogs=blogs)

# Blog detail + comments
@app.route('/blog/<int:blog_id>', methods=['GET','POST'])
def blog_detail(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    # increment views
    blog.views = (blog.views or 0) + 1
    db.session.commit()
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Please login to comment", "warning")
            return redirect(url_for('login'))
        c = Comment(text=form.text.data, user_id=current_user.id, blog_id=blog.id)
        db.session.add(c)
        db.session.commit()
        flash("Comment added", "success")
        return redirect(url_for('blog_detail', blog_id=blog.id))
    comments = Comment.query.filter_by(blog_id=blog.id).order_by(Comment.created_at.desc()).all()
    return render_template('blog_detail.html', blog=blog, form=form, comments=comments)

# Like endpoint (AJAX)
@app.route('/like/<int:blog_id>', methods=['POST'])
@login_required
def like(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    blog.likes = (blog.likes or 0) + 1
    db.session.commit()
    return jsonify({'likes': blog.likes})

# Update blog
@app.route('/update/<int:blog_id>', methods=['GET','POST'])
@login_required
def update_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.user_id != current_user.id:
        abort(403)
    form = BlogForm(obj=blog)
    if form.validate_on_submit():
        blog.title = form.title.data
        blog.content = form.content.data
        if form.image.data and allowed_file(form.image.data.filename):
            filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config['BLOG_FOLDER'], filename))
            blog.image = filename
        db.session.commit()
        flash("Blog updated", "success")
        return redirect(url_for('my_blogs'))
    return render_template('update_blog.html', form=form, create=False)

# Delete blog
@app.route('/delete/<int:blog_id>', methods=['POST'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.user_id != current_user.id:
        abort(403)
    db.session.delete(blog)
    db.session.commit()
    flash("Blog deleted", "info")
    return redirect(url_for('my_blogs'))

# Simple search (optional)
@app.route('/search')
def search():
    q = request.args.get('q','').strip()
    if not q:
        return redirect(url_for('index'))
    blogs = Blog.query.filter(Blog.title.contains(q) | Blog.content.contains(q)).order_by(Blog.created_at.desc()).all()
    return render_template('index.html', blogs=blogs, query=q)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
