import os
from enum import Enum, auto
from typing import Optional

import dlib
import numpy as np
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config_local import PHOTO
from data_model import User

# 载入所有模型
detector = dlib.get_frontal_face_detector()  # HOG+SVM
# detector = dlib.cnn_face_detection_model_v1('model/mmod_human_face_detector.dat')  # CNN+MMOD
sp = dlib.shape_predictor('model/shape_predictor_68_face_landmarks_GTX.dat')
facerec = dlib.face_recognition_model_v1('model/dlib_face_recognition_resnet_model_v1.dat')


class AttendanceStatus(Enum):
    UNKNOWN = auto()  # 未知，例如学生没有提交照片
    PRESENT = auto()  # 出勤
    ABSENT = auto()  # 缺勤
    # UNEXCUSED_ABSENCE = auto()  # 无故缺勤
    # EXCUSED_ABSENCE = auto()  # 请假
    # LATE = auto()  # 迟到
    # LEFT_EARLY = auto()  # 早退


def check_attendance(student_list: list[User], photo_path: str, threshold=0.4) -> list[AttendanceStatus]:
    unknown_face_descriptors = []
    student_face_descriptors = load_face_descriptors(student_list)

    # 读取待识别图片中的人脸
    img = dlib.load_rgb_image(photo_path)
    unknown_faces = detector(img, 1)
    for face in unknown_faces:
        shape = sp(img, face)
        face_descriptor = facerec.compute_face_descriptor(img, shape)
        unknown_face_descriptors.append(face_descriptor)

    return compare_faces(student_face_descriptors, unknown_face_descriptors, threshold=threshold)


def load_face_descriptors(student_list: list[User]) -> list[Optional[np.ndarray]]:
    result = []
    for student in student_list:
        # 载入numpy数组
        npy_path = os.path.join(PHOTO, f'{student.username}.npy')
        if os.path.isfile(npy_path):
            student_face_descriptor = np.load(npy_path)
        else:
            student_face_descriptor = None
        result.append(student_face_descriptor)

    return result


def save_student_photo(student_username: str, file: FileStorage) -> str:
    filename = secure_filename(file.filename)
    suffix = filename.rsplit('.', 1)[1]
    save_path = os.path.join(PHOTO, f'{student_username}.{suffix}')
    file.save(save_path)
    return save_path


def save_student_face_descriptor(student_username: str, photo_path: str) -> bool:
    student_image = dlib.load_rgb_image(photo_path)
    student_face = detector(student_image, 1)[0]
    shape = sp(student_image, student_face)  # HOG+SVM
    # shape = sp(student_image, student_face.rect)  # CNN+MMOD
    student_face_descriptor = facerec.compute_face_descriptor(student_image, shape)
    np.save(os.path.join(PHOTO, f'{student_username}.npy'), student_face_descriptor)
    return True


def compare_faces(
        student_face_descriptors: list[Optional[np.ndarray]],
        unknown_face_descriptors: list[np.ndarray],
        threshold=0.4
) -> list[AttendanceStatus]:
    result = []
    for student_face_descriptor in student_face_descriptors:
        if student_face_descriptor is None:
            result.append(AttendanceStatus.UNKNOWN)
            continue
        for unknown_face_descriptor in unknown_face_descriptors:
            distance = np.linalg.norm(student_face_descriptor - unknown_face_descriptor)
            if distance < threshold:
                result.append(AttendanceStatus.PRESENT)
                break
        else:
            result.append(AttendanceStatus.ABSENT)

    return result
