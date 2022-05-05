from sqlite3 import IntegrityError

from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app, g

from auth import login_required
from db import (
    set_nickname,
    add_course, delete_course, update_course,
    fetch_course_from_student, fetch_course_from_teacher,
    fetch_attendance_detail_by_student, fetch_attendance_detail_by_course
)

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@bp.route('/')
@login_required
def index():
    return render_template('dashboard/index.html')


@bp.route('/data')
@login_required
def data():
    if g.user.role == 0:
        course_list = fetch_course_from_student(g.user.id)
        record_list = [fetch_attendance_detail_by_student(course.id, g.user.id) for course in course_list]
        # 计算所有学生中最多的考勤记录次数，方便在模板中绘制表头
        max_record = max(map(lambda _: len(_), [record.attendance for record in record_list])) if record_list else 0
        return render_template(
            'dashboard/data/index.html',
            zip=zip,  # 必须给定 zip 函数，因为 jinja2 默认没有定义该函数
            headline=['课程代号', '课程名称', '任课教师'],
            course_list=course_list,
            record_list=record_list,
            max_record=max_record
        )
    elif g.user.role == 1:
        return render_template(
            'dashboard/data/index.html',
            course_list=fetch_course_from_teacher(g.user.id),
            headline=['课程代号', '课程名称', '操作']
        )
    else:
        g.error = '你所在的用户组无法执行此操作'
        return render_template('error.html')


@bp.route('/data/teacher_course_add', methods=('GET', 'POST'))
@login_required
def teacher_course_add():
    if request.method == 'POST':
        course_id = request.form['course_id'].strip()
        course_name = request.form['course_name'].strip()
        teacher_id = g.user.id
        error = None

        if not course_id:
            error = '课程代号不能为空'
        elif not course_name:
            error = '课程名称不能为空'
        elif not teacher_id:
            error = '教师不能为空'

        if error is None:
            try:
                add_course(course_id, course_name, teacher_id)
            except IntegrityError:
                current_app.logger.warning(f'{g.user.nickname}（{g.user.username}）尝试添加已存在的课程 {course_id}')
                error = '课程已存在'
            else:
                current_app.logger.info(f'{g.user.nickname}（{g.user.username}）已添加课程 {course_id}')
                flash(f'课程添加成功')
                return redirect(url_for('dashboard.data'))

        flash(error)

    return render_template('dashboard/data/edit/add_course.html')


@bp.route('/data/attendance_detail')
@login_required
def attendance_detail():
    if g.user.role == 1:
        course_id = request.args.get('course_id')
        record_list = fetch_attendance_detail_by_course(course_id)
        # 计算所有学生中最多的考勤记录次数，方便在模板中绘制表头
        max_record = max(map(lambda _: len(_), [record.attendance for record in record_list])) if record_list else 0
    else:
        g.error = '你所在的用户组无法执行此操作'
        return render_template('error.html')

    return render_template(
        'dashboard/data/detail.html',
        headline=['学生编号', '学生姓名'],
        record_list=record_list,
        max_record=max_record
    )


@bp.route('/data/teacher_course_edit', methods=('GET', 'POST'))
@login_required
def teacher_course_edit():
    if request.method == 'POST':
        course_id = request.form['course_id'].strip()
        name = request.form['name'].strip()
        teacher_id = g.user.id
        error = None

        if g.user.role != 1:
            current_app.logger.warning(
                f'{g.user.nickname}（{g.user.username}）尝试修改课程 {course_id} 失败'
                f'因为他不是教师'
            )
            error = '您不是教师，无法修改课程'

        if error is None:
            try:
                result = update_course(course_id, name, teacher_id)
            except IntegrityError:
                error = '无法修改课程'
            else:
                if result:
                    current_app.logger.info(f'{g.user.nickname}（{g.user.username}）已修改课程 {course_id}')
                    flash(f'课程修改成功')
                    return redirect(url_for('dashboard.data'))
                else:
                    current_app.logger.warning(
                        f'{g.user.nickname}（{g.user.username}）尝试修改课程 {course_id} 失败，因为他不是该课程的教师'
                    )
                    error = '你不是该课程的教师，禁止修改此课程'

        flash(error)

    course_id = request.args.get('course_id')
    name = request.args.get('name')
    return render_template('dashboard/data/edit/edit_course.html', course_id=course_id, name=name)


@bp.route('/data/teacher_course_delete')
@login_required
def teacher_course_delete():
    course_id = request.args.get('course_id')
    delete_course(course_id)
    current_app.logger.info(f'{g.user.nickname}（{g.user.username}）已删除课程 {course_id}')
    flash(f'课程删除成功')
    return redirect(url_for('dashboard.data'))


@bp.route('profile', methods=('GET', 'POST'))
@login_required
def profile():
    if request.method == 'POST':
        nickname = request.form['nickname'].strip()
        if nickname:
            g.user.nickname = nickname
            set_nickname(g.user.id, nickname)
        current_app.logger.info(f'{g.user.nickname}（{g.user.username}）已修改个人信息')
        flash('个人信息修改成功')
        return redirect(url_for('dashboard.profile'))

    return render_template('dashboard/profile.html')
