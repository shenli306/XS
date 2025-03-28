from Public.Base import web二次封装
import time
import pytest
import requests
import os
from bs4 import BeautifulSoup
import threading
from queue import Queue
import concurrent.futures
import re
import shutil
from ebooklib import epub
import colorama
from colorama import Fore, Back, Style
from tqdm import tqdm
import logging
import sys
import warnings
import uuid

# 屏蔽警告信息
warnings.filterwarnings("ignore")

# 配置日志，将selenium和其他库的日志级别设置为ERROR或更高
logging.basicConfig(level=logging.ERROR, format='%(message)s')

# 屏蔽selenium日志
selenium_logger = logging.getLogger('selenium')
selenium_logger.setLevel(logging.ERROR)
selenium_logger.propagate = False

# 屏蔽urllib3日志
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.ERROR)
urllib3_logger.propagate = False

# 创建自定义日志记录器
novel_logger = logging.getLogger('novel_downloader')
novel_logger.setLevel(logging.INFO)
novel_logger.propagate = False

# 清除所有处理器
for handler in novel_logger.handlers[:]:
    novel_logger.removeHandler(handler)

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(message)s'))
novel_logger.addHandler(console_handler)

# 初始化colorama
colorama.init(autoreset=True)

# 无头模式设置（True为启用无头模式，False为正常显示浏览器）
无头模式 = True

# 浏览器类定义
class 浏览器类:
    def __init__(self):
        self.driver = None
        self.browser = None
    
    def 启动浏览器(self):
        # 使用web二次封装创建浏览器实例
        self.browser = web二次封装('edge', 是否无头=True)
        self.driver = self.browser.driver
    
    def 打开地址(self, 地址):
        self.browser.打开地址(地址)
    
    def 输入内容(self, 定位方式, 定位值, 内容):
        self.browser.输入内容(定位方式, 定位值, 内容)
    
    def 点击元素(self, 定位方式, 定位值):
        self.browser.点击元素(定位方式, 定位值)
    
    def 关闭浏览器(self):
        if self.browser:
            self.browser.关闭浏览器()
            
    def execute_cdp_cmd(self, cmd, params):
        if self.driver:
            return self.driver.execute_cdp_cmd(cmd, params)

