import os.path

from flask import Flask, url_for, redirect

from db import init_db

app = Flask(__name__)


@app.route('/')
def index():
    return redirect(url_for('dashboard.index'))


def import_config():
    try:
        import config_local as config
    except ImportError:
        import config
        msg = ("""
            找不到文件 config_local.py，推荐使用该文件来配置服务端，
            请在该文件中 from config import *，然后覆写配置，
            作为替代，正在尝试读取 config.py 中的配置。
        """)
        app.logger.warning(msg)
    app.config.from_object(config)
    app.secret_key = app.config['SECRET_KEY']


def check_dir():
    # 检查 data 文件夹必要结构
    for path in ['data', 'data/photo', 'data/temp']:
        if not os.path.isdir(path):
            app.logger.warning(f'{path} 文件夹不存在，将会自动创建')
            os.makedirs(path)


def check_db():
    if not os.path.isfile(app.config['DATABASE']):
        app.logger.warning(f'数据库不存在，将会在 {app.config["DATABASE"]} 中初始化创建数据库')
        with app.app_context():
            init_db()


def register_blueprints():
    import admin
    import auth
    import dashboard
    import attendance

    app.register_blueprint(admin.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(attendance.bp)


def main():
    import_config()
    check_dir()
    check_db()
    register_blueprints()

    app.run(host=app.config['HOST'], port=app.config['PORT'])


if __name__ == '__main__':
    main()
