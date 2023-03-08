import functools
from flask import Blueprint, request, flash, render_template, redirect, url_for, session, g
from werkzeug.security import check_password_hash, generate_password_hash
from app.db import get_db
from app.utils import form_errors

bp = Blueprint('users', __name__)

@bp.route('/register', methods=('GET', 'POST'))
def register():
  db = get_db()
  errors = form_errors('email', 'password')
  if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']
    
    if email and password:
        hash_password = generate_password_hash(password)
        query = """--sql
        INSERT INTO users (`email`, `password`) VALUES ('%s', '%s')""" %(email, hash_password)
        db.execute(query)
        db.commit()
        flash('Account was created', 'success')
        return redirect(url_for('users.login'))
      
    if not email:
      errors['email'] = errors['blank']
    if not password:
      errors['password'] = errors['blank']
  return render_template('users/register.html', errors=errors)

@bp.route('/login', methods=('GET', 'POST'))
def login():
   db = get_db()
   if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']

    user = db.execute("""--sql
    SELECT * FROM users WHERE email = ?""", (email,)).fetchone()
    if user is None or not check_password_hash(user['password'], password):
      flash('The email address or password you entered is incorrect', 'danger')
      return redirect(url_for('users.login'))
    
    session.clear()
    session['user_id'] = user['id']
    return redirect(url_for('blog.posts'))

   return render_template('users/login.html')

@bp.route('/logout', methods=('GET',))
def logout():
  session.clear()
  flash('You logged out', category='success')
  return redirect(url_for('users.login'))

@bp.before_app_request
def load_auth_user():
  user_id = session.get('user_id')
  if user_id is None:
    g.user = None
  else:
    db = get_db()
    user = db.execute("""--sql
    SELECT * FROM users WHERE id = ?""", (user_id,)).fetchone()
    g.user = user

def login_required(view):
  @functools.wraps(view)
  def wrapped_view(**kwargs):
    if g.user is None:
      return redirect(url_for('users.login'))
    return view(**kwargs)
  return wrapped_view