class 万书屋下载器:
    def __init__(self):
        self.浏览器 = None
        # 使用绝对路径作为下载目录
        self.下载目录 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'downloads')
        if not os.path.exists(self.下载目录):
            os.makedirs(self.下载目录)
        # 初始化日志回调
        self.log_callback = None
        self.progress_callback = None
        # 初始化时创建浏览器实例
        try:
            self.浏览器 = 浏览器类()
            self.浏览器.启动浏览器()
            # 设置忽略SSL证书错误
            self.浏览器.execute_cdp_cmd('Security.setIgnoreCertificateErrors', {'ignore': True})
            # 设置忽略SSL错误
            self.浏览器.execute_cdp_cmd('Network.setBypassServiceWorker', {'bypass': True})
        except Exception as e:
            self.输出日志(f"初始化浏览器失败: {str(e)}", True)
            raise
    
    def __del__(self):
        # 类销毁时关闭浏览器
        if self.浏览器:
            try:
                self.浏览器.关闭浏览器()
            except Exception as e:
                self.输出日志(f"关闭浏览器失败: {str(e)}", True)
    
    def 输出日志(self, 消息, 是否错误=False):
        try:
            if self.log_callback:
                self.log_callback(消息, 是否错误)
            else:
                if 是否错误:
                    novel_logger.error(f"{Fore.RED}{消息}{Style.RESET_ALL}")
                else:
                    novel_logger.info(消息)
        except Exception as e:
            print(f"日志输出失败: {str(e)}")
    
    def 搜索小说(self, 搜索关键词):
        try:
            if not self.浏览器:
                raise Exception("浏览器未初始化")
                
            self.输出日志(f"开始搜索小说：{搜索关键词}")
            
            # 使用已存在的浏览器实例
            self.浏览器.打开地址('https://www.rrssk.com/?165')
            time.sleep(2)  # 等待页面加载
            
            self.浏览器.输入内容('class','input', 搜索关键词)
            self.浏览器.点击元素('class','btnSearch')
            time.sleep(2)  # 等待搜索结果加载
    
            # 获取搜索结果页面源码
            搜索结果页面 = self.浏览器.driver.page_source
            if not 搜索结果页面:
                raise Exception("获取页面源码失败")
                
            搜索结果soup = BeautifulSoup(搜索结果页面, 'html.parser')
    
            # 获取搜索结果列表
            搜索结果列表 = 搜索结果soup.select('.list.dList > ul > li')
            if not 搜索结果列表:
                搜索结果列表 = 搜索结果soup.select('.book-img-text .bookbox')
            if not 搜索结果列表:
                搜索结果列表 = 搜索结果soup.select('.result-list .result-item')
            if not 搜索结果列表:
                搜索结果列表 = 搜索结果soup.select('.books-list .books-item')
            if not 搜索结果列表:
                搜索结果列表 = 搜索结果soup.select('li.cc')
            if not 搜索结果列表:
                搜索结果列表 = 搜索结果soup.select('.novelslist2 li')
            if not 搜索结果列表:
                搜索结果列表 = 搜索结果soup.select('.conList .info')
            if not 搜索结果列表:
                搜索结果列表 = 搜索结果soup.select('.blue.btnBlue2')

            if not 搜索结果列表:
                self.输出日志("未找到任何搜索结果", True)
                return []

            # 处理搜索结果
            所有搜索结果 = []
            for 小说元素 in 搜索结果列表:
                try:
                    # 尝试获取小说名和链接
                    小说名元素 = (小说元素.select_one('.txtb .name a') or
                             小说元素.select_one('.name.font18 a') or
                             小说元素.select_one('h3 a') or 
                             小说元素.select_one('h4 a') or 
                             小说元素.select_one('.bookname a') or 
                             小说元素.select_one('a.blue') or
                             小说元素.select_one('.s2 a') or
                             小说元素.select_one('.name a') or
                             小说元素.select_one('a[title]'))
                    
                    if 小说名元素:
                        小说名 = 小说名元素.text.strip()
                        小说链接 = 小说名元素['href']
                        
                        # 尝试获取作者
                        作者元素 = (小说元素.select_one('.info dl:first-child dd a') or 
                                小说元素.select_one('.dlS dd a') or
                                小说元素.select_one('.author') or 
                                小说元素.select_one('.bookauthor') or
                                小说元素.select_one('.s4') or
                                小说元素.select_one('.info .author'))
                        作者 = 作者元素.text.strip() if 作者元素 else "未知"
                        
                        # 尝试获取最新章节
                        最新章节元素 = 小说元素.select_one('.info dl:last-child dd a')
                        最新章节 = 最新章节元素.text.strip() if 最新章节元素 else "未知"
                        
                        # 尝试获取简介
                        简介元素 = 小说元素.select_one('.intro')
                        简介 = 简介元素.text.strip() if 简介元素 else "暂无简介"
                        简介 = 简介[:50] + "..." if len(简介) > 50 else 简介
                        
                        # 清理小说名和作者
                        小说名 = 小说名.replace("[在线阅读]", "").strip()
                        if "作者：" in 作者:
                            作者 = 作者.replace("作者：", "").strip()
                        
                        # 确保链接是完整的
                        if not 小说链接.startswith('http'):
                            基础URL = 'https://www.shuwuwan.com'
                            小说链接 = f"{基础URL}{小说链接}" if 小说链接.startswith('/') else f"{基础URL}/{小说链接}"
                        
                        # 清理链接中的日志信息
                        小说链接 = 小说链接.split(',')[0].strip()  # 移除逗号后的所有内容
                        小说链接 = 小说链接.split('耗时')[0].strip()  # 移除"耗时"后的所有内容
                        
                        所有搜索结果.append((小说名, 小说链接, 作者, 最新章节, 简介))
                        self.输出日志(f"找到小说：{小说名} - {作者}")
                except Exception as e:
                    self.输出日志(f"处理搜索结果时出错：{str(e)}", True)
                    continue

            if not 所有搜索结果:
                self.输出日志("未能成功解析任何搜索结果", True)
            else:
                self.输出日志(f"共找到 {len(所有搜索结果)} 个搜索结果")
                
            return 所有搜索结果
            
        except Exception as e:
            self.输出日志(f"搜索小说时出错：{str(e)}", True)
            return []
    
    def 下载小说(self, 小说链接, 下载格式="epub"):
        try:
            if not self.浏览器:
                raise Exception("浏览器未初始化")
                
            self.输出日志(f"开始下载小说，链接：{小说链接}")
            
            # 使用已存在的浏览器实例
            self.浏览器.打开地址(小说链接)
            time.sleep(2)  # 等待页面加载
            
            # 获取小说信息
            页面源码 = self.浏览器.driver.page_source
            if not 页面源码:
                raise Exception("获取页面源码失败")
                
            soup = BeautifulSoup(页面源码, 'html.parser')
            
            # 获取小说标题
            小说标题元素 = soup.select_one('.conL .txtb .tit .name')
            if not 小说标题元素:
                小说标题元素 = soup.select_one('.book-info h1')
            if not 小说标题元素:
                小说标题元素 = soup.select_one('.book-title')
            if not 小说标题元素:
                小说标题元素 = soup.select_one('.book-name')
            if not 小说标题元素:
                raise Exception("无法获取小说标题")
            小说标题 = 小说标题元素.text.strip()
            
            # 获取作者
            作者元素 = soup.select_one('.conL .txtb .tit .author a')
            if not 作者元素:
                作者元素 = soup.select_one('.book-info .author')
            if not 作者元素:
                作者元素 = soup.select_one('.book-author')
            if not 作者元素:
                作者元素 = soup.select_one('.author-name')
            if not 作者元素:
                raise Exception("无法获取作者信息")
            作者 = 作者元素.text.strip()
            
            # 获取小说介绍
            小说介绍元素 = soup.select_one('.conL .txtb .intro')
            if not 小说介绍元素:
                小说介绍元素 = soup.select_one('.book-info .intro')
            if not 小说介绍元素:
                小说介绍元素 = soup.select_one('.book-description')
            if not 小说介绍元素:
                小说介绍元素 = soup.select_one('.book-intro')
            if not 小说介绍元素:
                raise Exception("无法获取小说介绍")
            小说介绍 = 小说介绍元素.text.strip()
            
            self.输出日志(f"获取到小说信息：《{小说标题}》 作者：{作者}")
            
            # 下载封面图片
            try:
                封面元素 = soup.select_one('.picb .pic img')
                if not 封面元素:
                    封面元素 = soup.select_one('.book-img img')
                if not 封面元素:
                    封面元素 = soup.select_one('.book-cover img')
                if not 封面元素:
                    封面元素 = soup.select_one('.novel-cover img')
                
                if 封面元素 and 封面元素.get('src'):
                    封面URL = 封面元素['src']
                    if not 封面URL.startswith('http'):
                        基础URL = 'https://www.shuwuwan.com'
                        封面URL = f"{基础URL}{封面URL}"
                    
                    # 下载封面图片
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(封面URL, headers=headers, verify=False)
                    if response.status_code == 200:
                        封面路径 = f'{self.下载目录}/{小说标题}_封面.jpg'
                        with open(封面路径, 'wb') as f:
                            f.write(response.content)
                        self.输出日志("封面图片下载成功")
                    else:
                        self.输出日志("封面图片下载失败：HTTP状态码不为200", True)
            except Exception as e:
                self.输出日志(f"下载封面失败：{str(e)}", True)
            
            # 获取章节列表
            章节列表元素 = soup.select('.chapterList .list ul li .name a')
            if not 章节列表元素:
                章节列表元素 = soup.select('.conL .txtb .list ul li a')
            if not 章节列表元素:
                章节列表元素 = soup.select('.chapter-list li a')
            if not 章节列表元素:
                章节列表元素 = soup.select('.book-chapter-list li a')
            if not 章节列表元素:
                章节列表元素 = soup.select('.novel-chapter-list li a')
            if not 章节列表元素:
                章节列表元素 = soup.select('.chapter a')
            
            if not 章节列表元素:
                raise Exception("无法获取章节列表")
                
            self.输出日志(f"获取到 {len(章节列表元素)} 个章节")
            
            # 创建章节列表并排序
            章节列表 = []
            for 章节 in 章节列表元素:
                章节名 = 章节.text.strip()
                章节链接 = 章节['href']
                if not 章节链接.startswith('http'):
                    章节链接 = f"https://www.shuwuwan.com{章节链接}"
                
                # 从URL中提取章节号
                try:
                    章节号 = int(章节链接.split('-')[-1].replace('.html', ''))
                except:
                    章节号 = len(章节列表) + 1
                章节列表.append((章节号, 章节名, 章节链接))
            
            # 按章节号排序
            章节列表.sort(key=lambda x: x[0])
            
            # 创建小说内容目录
            小说章节目录 = f'{self.下载目录}/{小说标题}_章节'
            if not os.path.exists(小说章节目录):
                os.makedirs(小说章节目录)
            
            # 下载章节内容
            成功下载章节数 = 0
            总章节数 = len(章节列表)
            
            for idx, (章节号, 章节名, 章节链接) in enumerate(章节列表):
                try:
                    self.浏览器.打开地址(章节链接)
                    time.sleep(0.5)  # 等待页面加载
                    
                    章节页面源码 = self.浏览器.driver.page_source
                    章节soup = BeautifulSoup(章节页面源码, 'html.parser')
                    章节内容元素 = 章节soup.select_one('#content')
                    
                    if 章节内容元素:
                        章节内容 = 章节内容元素.text.strip()
                        
                        # 清理章节内容
                        章节内容 = 清理章节内容(章节内容)
                        
                        # 保存章节内容
                        章节文件名 = f"{章节号:04d}_{章节名}.txt"
                        with open(f'{小说章节目录}/{章节文件名}', 'w', encoding='utf-8') as f:
                            f.write(f"{章节名}\n\n")
                            f.write(章节内容)
                        
                        成功下载章节数 += 1
                        
                        # 发送进度信号
                        if hasattr(self, 'progress_callback'):
                            self.progress_callback(idx + 1, 总章节数)
                        
                except Exception as e:
                    self.输出日志(f"下载章节 {章节名} 失败：{str(e)}", True)
                    continue
            
            # 检查是否成功下载了足够的章节
            if 成功下载章节数 == 0:
                raise Exception("未能成功下载任何章节")
            
            self.输出日志(f"成功下载 {成功下载章节数}/{总章节数} 个章节")
            
            # 根据选择的格式生成文件
            if 下载格式.lower() == "txt":
                生成TXT文件(小说标题, 作者, 小说介绍, 小说章节目录, self.下载目录)
            else:
                生成EPUB文件(小说标题, 作者, 小说介绍, 小说章节目录, self.下载目录)
            
            # 验证文件是否成功生成
            目标文件 = f'{self.下载目录}/{小说标题}.{"txt" if 下载格式.lower() == "txt" else "epub"}'
            if not os.path.exists(目标文件):
                raise Exception(f"未能成功生成{下载格式.upper()}文件")
            
            self.输出日志(f"小说下载完成：{目标文件}")
            return True
            
        except Exception as e:
            self.输出日志(f"下载小说时出错：{str(e)}", True)
            return False

