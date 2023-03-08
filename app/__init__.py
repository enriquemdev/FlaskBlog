from flask import Flask
from pathlib import Path


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=Path(app.instance_path) / 'db.sqlite3'
    )
    
    try:
        Path(app.instance_path).mkdir()
    except OSError:
        pass 
    
    from . blog.views import bp as blog_bp
    app.register_blueprint(blog_bp)

    from . page.views import bp as page_bp
    app.register_blueprint(page_bp)

    from . users.views import bp as users_bp
    app.register_blueprint(users_bp)
    
    from . import db
    db.init_app(app)
    
    return app