import json
import secrets
import sqlite3
import traceback
from typing import Optional

from flask import current_app
from werkzeug.security import generate_password_hash

from data_model import User, Course, Record


class Connect:

    def __init__(self, file_path):
        self.file_path = file_path
        self.conn = sqlite3.connect(self.file_path)
        self.c = self.conn.cursor()

    def __enter__(self) -> sqlite3.Cursor:
        self.conn = sqlite3.connect(self.file_path)
        self.c = self.conn.cursor()
        return self.c

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self.conn:
            self.conn.commit()
            self.conn.close()

        if exc_type:
            current_app.logger.error(traceback.format_exc())
            return False

        return True


def init_db(file_path: Optional[str] = None):
    if not file_path:
        file_path = current_app.config['DATABASE']

    with current_app.open_resource('schema.sql') as f:
        init_sql = f.read().decode('utf8')

    default_admin_username = current_app.config['DEFAULT_ADMIN']
    default_admin_password = secrets.token_urlsafe(16)
    with Connect(file_path) as c:
        c.executescript(init_sql)
        c.execute(
            'INSERT INTO user (nickname, username, password, role) VALUES (?, ?, ?, ?)',
            (default_admin_username, default_admin_username,
             generate_password_hash(f'{default_admin_username}{default_admin_password}'), 3,)
        )

    current_app.logger.warning(f'数据库 {file_path} 已初始化')
    current_app.logger.info(
        f'初始用户为超级管理员，'
        f'用户名：{default_admin_username}，'
        f'密码：{default_admin_password}'
    )


def get_user_model(user: Optional[tuple]) -> Optional[User]:
    if user is None:
        return None
    return User(
        id=user[0],
        nickname=user[1],
        username=user[2],
        password=user[3],
        role=user[4]
    )


def get_course_model(course: Optional[tuple]) -> Optional[Course]:
    if course is None:
        return None
    return Course(
        id=course[0],
        name=course[1],
        teacher_id=course[2],
        teacher_nickname=fetch_user_by_id(course[2]).nickname,
    )


def get_record_model(record: Optional[tuple]) -> Optional[Record]:
    if record is None:
        return None
    student = fetch_user_by_id(record[2])
    return Record(
        id=record[0],
        student_username=student.username,
        student_nickname=student.nickname,
        attendance=json.loads(record[3])
    )


def create_user(username: str, password: str, role: int | str) -> Optional[User]:
    with Connect(current_app.config['DATABASE']) as db:
        db.execute(
            "INSERT INTO user (nickname, username, password, role) VALUES (?, ?, ?, ?)",
            (username, username, generate_password_hash(f'{username}{password}', ), role)
        )
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

    current_app.logger.info(f"用户名 {username} 注册成功")
    return get_user_model(user)


def delete_user_by_id(user_id: int | str) -> bool:
    with Connect(current_app.config['DATABASE']) as db:
        db.execute(
            "DELETE FROM user WHERE id = ?", (user_id,)
        )
        return True


def fetch_user_by_id(user_id: int | str) -> Optional[User]:
    with Connect(current_app.config['DATABASE']) as db:
        return get_user_model(db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone())


def fetch_user_by_username(username: str) -> Optional[User]:
    with Connect(current_app.config['DATABASE']) as db:
        return get_user_model(db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone())


def fetch_course_by_id(course_id: str) -> Optional[Course]:
    with Connect(current_app.config['DATABASE']) as db:
        return get_course_model(db.execute(
            "SELECT * FROM course WHERE id = ?", (course_id,)
        ).fetchone())


def fetch_course_from_teacher(teacher_id: int | str) -> list[Optional[Course]]:
    with Connect(current_app.config['DATABASE']) as db:
        course = db.execute(
            'SELECT * FROM course where teacher_id = ?',
            (teacher_id,)
        ).fetchall()
    # map 返回的是一个迭代器，只能一次性使用，因此需要转换为 list 以便多次使用
    return list(map(get_course_model, course))