# 清理章节内容函数
def 清理章节内容(章节内容):
    # 清理章节内容
    章节内容 = 章节内容.replace('    ', '\n\n')
    
    # 清洗内容 - 保留万书屋专用广告清理
    需要移除的内容 = [
        "(http://www.shuwuwan.com/book/F72W-1.html)",
        "章节错误,点此举报(免注册)我们会尽快处理.举报后请耐心等待,并刷新页面。",
        "请记住本书首发域名：http://www.shuwuwan.com",
        "www.shuwuwan.com",
        "shuwuwan.com",
        "书屋湾",
        "首发域名",
        "章节错误",
        "点此举报",
        "免注册",
        "耐心等待",
        "刷新页面"
    ]
    
    for 广告内容 in 需要移除的内容:
        章节内容 = 章节内容.replace(广告内容, "")
    
    # 清理章节末尾的URL
    章节内容 = re.sub(r'https?://[^\s<>"]+|www\.[^\s<>"]+', '', 章节内容)
    章节内容 = re.sub(r'[a-zA-Z0-9-]+\.html', '', 章节内容)
    
    # 1. 移除广告和无用内容 - 采用完本阁的方式
    章节内容 = re.sub(r'[（(].{1,30}[)）]', '', 章节内容)  # 移除括号中的广告
    章节内容 = re.sub(r'.*www.*\n?', '', 章节内容)  # 移除包含www的行
    章节内容 = re.sub(r'.*http.*\n?', '', 章节内容)  # 移除包含http的行
    章节内容 = re.sub(r'.*投票推荐.*\n?', '', 章节内容)  # 移除投票推荐
    章节内容 = re.sub(r'.*加入书签.*\n?', '', 章节内容)  # 移除加入书签
    章节内容 = re.sub(r'.*留言反馈.*\n?', '', 章节内容)  # 移除留言反馈
    章节内容 = re.sub(r'.*催更报错.*\n?', '', 章节内容)  # 移除催更报错
    
    # 清理所有类型的括号及其内容 - 保留万书屋的这部分处理
    章节内容 = re.sub(r'\([^)]*\)', '', 章节内容)  # 清理英文括号
    章节内容 = re.sub(r'（[^）]*）', '', 章节内容)  # 清理中文括号
    章节内容 = re.sub(r'【[^】]*】', '', 章节内容)  # 清理中文方括号
    章节内容 = re.sub(r'\[[^\]]*\]', '', 章节内容)  # 清理英文方括号
    章节内容 = re.sub(r'「[^」]*」', '', 章节内容)  # 清理中文书名号
    章节内容 = re.sub(r'『[^』]*』', '', 章节内容)  # 清理中文双书名号
    
    # 清理单个括号
    章节内容 = re.sub(r'[\(（【\[「『]', '', 章节内容)  # 清理左括号
    章节内容 = re.sub(r'[\)）】\]」』]', '', 章节内容)  # 清理右括号
    
    # 清理多余的空行和空格
    章节内容 = re.sub(r'\n\s*\n\s*\n+', '\n\n', 章节内容)  # 清理多余空行
    章节内容 = re.sub(r'[ \t]+', ' ', 章节内容)  # 清理多余空格
    章节内容 = re.sub(r'\n\s+', '\n', 章节内容)  # 清理行首空格
    章节内容 = re.sub(r'\s+\n', '\n', 章节内容)  # 清理行尾空格
    
    # 清理等号分隔线
    章节内容 = re.sub(r'=+', '', 章节内容)
    
    # 清理章节内容首尾的空白字符
    章节内容 = 章节内容.strip()
    
    # 2. 分段处理 - 完全采用完本阁的方式
    paragraphs = []
    # 按照换行符分割文本
    lines = [line.strip() for line in 章节内容.split('\n') if line.strip()]
    
    current_paragraph = []
    for line in lines:
        # 跳过导航相关的行
        if any(skip in line for skip in ['返回书页', '加入书签', '投票推荐', '催更报错', '留言反馈']):
            continue
            
        # 如果是对话或者很短的句子，单独成段
        if (line.startswith('"') or line.startswith('"') or 
            line.startswith('「') or line.startswith('『') or
            len(line) < 15):  # 短句独立成段
            if current_paragraph:
                paragraphs.append(''.join(current_paragraph))
                current_paragraph = []
            paragraphs.append(line)
        else:
            # 如果当前行以句号、问号、感叹号等结尾，说明是段落结束
            if any(line.endswith(end) for end in ['。', '！', '？', '…', '!', '?', '..."', '"']):
                current_paragraph.append(line)
                paragraphs.append(''.join(current_paragraph))
                current_paragraph = []
            else:
                current_paragraph.append(line)
    
    # 处理最后一个段落
    if current_paragraph:
        paragraphs.append(''.join(current_paragraph))
    
    # 构建最终文本 - 为TXT格式添加缩进
    final_text = []
    for p in paragraphs:
        if p.strip():  # 确保段落不是空的
            # 处理对话段落的缩进
            if (p.startswith('"') or p.startswith('"') or 
                p.startswith('「') or p.startswith('『')):
                final_text.append(f'    {p}')
            else:
                final_text.append(f'    {p}')
            
    return '\n\n'.join(final_text)  # 段落之间用两个换行符分隔

