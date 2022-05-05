import os
import time

from flask import Blueprint, flash, redirect, render_template, request, current_app, g
from werkzeug.utils import secure_filename

from auth import login_required
from core import check_attendance, AttendanceStatus
from data_model import User, Course
from db import (
    fetch_course_by_id, update_attendance_record,
    fetch_course_from_teacher, fetch_attendance_detail_by_student, fetch_student_list_from_course
)

bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@bp.route('/', methods=('GET',))
@login_required
def index():
    if g.user.role == 1:
        course_list = fetch_course_from_teacher(g.user.id)
        return render_template('attendance/index.html', course_list=course_list)
    else:
        g.error = '你所在的用户组无法执行此操作'
        return render_template('error.html')


@bp.route('/', methods=('POST',))
@login_required
def post_photo():
    # if 'file' not in request.files:
    #     return redirect(request.url)

    file = request.files['file']
    course_id = request.form['course_id']
    if file.filename == '':
        flash('请选择一个文件')
        return redirect(request.url)
    if not course_id:
        flash('请选择一个课程')
        return redirect(request.url)

    filename = secure_filename(file.filename)
    save_path = os.path.join(current_app.config['TEMP'], filename)
    file.save(save_path)

    student_list = fetch_student_list_from_course(course_id)
    course = fetch_course_by_id(course_id)

    start = time.time()
    batch_attendance_result = attendance(course, student_list, save_path)
    current_app.logger.info(f'考勤分析结束，耗时{time.time() - start:.3f}秒')

    color_block_list = [generate_color_block(attendance_status) for attendance_status in batch_attendance_result]
    headline = ['学号', '姓名']

    return render_template(
        'attendance/index.html',
        zip=zip,  # 必须给定 zip 函数，因为 jinja2 默认没有定义该函数
        headline=headline,
        color_block_list=color_block_list,
        student_list=student_list,
        count_present=batch_attendance_result.count(AttendanceStatus.PRESENT),
        count_absent=batch_attendance_result.count(AttendanceStatus.ABSENT),
    )


def attendance(course: Course, student_list: list[User], photo_path: str) -> list[AttendanceStatus]:
    batch_attendance_result = check_attendance(student_list, photo_path, threshold=current_app.config['THRESHOLD'])

    for attendance_status, student in zip(batch_attendance_result, student_list):
        change_attendance_record(course.id, student.id, attendance_status)

    return batch_attendance_result


def change_attendance_record(course_id: str, student_id: int, attendance_status: AttendanceStatus) -> None:
    old_attendance = fetch_attendance_detail_by_student(course_id, student_id).attendance
    new_attendance = old_attendance + [generate_color_block(attendance_status)]
    update_attendance_record(course_id, student_id, new_attendance)


def generate_color_block(attendance_status: AttendanceStatus) -> str:
    return {
        AttendanceStatus.UNKNOWN: '🟥',
        AttendanceStatus.PRESENT: '🟩',
        AttendanceStatus.ABSENT: '🟥',
    }.get(attendance_status, '🟨')
