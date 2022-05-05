import functools
from sqlite3 import IntegrityError

from flask import Blueprint, flash, redirect, render_template, request, session, url_for, g
from werkzeug.security import check_password_hash

from db import fetch_user_by_id, fetch_user_by_username, create_user

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        role = request.form['role']
        error = None

        if not username:
            error = '用户名未填写'
        elif not password:
            error = '密码未填写'
        elif not username.isalnum():
            error = '用户名只能是字母和数字'
        elif len(username) < 3 or len(username) > 20:
            error = '用户名长度必须在 3 到 20 之间'
        elif role not in ['0', '1']:
            error = '你只能以教师或学生身份注册'

        if error is None:
            try:
                user = create_user(username, password, role)
            except IntegrityError:
                error = f'用户名 {username} 已被注册过'
            else:
                session.clear()
                session['id'] = user.id
                return redirect(url_for('dashboard.index'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        error = None

        user = fetch_user_by_username(username)

        if user is None:
            error = '用户名不存在'
        elif not check_password_hash(user.password, f'{username}{password}'):
            error = '密码错误'

        if error is None:
            session.clear()
            session['id'] = user.id
            return redirect(url_for('dashboard.index'))

        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@bp.before_app_request
def load_logged_in_user():
    """使用 before_app_request 钩子，在每次请求前将用户加载到 g 对象中"""
    user_id = session.get('id')

    if user_id is None:
        g.user = None
    else:
        g.user = fetch_user_by_id(user_id)


def login_required(view):
    """通过设定 login_required 装饰器，在被装饰的视图函数前检查用户是否已登录"""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('id') is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