# 重定向标准错误到空设备
class 错误抑制:
    def __enter__(self):
        self.原始错误输出 = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.close()
        sys.stderr = self.原始错误输出

# 修改打印函数
def 打印标题(文本, 日志回调=None):
    边框 = "═" * (len(文本) + 4)
    消息 = f"\n{边框}\n║ {文本} ║\n{边框}\n"
    if 日志回调:
        日志回调(消息, False)
    else:
        print(f"\n{Fore.CYAN}{边框}")
        print(f"║ {Fore.YELLOW}{Style.BRIGHT}{文本} {Fore.CYAN}║")
        print(f"{边框}{Style.RESET_ALL}\n")

def 打印信息(标签, 内容, 颜色=Fore.GREEN, 日志回调=None):
    消息 = f"{标签}: {内容}"
    if 日志回调:
        日志回调(消息, False)
    else:
        print(f"{Fore.WHITE}{标签}: {颜色}{内容}{Style.RESET_ALL}")

def 打印成功(文本, 日志回调=None):
    消息 = f"✓ {文本}"
    if 日志回调:
        日志回调(消息, False)
    else:
        print(f"{Fore.GREEN}✓ {文本}{Style.RESET_ALL}")

def 打印警告(文本, 日志回调=None):
    消息 = f"⚠ {文本}"
    if 日志回调:
        日志回调(消息, False)
    else:
        print(f"{Fore.YELLOW}⚠ {文本}{Style.RESET_ALL}")
    
def 打印错误(文本, 日志回调=None):
    消息 = f"✗ {文本}"
    if 日志回调:
        日志回调(消息, True)
    else:
        print(f"{Fore.RED}✗ {文本}{Style.RESET_ALL}")

def 打印分隔线(日志回调=None):
    分隔线 = "─" * 50
    if 日志回调:
        日志回调(分隔线, False)
    else:
        print(f"{Fore.BLUE}{分隔线}{Style.RESET_ALL}")