def fetch_course_from_student(student_id: int | str) -> list[Optional[Course]]:
    with Connect(current_app.config['DATABASE']) as db:
        course = db.execute(
            'SELECT * FROM attendance where student_id = ?',
            (student_id,)
        ).fetchall()
    # map 返回的是一个迭代器，只能一次性使用，因此需要转换为 list 以便多次使用
    return list(map(lambda row: fetch_course_by_id(row[1]), course))


def fetch_student_list_from_course(course_id: str) -> list[Optional[User]]:
    with Connect(current_app.config['DATABASE']) as db:
        user = db.execute(
            'SELECT * FROM attendance where course_id = ?',
            (course_id,)
        ).fetchall()
    # map 返回的是一个迭代器，只能一次性使用，因此需要转换为 list 以便多次使用
    return list(map(lambda row: fetch_user_by_id(row[2]), user))


def fetch_attendance_detail_by_student(course_id: str, student_id: int | str) -> Optional[Record]:
    with Connect(current_app.config['DATABASE']) as db:
        record = db.execute(
            'SELECT * FROM attendance where course_id = ? and student_id = ?',
            (course_id, student_id)
        ).fetchone()
    return get_record_model(record)


def fetch_attendance_detail_by_course(course_id: str) -> list[Optional[Record]]:
    with Connect(current_app.config['DATABASE']) as db:
        record = db.execute(
            'SELECT * FROM attendance where course_id = ?',
            (course_id,)
        ).fetchall()
        # map 返回的是一个迭代器，只能一次性使用，因此需要转换为 list 以便多次使用
    return list(map(get_record_model, record))


def fetch_all_admin() -> list[Optional[User]]:
    with Connect(current_app.config['DATABASE']) as db:
        admin = db.execute(
            'SELECT * FROM user WHERE role in (2, 3)'
        ).fetchall()
        # map 返回的是一个迭代器，只能一次性使用，因此需要转换为 list 以便多次使用
    return list(map(get_user_model, admin))


def update_attendance_record(course_id: str, student_id: int | str, new_record: list[Optional[str]]) -> bool:
    old_record = fetch_attendance_detail_by_student(course_id, student_id)
    if old_record is None:
        return False
    with Connect(current_app.config['DATABASE']) as db:
        db.execute(
            'UPDATE attendance SET record = ? WHERE id = ?',
            (json.dumps(new_record), old_record.id)
        )
    return True


def add_course(course_id: str, course_name: str, teacher_id: int | str) -> bool:
    with Connect(current_app.config['DATABASE']) as db:
        db.execute(
            'INSERT INTO course (id, name, teacher_id) VALUES (?, ?, ?)',
            (course_id, course_name, teacher_id)
        )
    return True


def update_course(course_id: str, course_name: str, teacher_id: int | str) -> bool:
    with Connect(current_app.config['DATABASE']) as db:
        course = db.execute(
            'SELECT * FROM course where teacher_id = ?',
            (teacher_id,)
        ).fetchall()
        # 无任何课程，或试图修改的课程不在该教师的课程列表中
        if not course or str(course_id) not in map(lambda x: str(x[2]), course):
            raise RuntimeError
        db.execute(
            'UPDATE course SET name = ? WHERE id = ?',
            (course_name, course_id)
        )
    return True


def delete_course(course_id: str) -> bool:
    with Connect(current_app.config['DATABASE']) as db:
        db.execute(
            'DELETE FROM course where id = ?',
            (course_id,)
        )
        db.execute(
            'DELETE FROM attendance where course_id = ?',
            (course_id,)
        )
    return True


def add_student_to_course(student_id: int | str, course_id: str) -> bool:
    student = fetch_user_by_username(student_id)
    course = fetch_course_by_id(course_id)
    if not student:
        raise RuntimeError(f'学生 {student_id} 不存在')
    if not course:
        raise RuntimeError(f'课程 {course_id}不存在')

    with Connect(current_app.config['DATABASE']) as db:
        db.execute(
            'INSERT INTO attendance (course_id, student_id) VALUES (?, ?)',
            (course_id, student.id)
        )
    return True


def set_nickname(user_id: int | str, nickname: str) -> bool:
    with Connect(current_app.config['DATABASE']) as db:
        db.execute(
            'UPDATE user SET nickname = ? WHERE id = ?',
            (nickname, user_id)
        )
    return True
