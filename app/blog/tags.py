from app.db import get_db

def create_tags(tags, post_id):
  db = get_db()

  def insert_tag(name):
    # Create tags if they don't exist
    db.execute("""--sql
    INSERT OR IGNORE INTO tags (`name`) VALUES (?)""", (name,))
    db.commit()

    # Get the id of the tag from the database
    tag_id = db.execute("""--sql
    SELECT id FROM tags WHERE name = ?""", (name,)).fetchone()['id']

    # Insert into the posts_tags table post_id and tag_id
    db.execute("""--sql
    INSERT INTO posts_tags (post_id, tag_id) VALUES (?, ?)""", (post_id, tag_id))
  
  list(map(insert_tag, tags))
  db.commit()

def update_tags(tags, post_id):
   db = get_db()
   # Delete or tags with post_id
   db.execute("""--sql
   DELETE FROM posts_tags WHERE post_id = ?""", (post_id,))
   db.commit()
   # Create tags with updated tags
   create_tags(tags, post_id)

# Get tags for a post
def get_tags(post_id):
   db = get_db()
   query = f"""--sql
   SELECT name as tag_name FROM posts_tags INNER JOIN posts ON posts.id = post_id INNER JOIN tags ON tags.id == tag_id WHERE posts.id = %s""" %post_id
   tags = db.execute(query).fetchall()
   return list(map(lambda tag: tag['tag_name'], tags))