#打开万书屋首页
def test_打开万书屋首页():
    # 默认使用无头模式
    打印标题("万书屋小说下载器")
    
    # 创建下载目录
    下载目录 = 'downloads'
    if not os.path.exists(下载目录):
        os.makedirs(下载目录)
        
    # 创建浏览器实例
    浏览器 = 浏览器类()
    浏览器.启动浏览器()
    
    try:
        # 访问万书屋首页
        浏览器.打开地址('https://www.rrssk.com/?165')
        time.sleep(2)  # 等待页面加载
        
        # 获取搜索框并输入关键词
        搜索关键词 = input(f"{Fore.YELLOW}请输入要搜索的小说名称：{Style.RESET_ALL}")
        浏览器.输入内容('class','input', 搜索关键词)
        浏览器.点击元素('class','btnSearch')
        time.sleep(2)  # 等待搜索结果加载
        
        # 获取搜索结果页面源码
        搜索结果页面 = 浏览器.driver.page_source
        搜索结果soup = BeautifulSoup(搜索结果页面, 'html.parser')
        
        # 获取搜索结果列表
        所有搜索结果 = []
        搜索结果列表 = 搜索结果soup.select('.list.dList > ul > li')
        if not 搜索结果列表:
            搜索结果列表 = 搜索结果soup.select('.book-img-text .bookbox')
        if not 搜索结果列表:
            搜索结果列表 = 搜索结果soup.select('.result-list .result-item')
        if not 搜索结果列表:
            搜索结果列表 = 搜索结果soup.select('.books-list .books-item')
        if not 搜索结果列表:
            搜索结果列表 = 搜索结果soup.select('li.cc')
        if not 搜索结果列表:
            搜索结果列表 = 搜索结果soup.select('.novelslist2 li')
        if not 搜索结果列表:
            搜索结果列表 = 搜索结果soup.select('.conList .info')
        if not 搜索结果列表:
            搜索结果列表 = 搜索结果soup.select('.blue.btnBlue2')
        
        # 处理搜索结果
        for 小说元素 in 搜索结果列表:
            try:
                # 尝试获取小说名和链接
                小说名元素 = (小说元素.select_one('.txtb .name a') or
                         小说元素.select_one('.name.font18 a') or
                         小说元素.select_one('h3 a') or 
                         小说元素.select_one('h4 a') or 
                         小说元素.select_one('.bookname a') or 
                         小说元素.select_one('a.blue') or
                         小说元素.select_one('.s2 a') or
                         小说元素.select_one('.name a') or
                         小说元素.select_one('a[title]'))
                
                if 小说名元素:
                    小说名 = 小说名元素.text.strip()
                    小说链接 = 小说名元素['href']
                    
                    # 尝试获取作者
                    作者元素 = (小说元素.select_one('.info dl:first-child dd a') or 
                            小说元素.select_one('.dlS dd a') or
                            小说元素.select_one('.author') or 
                            小说元素.select_one('.bookauthor') or
                            小说元素.select_one('.s4') or
                            小说元素.select_one('.info .author'))
                    作者 = 作者元素.text.strip() if 作者元素 else "未知"
                    
                    # 尝试获取最新章节
                    最新章节元素 = 小说元素.select_one('.info dl:last-child dd a')
                    最新章节 = 最新章节元素.text.strip() if 最新章节元素 else "未知"
                    
                    # 尝试获取简介
                    简介元素 = 小说元素.select_one('.intro')
                    简介 = 简介元素.text.strip() if 简介元素 else "暂无简介"
                    简介 = 简介[:50] + "..." if len(简介) > 50 else 简介
                    
                    # 清理小说名和作者
                    小说名 = 小说名.replace("[在线阅读]", "").strip()
                    if "作者：" in 作者:
                        作者 = 作者.replace("作者：", "").strip()
                    
                    # 确保链接是完整的
                    if not 小说链接.startswith('http'):
                        基础URL = 'https://www.shuwuwan.com'
                        小说链接 = f"{基础URL}{小说链接}" if 小说链接.startswith('/') else f"{基础URL}/{小说链接}"
                    
                    所有搜索结果.append((小说名, 小说链接, 作者, 最新章节, 简介))
            except Exception as e:
                print(f"处理搜索结果时出错：{str(e)}")
                continue
        
        # 如果没有找到任何搜索结果
        if not 所有搜索结果:
            打印错误("未找到相关小说，请尝试其他关键词")
            浏览器.关闭浏览器()
            return
        
        打印标题("搜索结果")
        
        # 显示所有搜索结果
        for i, (小说名, 小说链接, 作者, 最新章节, 简介) in enumerate(所有搜索结果, 1):
            打印信息(f"{i}", f"{小说名} - {作者}")
            打印信息("  最新章节", 最新章节)
            打印信息("  简介", 简介)
            print()

        # 选择要下载的小说
        选择索引 = int(input(f"{Fore.YELLOW}请输入要下载的小说编号（1-{len(所有搜索结果)}）：{Style.RESET_ALL}")) - 1

        if 选择索引 < 0 or 选择索引 >= len(所有搜索结果):
            打印错误("无效的选择")
            浏览器.关闭浏览器()
            return

        小说名, 小说链接, 作者, _, _ = 所有搜索结果[选择索引]

        # 访问选择的小说详情页
        with 错误抑制():
            浏览器.打开地址(小说链接)
            time.sleep(1)  # 等待页面加载

        # 获取当前页面URL
        小说页面URL = 浏览器.driver.current_url

        # 获取页面HTML内容
        页面源码 = 浏览器.driver.page_source
        soup = BeautifulSoup(页面源码, 'html.parser')

        # 获取小说信息
        小说标题 = soup.select_one('.conL .txtb .tit .name').text.strip()
        作者 = soup.select_one('.conL .txtb .tit .author a').text.strip()
        小说介绍 = soup.select_one('.conL .txtb .intro').text.strip()
        
        # 打印小说信息
        打印标题(f"《{小说标题}》 - 信息")
        打印信息("作者", 作者)
        打印信息("介绍", 小说介绍[:100] + "..." if len(小说介绍) > 100 else 小说介绍)
        
        # 保存小说信息到文件
        with open(f'{下载目录}/{小说标题}_信息.txt', 'w', encoding='utf-8') as f:
            f.write(f"标题: 《{小说标题}》\n")
            f.write(f"作者: {作者}\n")
            f.write(f"简介：\n{小说介绍}\n")
        
        打印成功(f"小说介绍已保存至：{下载目录}/{小说标题}_信息.txt")
        
        # 获取所有章节列表
        所有章节列表 = []
        打印标题("获取章节列表")

        # 创建小说内容目录
        小说章节目录 = f'{下载目录}/{小说标题}_章节'
        if not os.path.exists(小说章节目录):
            os.makedirs(小说章节目录)
        
        # 获取章节列表
        章节列表元素 = soup.select('.chapterList .list ul li .name a')
        if not 章节列表元素:
            章节列表元素 = soup.select('.conL .txtb .list ul li a')
        if not 章节列表元素:
            章节列表元素 = soup.select('.chapter-list li a')
        if not 章节列表元素:
            章节列表元素 = soup.select('.book-chapter-list li a')
        if not 章节列表元素:
            章节列表元素 = soup.select('.novel-chapter-list li a')
        if not 章节列表元素:
            章节列表元素 = soup.select('.chapter a')
        
        if not 章节列表元素:
            打印错误("无法获取章节列表")
            浏览器.关闭浏览器()
            return
        
        章节总数 = len(章节列表元素)
        打印信息("总章节数", 章节总数)
        
        # 询问下载范围
        下载方式 = input(f"{Fore.YELLOW}选择下载方式 (1:全本下载, 2:自定义范围): {Style.RESET_ALL}")
        
        开始章节 = 0
        结束章节 = 章节总数
        
        if 下载方式 == "2":
            开始章节 = int(input(f"{Fore.YELLOW}请输入起始章节 (1-{章节总数}): {Style.RESET_ALL}")) - 1
            结束章节 = int(input(f"{Fore.YELLOW}请输入结束章节 (1-{章节总数}): {Style.RESET_ALL}"))
            
            if 开始章节 < 0:
                开始章节 = 0
            if 结束章节 > 章节总数:
                结束章节 = 章节总数
        
        # 询问下载格式
        格式选择 = input(f"{Fore.YELLOW}选择下载格式 (1:TXT, 2:EPUB): {Style.RESET_ALL}")
        
        # 创建进度条
        with tqdm(total=结束章节-开始章节, desc="下载进度", unit="章",
                 bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL)) as 进度条:
            下载结果 = []
            
            # 下载章节内容
            for i in range(开始章节, 结束章节):
                章节 = 章节列表元素[i]
                章节名 = 章节.text.strip()
                章节链接 = 章节['href']
                
                # 构建完整的章节链接
                if not 章节链接.startswith('http'):
                    章节链接 = f"https://www.shuwuwan.com{章节链接}"
                
                try:
                    # 访问章节页面
                    浏览器.打开地址(章节链接)
                    time.sleep(0.5)  # 等待页面加载
                    
                    # 获取章节内容
                    章节页面源码 = 浏览器.driver.page_source
                    章节soup = BeautifulSoup(章节页面源码, 'html.parser')
                    章节内容元素 = 章节soup.select_one('#content')
                    
                    if 章节内容元素:
                        章节内容 = 章节内容元素.text.strip()
                        
                        # 清理章节内容
                        章节内容 = 清理章节内容(章节内容)
                        
                        # 保存章节内容
                        章节文件名 = f"{i+1:04d}_{章节名}.txt"
                        with open(f'{小说章节目录}/{章节文件名}', 'w', encoding='utf-8') as f:
                            f.write(f"{章节名}\n\n")
                            f.write(章节内容)
                        
                        下载结果.append(True)
                    else:
                        下载结果.append(False)
                except Exception as e:
                    下载结果.append(False)
                # 无论成功失败，都只更新进度条，不打印具体信息
                进度条.update(1)
            
            进度条.close()
            
            # 计算下载成功的章节数
            成功数量 = sum(下载结果)
            打印分隔线()
            打印成功(f"章节下载完成！成功：{成功数量}/{len(下载结果)}")
            
            # 创建完整小说文件
            print(f"{Fore.CYAN}正在生成完整小说文件...{Style.RESET_ALL}")
            
            # 根据用户选择的格式生成对应文件
            if 格式选择 == "1":  # TXT格式
                生成TXT文件(小说标题, 作者, 小说介绍, 小说章节目录, 下载目录)
            else:  # EPUB格式（默认）
                生成EPUB文件(小说标题, 作者, 小说介绍, 小说章节目录, 下载目录)
    
    except Exception as e:
        打印错误(f"获取小说信息出错：{e}")
        import traceback
        traceback.print_exc()

    finally:
        with 错误抑制():
            浏览器.关闭浏览器()

