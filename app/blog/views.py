from flask import g, Blueprint, render_template, request, flash, url_for, redirect
from app.db import get_db
from app.users.views import login_required
from app.utils import form_errors
from datetime import datetime
from app.blog.tags import create_tags, update_tags, get_tags
from app.blog.utils import pagination, slugify

bp = Blueprint('blog', __name__)

@bp.route('/')
def posts():
  user = g.user
  db = get_db()
  now = datetime.now()

  # Post pagination
  post_count = db.execute("""--sql
  SELECT COUNT(*) FROM posts WHERE posts.publish <= ? AND posts.publish""", (now,)).fetchone()[0]
  page = request.args.get('page') or 1
  paginate = pagination(post_count, int(page))

  # Retrive all published post
  query = f"""--sql
  SELECT * FROM posts WHERE posts.publish <= '%s' AND posts.publish !='' ORDER BY `created` DESC LIMIT %s OFFSET %s""" %(now, paginate['per_page'], paginate['offset'])

  # Admin query: Retrive all posts
  if user is not None and user['is_admin']:
      post_count = db.execute("""--sql
      SELECT COUNT(*) FROM posts""").fetchone()[0]
      paginate = pagination(post_count, int(page))
      query = """--sql
      SELECT * FROM posts ORDER BY created DESC LIMIT %s OFFSET %s""" %(paginate['per_page'], paginate['offset'])
  
  # Posts
  post_list  = db.execute(query).fetchall()
  return render_template('index.html', posts=post_list, date=now.date(), paginator=paginate)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def post_create():
    # if user is not admin return redirect
    if not g.user['is_admin']:
       return redirect(url_for('blog.posts'))
    db = get_db()
    errors = form_errors('title', 'body', 'tags') # error handler dictionary
    if request.method == 'POST':
      # Retrieve post data
      title = request.form['title']
      slug = slugify(title)
      body = request.form['body']
      tags = request.form.get('tags', None)
      publish = request.form.get('publish', None)
      # Check for errors
      if not title:
          errors['title'] = errors['blank']
      if not body:
          errors['body'] = errors['blank']
      if not tags:
         errors['tags'] = errors['blank']
      if title and body and tags: # If data valid create post
          query = """--sql
          INSERT INTO posts (title, slug, body, publish, user_id) 
          VALUES ('%s', '%s', '%s', '%s', %s)""" %(title, slug, body, publish, g.user['id'])
          db.execute(query)
          db.commit()
          # Get created post
          post = db.execute("""--sql
          SELECT id FROM posts WHERE slug=?""", (slug,)).fetchone()
          create_tags(tags.split(','), post['id']) # create tags for post
          flash(f'{title} was created', category='success')
          return redirect(url_for('blog.post_detail', slug=slug))
      return render_template('blog/form.html', post=None, errors=errors, title='Create Post')
    return render_template('blog/form.html', post=None, errors=errors, title='Create Post')

@bp.route('/<slug>')
def post_detail(slug):
    db = get_db()
    post = db.execute("""--sql
    SELECT * FROM posts WHERE slug = ? """, (slug,)).fetchone()
    tags = get_tags(post['id'])
    return render_template('blog/detail.html', post=post, tags=tags)

@bp.route('/<slug>/edit', methods=('GET', 'POST'))
@login_required
def post_edit(slug):
  if not g.user['is_admin']:
    return redirect(url_for('blog.posts'))
  db = get_db()
  errors = form_errors('title', 'body', 'tags')
  if request.method == 'POST':
    title = request.form['title']
    post_slug = slugify(title)
    body = request.form['body']
    tags = request.form.get('tags', None)
    publish = request.form.get('publish', None)
    if not title:
      errors['title'] = errors['blank']
    if not body:
      errors['body'] = errors['blank']
    if not tags:
       errors['tags'] = errors['blank']
    if title and body and tags:
       query = """--sql
       UPDATE posts SET title='%s', slug='%s', body='%s', publish='%s' WHERE slug = '%s'""" %(title, slugify(title), body, publish, slug)
       db.execute(query)
       db.commit()
       post_id = db.execute("""--sql
       SELECT id FROM posts WHERE slug = ?""", (slugify(title),)).fetchone()[0]
       update_tags(tags.split(','), post_id) # update the slug
       flash(f'{title} was updated', category='success')
       return redirect(url_for('blog.post_detail', slug=post_slug))
  
  post = db.execute("""--sql
  SELECT * FROM posts WHERE slug = ?""", (slug,)).fetchone()
  tags = get_tags(post['id'])

  return render_template('blog/form.html', errors=errors, post=post, tags=tags, title='Edit Post')

@bp.route('/<slug>/delete')
@login_required
def post_delete(slug):
    # Remove post from database
    db = get_db()
    db.execute("""--sql
    DELETE FROM posts WHERE slug = ?""", (slug,))
    flash('Post was deleted', category='danger')
    return redirect(url_for('blog.posts'))

@bp.route('/preview', methods=('GET', 'POST'))
def post_preview():
   if request.method == 'POST':
    title = request.form['title']
    body = request.form['body']
    tags = request.form['tags']
    publish = request.form['publish']
    date = publish
    if title and body and tags:
      if publish:
        date = datetime.strptime(publish, '%Y-%m-%d').date()
      post = {
          'title': title,
          'body': body,
          'publish': date,
      }
      return render_template('blog/detail.html', post=post, tags=tags.split(','))
    flash('Nothing to preview', category='danger')
    return redirect(url_for('blog.post_create'))