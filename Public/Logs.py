"""
我的项目在运行的过程中，要时刻记录所有的信息，便于我后期追溯问题，排查问题
所以要写一个日志类，记录所有的信息，日志信息写入到本地文件中 保存起来

叫什么名字？ 每天记录一个文件    selenium_2024-11-09.log
存在哪里？  项目下面的Logs文件夹中
什么格式？  
2024-11-09 16:30:30  -----selenium-------  info/error      具体的内容，比如：打开浏览器 耗时5.3秒
2024-11-09 16:31:30  -----selenium-------  info/error      点击name  username元素器 耗时0.53秒

小弟把事情做完了，通过邮件汇报给我就行了。
"""
import os,time
import logging


class  日志记录类:
    def __init__(self):
        # 1. 创建一个logger
        self.logger = logging.getLogger("-----selenium------")
        # 2. 设置日志的级别
        self.logger.setLevel(logging.INFO)
        # 3. 创建一个handler，用于写入日志文件
        # 3.1 创建一个日志文件
        日志文件路径 = os.getcwd()+"/Logs/selenium_" + time.strftime("%Y_%m_%d") + ".log"
        self.file_handler = logging.FileHandler(日志文件路径,encoding="utf-8")
        # 3.2 设置日志的级别
        self.file_handler.setLevel(logging.INFO)
        # 4. 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s  %(message)s')
        self.file_handler.setFormatter(formatter)
        # 5. 给logger添加handler
        self.logger.addHandler(self.file_handler)
        # 6. 控制台也显示日志
        控制台 = logging.StreamHandler()
        控制台.setLevel(logging.INFO)
        控制台.setFormatter(formatter)
        self.logger.addHandler(控制台)
        

    def info(self, msg):
        """记录消息级别"""
        self.logger.info(msg)

    def error(self, msg):
        """记录错误级别"""
        self.logger.error(msg)