# 生成TXT格式小说文件
def 生成TXT文件(小说标题, 作者, 小说介绍, 小说章节目录, 下载目录):
    try:
        # 生成TXT文件路径
        txt_文件路径 = f'{下载目录}/{小说标题}.txt'
        
        # 检查是否已存在同名文件，如果存在则先删除
        if os.path.exists(txt_文件路径):
            try:
                os.remove(txt_文件路径)
                print(f"{Fore.YELLOW}已删除旧的TXT文件{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}删除旧文件失败: {e}{Style.RESET_ALL}")
                return False
        
        # 检查章节目录是否存在
        if not os.path.exists(小说章节目录):
            print(f"{Fore.RED}章节目录不存在: {小说章节目录}{Style.RESET_ALL}")
            return False
            
        # 检查章节文件是否存在
        章节文件列表 = sorted([f for f in os.listdir(小说章节目录) if f.endswith('.txt')],
                      key=lambda x: int(x.split('_')[0]))
        if not 章节文件列表:
            print(f"{Fore.RED}未找到任何章节文件{Style.RESET_ALL}")
            return False
        
        # 添加进度条
        with tqdm(total=len(章节文件列表), desc="生成TXT文件", unit="章",
                 bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL)) as pbar:
            with open(txt_文件路径, 'w', encoding='utf-8') as f:
                # 写入小说信息
                f.write(f"《{小说标题}》\n")
                f.write(f"作者：{作者}\n")
                f.write("\n简介：\n")
                f.write(小说介绍 + "\n\n")
                f.write("=" * 50 + "\n\n")
                
                # 写入章节内容
                总字数 = 0
                总章节数 = 0
                for 章节文件 in 章节文件列表:
                    try:
                        with open(f'{小说章节目录}/{章节文件}', 'r', encoding='utf-8') as 章节f:
                            章节内容 = 章节f.read()
                            章节名 = 章节内容.split('\n')[0]  # 第一行是章节名
                            章节正文 = '\n'.join(章节内容.split('\n')[2:])  # 跳过标题和空行
                            
                            # 写入章节标题
                            f.write(f"\n{章节名}\n")
                            f.write("-" * len(章节名) + "\n\n")
                            
                            # 使用完本阁的分段处理逻辑
                            paragraphs = []
                            # 按照换行符分割文本
                            lines = [line.strip() for line in 章节正文.split('\n') if line.strip()]
                            
                            current_paragraph = []
                            for line in lines:
                                # 跳过导航相关的行
                                if any(skip in line for skip in ['返回书页', '加入书签', '投票推荐', '催更报错', '留言反馈']):
                                    continue
                                    
                                # 如果是对话或者很短的句子，单独成段
                                if (line.startswith('"') or line.startswith('"') or 
                                    line.startswith('「') or line.startswith('『') or
                                    len(line) < 15):  # 短句独立成段
                                    if current_paragraph:
                                        paragraphs.append(''.join(current_paragraph))
                                        current_paragraph = []
                                    paragraphs.append(line)
                                else:
                                    # 如果当前行以句号、问号、感叹号等结尾，说明是段落结束
                                    if any(line.endswith(end) for end in ['。', '！', '？', '…', '!', '?', '..."', '"']):
                                        current_paragraph.append(line)
                                        paragraphs.append(''.join(current_paragraph))
                                        current_paragraph = []
                                    else:
                                        current_paragraph.append(line)
                            
                            # 处理最后一个段落
                            if current_paragraph:
                                paragraphs.append(''.join(current_paragraph))
                            
                            # 写入段落
                            for p in paragraphs:
                                if p.strip():  # 确保段落不是空的
                                    # 处理对话段落的缩进
                                    if (p.startswith('"') or p.startswith('"') or 
                                        p.startswith('「') or p.startswith('『')):
                                        f.write(f"    {p}\n\n")
                                    else:
                                        f.write(f"    {p}\n\n")
                            
                            # 统计字数
                            章节字数 = len(章节正文.replace('\n', '').replace(' ', ''))
                            总字数 += 章节字数
                            总章节数 += 1
                    except Exception as e:
                        print(f"{Fore.RED}处理章节 {章节文件} 时出错: {e}{Style.RESET_ALL}")
                        continue
                    finally:
                        pbar.update(1)
        
        if 总章节数 == 0:
            print(f"{Fore.RED}生成TXT文件失败：未能写入任何章节{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.GREEN}已生成TXT文件：{txt_文件路径}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}总章节数: {Fore.CYAN}{总章节数}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}总字数: {Fore.CYAN}{总字数} 字{Style.RESET_ALL}")
        print(f"{Fore.CYAN}下载完成{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}生成TXT文件时出错: {str(e)}{Style.RESET_ALL}")
        if os.path.exists(txt_文件路径):
            try:
                os.remove(txt_文件路径)
            except:
                pass
        return False

