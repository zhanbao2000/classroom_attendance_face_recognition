import time
from sqlite3 import IntegrityError

from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app, g

from auth import login_required
from core import save_student_photo, save_student_face_descriptor
from db import add_student_to_course, fetch_all_admin, create_user, delete_user_by_id, fetch_user_by_username

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/course_manager', methods=('GET', 'POST'))
@login_required
def course_manager():
    if request.method == 'POST':
        student_username = request.form['student_username'].strip()
        course_id = request.form['course_id'].strip()
        error = None

        if g.user.role not in [2, 3]:
            current_app.logger.warning(
                f'{g.user.nickname}（{g.user.username}）尝试管理学生 {student_username} 的课程 {course_id} 失败'
                f'因为他不是管理员'
            )
            error = '您不是管理员，无法管理学生的课程'

        if error is None:
            try:
                add_student_to_course(student_username, course_id)
            except IntegrityError:
                error = '无法将学生添加到课程'
            except RuntimeError as e:  # 学生不存在，或教师不存在
                error = str(e)
            else:
                current_app.logger.info(
                    f'{g.user.nickname}（{g.user.username}）已将学生 {student_username} 添加到课程 {course_id}'
                )
                flash(f'学生添加成功')
                return redirect(url_for('admin.course_manager'))

        flash(error)

    return render_template('admin/course_manager.html')


@bp.route('/photo_manager', methods=('GET', 'POST'))
@login_required
def photo_manager():
    if request.method == 'POST':
        file = request.files['file']
        student_username = request.form['student_username'].strip()
        error = None

        if g.user.role not in [2, 3]:
            current_app.logger.warning(
                f'{g.user.nickname}（{g.user.username}）尝试为学生 {student_username} 添加照片失败'
                f'因为他不是管理员'
            )
            error = '您不是管理员，无法为学生添加照片'

        if file.filename == '':
            error = '请选择一个文件'

        if fetch_user_by_username(student_username) is None:
            error = '学生不存在'

        if error is None:
            try:
                start = time.time()
                photo_path = save_student_photo(student_username, file)
                save_student_face_descriptor(student_username, photo_path)
            except Exception as e:
                error = str(e)
            else:
                current_app.logger.info(
                    f'{g.user.nickname}（{g.user.username}）已为学生 {student_username} 添加照片，'
                    f'耗时 {time.time() - start:.3f} 秒'
                )
                flash(f'照片添加成功')
                return redirect(url_for('admin.photo_manager'))

        flash(error)

    return render_template('admin/photo_manager.html')


@bp.route('/admin_manager')
@login_required
def admin_manager():
    if g.user.role == 3:
        return render_template(
            'admin/admin_manager.html',
            admin_list=fetch_all_admin(),
            headline=['用户名', '昵称', '操作']
        )

    g.error = '你所在的用户组无法执行此操作'
    return render_template('error.html')


@bp.route('/admin_new', methods=('GET', 'POST'))
@login_required
def admin_new():
    if g.user.role == 3:
        if request.method == 'POST':
            username = request.form['username'].strip()
            password = request.form['password'].strip()
            error = None

            if not username:
                error = '用户名未填写'
            elif not password:
                error = '密码未填写'
            elif not username.isalnum():
                error = '用户名只能是字母和数字'
            elif len(username) < 3 or len(username) > 20:
                error = '用户名长度必须在 3 到 20 之间'

            if error is None:
                try:
                    user = create_user(username, password, 2)
                except IntegrityError:
                    error = f'用户名 {username} 已被注册过'
                else:
                    flash(f'管理员 {user.username} 已创建成功')
                    return redirect(url_for('admin.admin_manager'))

            flash(error)

        return render_template('admin/admin_new.html')

    g.error = '你所在的用户组无法执行此操作'
    return render_template('error.html')


@bp.route('/admin_delete')
@login_required
def admin_delete():
    admin_id = request.args.get('admin_id')
    if g.user.role == 3:
        try:
            delete_user_by_id(admin_id)
        except IntegrityError:
            g.error = '无法删除用户'
        else:
            flash(f'用户 {admin_id} 已删除')
            return redirect(url_for('admin.admin_manager'))

    g.error = '你所在的用户组无法执行此操作'
    return render_template('error.html')
