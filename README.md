# <p align="center">基于多人人脸识别的课堂考勤系统设计

## 概要

本项目是一个简单的课堂考勤系统设计，可以用于课堂考勤。仅需将其部署在服务器上即可使用。

## 部署

### 克隆项目

```bash
git clone https://github.com/zhanbao2000/classroom_attendance_face_recognition.git
```

### 下载模型

请在根目录下创建一个名为 `model` 的文件夹，并将模型文件添加到该文件夹中。

你需要在 [davisking/dlib-models](https://github.com/davisking/dlib-models) 下载以下三个模型：

 - [dlib_face_recognition_resnet_model_v1.dat](https://github.com/davisking/dlib-models/raw/master/dlib_face_recognition_resnet_model_v1.dat.bz2)
 - [mmod_human_face_detector.dat](https://github.com/davisking/dlib-models/raw/master/mmod_human_face_detector.dat.bz2)
 - [shape_predictor_68_face_landmarks_GTX.dat](https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks_GTX.dat.bz2)

下载并**解压**后，将这些文件放到 `model` 文件夹中。

### 安装依赖

```bash
cd classroom_attendance_face_recognition
pip install -r requirements.txt
```

### 修改配置文件

本仓库下已经提供了一个默认的 `config.py` 文件，但是不建议在生产环境中直接修改并使用该文件，因为通过 `git` 更新项目时会覆盖掉 `config.py`。

建议在项目根目录下复制一份 `config.py` 为 `config_local.py`，并在 `config_local.py` 中修改相关配置。

###### config_local.py

```python
from config import *

# 定义你需要覆写的配置
# 例如：
# PORT = 8888
```

当服务端检测到有 `config_local.py` 文件时，会优先使用该文件中的配置。

### 启动服务

```bash
python app.py
```