# 生成EPUB格式小说文件
def 生成EPUB文件(小说标题, 作者, 小说介绍, 小说章节目录, 下载目录):
    try:
        # 生成EPUB文件路径
        epub_文件路径 = f'{下载目录}/{小说标题}.epub'
        
        # 检查是否已存在同名文件，如果存在则先删除
        if os.path.exists(epub_文件路径):
            try:
                os.remove(epub_文件路径)
                print(f"{Fore.YELLOW}已删除旧的EPUB文件{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}删除旧文件失败: {e}{Style.RESET_ALL}")
                return False
        
        # 检查章节目录是否存在
        if not os.path.exists(小说章节目录):
            print(f"{Fore.RED}章节目录不存在: {小说章节目录}{Style.RESET_ALL}")
            return False
            
        # 检查章节文件是否存在
        章节文件列表 = sorted([f for f in os.listdir(小说章节目录) if f.endswith('.txt')],
                      key=lambda x: int(x.split('_')[0]))
        if not 章节文件列表:
            print(f"{Fore.RED}未找到任何章节文件{Style.RESET_ALL}")
            return False
        
        # 创建EPUB书籍
        book = epub.EpubBook()
        
        # 设置元数据
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(小说标题)
        book.set_language('zh-CN')
        book.add_author(作者)
        
        # 添加封面图片
        封面路径 = f'{下载目录}/{小说标题}_封面.jpg'
        if os.path.exists(封面路径):
            try:
                with open(封面路径, 'rb') as f:
                    book.set_cover("cover.jpg", f.read())
                print(f"{Fore.GREEN}✓ 已添加封面图片{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}添加封面失败: {e}{Style.RESET_ALL}")
        
        # 添加CSS样式
        style = '''
            @namespace epub "http://www.idpf.org/2007/ops";
            body {
                font-family: "Noto Serif CJK SC", "Source Han Serif SC", SimSun, serif;
                margin: 5%;
                text-align: justify;
            }
            h1 {
                text-align: center;
                color: #333;
                margin: 2em 0 1em;
                font-weight: bold;
                font-size: 1.5em;
            }
            p {
                text-indent: 2em;
                line-height: 1.8;
                margin: 0.8em 0;
                font-size: 1.1em;
            }
            .dialogue {
                text-indent: 0;
                margin: 0.5em 1em;
            }
            .chapter-content {
                margin-top: 2em;
            }
        '''
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        book.add_item(nav_css)
        
        # 添加简介章节
        intro_chapter = epub.EpubHtml(title='简介', file_name='intro.xhtml', lang='zh-CN')
        # 处理简介内容，确保正确分段
        简介内容 = 小说介绍.replace('\n\n', '</p><p>')  # 将双换行转换为段落
        简介内容 = 简介内容.replace('\n', '</p><p>')    # 将单换行转换为段落
        intro_chapter.content = f'<h1>简介</h1><p>{简介内容}</p>'
        intro_chapter.add_item(nav_css)
        book.add_item(intro_chapter)
        
        # 添加章节
        chapters = []
        总字数 = 0
        总章节数 = 0
        
        # 添加进度条
        with tqdm(total=len(章节文件列表), desc="生成EPUB文件", unit="章",
                 bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL)) as pbar:
            for 章节文件 in 章节文件列表:
                try:
                    with open(f'{小说章节目录}/{章节文件}', 'r', encoding='utf-8') as f:
                        章节内容 = f.read()
                        章节名 = 章节内容.split('\n')[0]  # 第一行是章节名
                        章节正文 = '\n'.join(章节内容.split('\n')[2:])  # 跳过标题和空行
                        
                        # 创建章节
                        chapter = epub.EpubHtml(
                            title=章节名,
                            file_name=f'chapter_{len(chapters)+1}.xhtml',
                            lang='zh-CN'
                        )
                        
                        # 使用完本阁的分段处理逻辑
                        paragraphs = []
                        # 按照换行符分割文本
                        lines = [line.strip() for line in 章节正文.split('\n') if line.strip()]
                        
                        current_paragraph = []
                        for line in lines:
                            # 跳过导航相关的行
                            if any(skip in line for skip in ['返回书页', '加入书签', '投票推荐', '催更报错', '留言反馈']):
                                continue
                                
                            # 如果是对话或者很短的句子，单独成段
                            if (line.startswith('"') or line.startswith('"') or 
                                line.startswith('「') or line.startswith('『') or
                                len(line) < 15):  # 短句独立成段
                                if current_paragraph:
                                    paragraphs.append(''.join(current_paragraph))
                                    current_paragraph = []
                                paragraphs.append(line)
                            else:
                                # 如果当前行以句号、问号、感叹号等结尾，说明是段落结束
                                if any(line.endswith(end) for end in ['。', '！', '？', '…', '!', '?', '..."', '"']):
                                    current_paragraph.append(line)
                                    paragraphs.append(''.join(current_paragraph))
                                    current_paragraph = []
                                else:
                                    current_paragraph.append(line)
                        
                        # 处理最后一个段落
                        if current_paragraph:
                            paragraphs.append(''.join(current_paragraph))
                        
                        # 格式化HTML
                        formatted_content = []
                        for p in paragraphs:
                            if p.strip():  # 确保段落不是空的
                                # 处理对话段落的缩进
                                if (p.startswith('"') or p.startswith('"') or 
                                    p.startswith('「') or p.startswith('『')):
                                    formatted_content.append(f'<p class="dialogue">{p}</p>')
                                else:
                                    formatted_content.append(f'<p>{p}</p>')
                        
                        content = '\n'.join(formatted_content)
                        
                        if not content:
                            raise ValueError("章节内容为空")
                            
                        # 将处理后的内容转换为HTML
                        chapter.content = f'''<html>
                        <head></head>
                        <body>
                            <h1>{章节名}</h1>
                            <div class="chapter-content">
                                {content}
                            </div>
                        </body>
                        </html>'''
                        chapter.add_item(nav_css)
                        book.add_item(chapter)
                        chapters.append(chapter)
                        
                        # 统计字数
                        章节字数 = len(章节正文.replace('\n', '').replace(' ', ''))
                        总字数 += 章节字数
                        总章节数 += 1
                except Exception as e:
                    print(f"{Fore.RED}处理章节 {章节文件} 时出错: {e}{Style.RESET_ALL}")
                    continue
                finally:
                    pbar.update(1)
        
        if 总章节数 == 0:
            print(f"{Fore.RED}生成EPUB文件失败：未能写入任何章节{Style.RESET_ALL}")
            return False
        
        # 创建目录
        book.toc = [(epub.Section('简介'), [intro_chapter])]
        book.toc.extend(chapters)
        
        # 设置spine
        book.spine = ['nav', intro_chapter] + chapters
        
        # 添加默认的NCX和Nav文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 生成epub文件
        epub.write_epub(epub_文件路径, book, {})
        
        print(f"{Fore.GREEN}已生成EPUB文件：{epub_文件路径}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}总章节数: {Fore.CYAN}{总章节数}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}总字数: {Fore.CYAN}{总字数} 字{Style.RESET_ALL}")
        print(f"{Fore.CYAN}下载完成{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}生成EPUB文件时出错: {str(e)}{Style.RESET_ALL}")
        if os.path.exists(epub_文件路径):
            try:
                os.remove(epub_文件路径)
            except:
                pass
        return False

