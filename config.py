# 环境配置
ENV: str = 'development'
DEBUG: bool = True

# 服务端绑定的地址
PORT: int = 8080
HOST: str = '127.0.0.1'

# 数据库存放路径
DATABASE: str = './data/data.sqlite'

# 临时文件夹存放路径
TEMP: str = './data/temp'

# 学生照片存放路径
PHOTO: str = './data/photo'

# web 后台管理
SECRET_KEY: str = '1145141919810'
SESSION_TYPE: str = 'filesystem'

# 默认管理员账号（初始化时被创建，密码为随机16位，初始化时在日志中显示）
DEFAULT_ADMIN: str = 'superuser'

# 人脸识别阈值（默认 0.4）
THRESHOLD = 0.4
