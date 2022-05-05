from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str
    nickname: str
    password: str
    role: int


class Course(BaseModel):
    id: str
    name: str
    teacher_id: int
    teacher_nickname: str  # 姓名，User 类的 nickname


class Record(BaseModel):
    id: int
    student_username: str  # 学号
    student_nickname: str  # 姓名，User 类的 nickname
    attendance: list[Optional[str]]
