DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS attendance;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nickname TEXT NOT NULL,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role INTEGER NOT NULL  -- 0: 学生, 1: 教师, 2: 管理员, 3: 超级管理员
);

CREATE TABLE course (
  id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  teacher_id INTEGER NOT NULL  -- user.id 的无约束外键
);

CREATE TABLE attendance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL,  -- course.id 的无约束外键
  student_id INTEGER NOT NULL,  -- user.id 的无约束外键
  record TEXT NOT NULL DEFAULT '[]' -- json
);
