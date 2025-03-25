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

# 屏蔽警告信息
warnings.filterwarnings("ignore")

# 配置日志，将selenium和其他库的日志级别设置为ERROR或更高
logging.basicConfig(level=logging.ERROR)

# 屏蔽selenium日志
selenium_logger = logging.getLogger('selenium')
selenium_logger.setLevel(logging.ERROR)

# 屏蔽urllib3日志
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.ERROR)

# 初始化colorama
colorama.init(autoreset=True)

# 无头模式设置（True为启用无头模式，False为正常显示浏览器）
无头模式 = True

# 重定向标准错误到空设备
class 错误抑制:
    def __enter__(self):
        self.原始错误输出 = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.close()
        sys.stderr = self.原始错误输出

# 美化打印函数
def 打印标题(文本):
    边框 = "═" * (len(文本) + 4)
    print(f"\n{Fore.CYAN}{边框}")
    print(f"║ {Fore.YELLOW}{Style.BRIGHT}{文本} {Fore.CYAN}║")
    print(f"{边框}{Style.RESET_ALL}\n")

def 打印信息(标签, 内容, 颜色=Fore.GREEN):
    print(f"{Fore.WHITE}{标签}: {颜色}{内容}{Style.RESET_ALL}")

def 打印成功(文本):
    print(f"{Fore.GREEN}✓ {文本}{Style.RESET_ALL}")

def 打印警告(文本):
    print(f"{Fore.YELLOW}⚠ {文本}{Style.RESET_ALL}")
    
def 打印错误(文本):
    print(f"{Fore.RED}✗ {文本}{Style.RESET_ALL}")

def 打印分隔线():
    print(f"{Fore.BLUE}{'─' * 50}{Style.RESET_ALL}")

# 扩展web二次封装类，添加脚本执行和按键方法
class 增强web二次封装(web二次封装):
    def 脚本执行(self, js脚本):
        """执行JavaScript脚本"""
        return self.driver.execute_script(js脚本)
    
    def 按键(self, 键名):
        """模拟键盘按键"""
        from selenium.webdriver.common.keys import Keys
        键位映射 = {
            'enter': Keys.ENTER,
            'tab': Keys.TAB,
            'space': Keys.SPACE,
            'escape': Keys.ESCAPE,
            'esc': Keys.ESCAPE,
        }
        
        元素 = self.driver.switch_to.active_element
        if 键名.lower() in 键位映射:
            元素.send_keys(键位映射[键名.lower()])
        else:
            元素.send_keys(键名)

# 打开辣文小说18+首页
def test_打开辣文小说18首页():
    # 默认使用无头模式
    打印标题("辣文小说18+ 下载器")
    print(f"{Fore.CYAN}使用无头模式启动浏览器...{Style.RESET_ALL}")
    
    # 使用错误抑制上下文管理器屏蔽浏览器启动日志
    with 错误抑制():
        浏览器 = 增强web二次封装('edge', 是否无头=无头模式)
        浏览器.打开地址('https://www.aaqqcc.com/')
    
    # 从终端获取用户输入
    搜索关键词 = input(f"{Fore.YELLOW}请输入要搜索的书籍名称：{Style.RESET_ALL}")
    
    with 错误抑制():
        # 根据网站提供的表单结构更新搜索操作
        try:
            # 尝试新的搜索表单: name="keyboard"
            浏览器.输入内容('name', 'keyboard', 搜索关键词)
            打印信息("搜索方法", "使用keyboard搜索框", Fore.CYAN)
        except:
            try:
                # 尝试旧的搜索方法: name="searchkey"
                浏览器.输入内容('name', 'searchkey', 搜索关键词)
                打印信息("搜索方法", "使用searchkey搜索框", Fore.CYAN)
            except:
                # 尝试通用的搜索框方法
                浏览器.输入内容('css', 'input.input', 搜索关键词)
                打印信息("搜索方法", "使用通用搜索框", Fore.CYAN)
        
        # 尝试点击搜索按钮（有多种可能的方式）
        try:
            # 尝试提交包含搜索框的表单
            浏览器.脚本执行("document.querySelector('form.search').submit();")
            打印信息("搜索提交", "使用表单提交", Fore.CYAN)
        except:
            try:
                # 尝试点击搜索按钮
                浏览器.点击元素('css', 'form.search button[type="submit"]')
                打印信息("搜索提交", "点击搜索按钮", Fore.CYAN)
            except:
                try:
                    # 尝试点击类型为submit的输入元素
                    浏览器.点击元素('xpath', '//input[@type="submit"]')
                    打印信息("搜索提交", "点击提交按钮", Fore.CYAN)
                except:
                    # 使用通用方法处理
                    浏览器.按键('enter')
                    打印信息("搜索提交", "使用回车键提交", Fore.CYAN)
    
    # 等待搜索结果加载
    time.sleep(3)
    
    # 获取搜索结果页面源码
    搜索结果页面 = 浏览器.driver.page_source
    搜索结果soup = BeautifulSoup(搜索结果页面, 'html.parser')
    
    # 首先尝试获取分页信息
    分页信息元素 = 搜索结果soup.select_one('.pagebar')
    有分页 = False
    if 分页信息元素:
        有分页 = True
        打印信息("搜索状态", "检测到多页搜索结果", Fore.CYAN)
    
    # 收集所有搜索结果页面
    所有搜索结果 = []
    
    # 处理当前页面的结果
    def 处理搜索结果页(页面内容):
        页面soup = BeautifulSoup(页面内容, 'html.parser') if isinstance(页面内容, str) else 页面内容
        # 尝试多种可能的搜索结果列表选择器
        结果列表 = 页面soup.select('.novelslist2 li')
        if not 结果列表 or len(结果列表) == 0:
            结果列表 = 页面soup.select('.searchlist .book_list')
        if not 结果列表 or len(结果列表) == 0:
            结果列表 = 页面soup.select('.result-list .result-item')
        if not 结果列表 or len(结果列表) == 0:
            结果列表 = 页面soup.select('li.bookitem')
        if not 结果列表 or len(结果列表) == 0:
            结果列表 = 页面soup.select('.list-item')
        if not 结果列表 or len(结果列表) == 0:
            结果列表 = 页面soup.select('.grid .grid-item')
        if not 结果列表 or len(结果列表) == 0:
            结果列表 = 页面soup.select('.grid-item')
        
        页面小说列表 = []
        for 小说 in 结果列表:
            # 优先尝试新的搜索结果格式（带图片）
            封面链接元素 = 小说.select_one('a.cover')
            小说名元素 = 小说.select_one('h3 a')
            
            if 封面链接元素 and 小说名元素:
                # 新格式搜索结果：使用标题文本而非图片链接
                小说链接 = 小说名元素['href']  # 改用标题链接
                小说名 = 小说名元素.text.strip()
                作者 = "未知"  # 此格式可能没有显示作者
                
                页面小说列表.append((小说名, 小说链接, 作者, "标题链接"))
            else:
                # 尝试常规文本链接格式
                小说名元素 = 小说.select_one('span.s2 a') or 小说.select_one('.book_name a') or 小说.select_one('.name a') or 小说.select_one('a.bookname') or 小说.select_one('a')
                
                if 小说名元素:
                    小说名 = 小说名元素.text.strip()
                    小说链接 = 小说名元素['href']
                    
                    # 尝试获取作者信息
                    作者元素 = 小说.select_one('span.s4') or 小说.select_one('.author') or 小说.select_one('.book_author') or 小说.select_one('.info')
                    作者 = 作者元素.text.strip() if 作者元素 else "未知"
                    
                    页面小说列表.append((小说名, 小说链接, 作者, "文本链接"))
        
        return 页面小说列表
    
    # 处理第一页
    当前页结果 = 处理搜索结果页(搜索结果soup)
    所有搜索结果.extend(当前页结果)
    
    # 如果有分页，抓取前3页（避免过多请求）
    if 有分页:
        # 尝试找到分页链接
        下一页链接 = None
        
        for page_num in range(2, 4):  # 抓取第2、3页
            try:
                # 尝试构建或找到下一页链接
                try:
                    # 方法1：直接查找下一页链接
                    下一页元素 = 搜索结果soup.select_one('.next') or 搜索结果soup.select_one('a:contains("下一页")')
                    if 下一页元素:
                        下一页链接 = 下一页元素['href']
                except:
                    # 方法2：构建下一页链接
                    当前URL = 浏览器.driver.current_url
                    if '?' in 当前URL:
                        基础URL = 当前URL.split('?')[0]
                        下一页链接 = f"{基础URL}?page={page_num}"
                    else:
                        下一页链接 = f"{当前URL}?page={page_num}"
                
                if 下一页链接:
                    # 确保链接完整
                    if not 下一页链接.startswith('http'):
                        基础URL = 'https://www.aaqqcc.com'
                        下一页链接 = f"{基础URL}{下一页链接}" if 下一页链接.startswith('/') else f"{基础URL}/{下一页链接}"
                    
                    # 访问下一页
                    打印信息("分页处理", f"正在获取第{page_num}页搜索结果...", Fore.CYAN)
                    with 错误抑制():
                        浏览器.打开地址(下一页链接)
                        time.sleep(2)  # 等待页面加载
                        下一页源码 = 浏览器.driver.page_source
                        下一页结果 = 处理搜索结果页(下一页源码)
                        所有搜索结果.extend(下一页结果)
            except Exception as e:
                打印警告(f"获取第{page_num}页失败，继续处理已有结果")
                break
    
    # 如果没有找到任何搜索结果
    if not 所有搜索结果:
        # 如果所有选择器都失败，打印页面源码以便调试
        with open('搜索结果页面.html', 'w', encoding='utf-8') as f:
            f.write(搜索结果页面)
        打印错误(f"未找到相关小说，搜索页面已保存到'搜索结果页面.html'，请尝试其他关键词")
        浏览器.driver.quit()
        return
    
    打印标题("搜索结果")
    
    # 显示所有搜索结果
    for i, (小说名, 小说链接, 作者, 链接类型) in enumerate(所有搜索结果, 1):
        if 链接类型 == "标题链接":
            打印信息(f"{i}", f"{小说名} [图文]", Fore.CYAN)
        else:
            打印信息(f"{i}", f"{小说名} - {作者}")
    
    # 选择要下载的小说
    选择索引 = int(input(f"{Fore.YELLOW}请输入要下载的小说编号（1-{len(所有搜索结果)}）：{Style.RESET_ALL}")) - 1
    
    if 选择索引 < 0 or 选择索引 >= len(所有搜索结果):
        打印错误("无效的选择")
        浏览器.driver.quit()
        return
    
    小说名, 小说链接, 作者, 链接类型 = 所有搜索结果[选择索引]
    
    # 确保小说链接是完整的URL
    if not 小说链接.startswith('http'):
        基础URL = 'https://www.aaqqcc.com'
        小说链接 = f"{基础URL}{小说链接}" if 小说链接.startswith('/') else f"{基础URL}/{小说链接}"
    
    # 根据链接类型访问小说详情页
    with 错误抑制():
        if 链接类型 == "标题链接":
            打印信息("链接类型", "标题链接，尝试点击标题文本", Fore.CYAN)
            try:
                # 尝试直接通过XPath定位并点击标题链接
                浏览器.点击元素('xpath', f"//h3/a[contains(text(), '{小说名}')]")
                打印信息("点击方式", "使用标题文本定位", Fore.CYAN)
            except:
                try:
                    # 尝试点击包含小说名的链接（更宽松的匹配）
                    浏览器.点击元素('xpath', f"//a[contains(text(), '{小说名}')]")
                    打印信息("点击方式", "使用一般文本定位", Fore.CYAN)
                except:
                    # 如果点击失败，直接访问链接
                    浏览器.打开地址(小说链接)
                    打印信息("点击方式", "使用直接访问链接", Fore.CYAN)
        else:
            # 文本链接直接访问
            浏览器.打开地址(小说链接)
            打印信息("点击方式", "使用直接访问链接", Fore.CYAN)
        
        time.sleep(2)  # 等待页面加载
    
    # 创建保存目录
    下载目录 = 'downloads'
    if not os.path.exists(下载目录):
        os.makedirs(下载目录)
    
    小说保存目录 = os.path.join(下载目录, 小说名)
    if not os.path.exists(小说保存目录):
        os.makedirs(小说保存目录)
    
    # 获取小说详情页源码
    详情页源码 = 浏览器.driver.page_source
    详情soup = BeautifulSoup(详情页源码, 'html.parser')
    
    # 获取小说信息 - 适配新的HTML结构
    # 尝试从新格式(main.container)中获取信息
    小说标题 = None
    小说介绍 = None

    # 新格式: main.container > section.book 
    书籍区块 = 详情soup.select_one('main.container section.book')
    if 书籍区块:
        # 尝试获取标题
        标题元素 = 书籍区块.select_one('.txt h1')
        if 标题元素:
            小说标题 = 标题元素.text.strip()
            打印信息("解析方式", "使用新的书籍区块格式", Fore.CYAN)
        
        # 尝试获取作者
        作者元素 = 书籍区块.select_one('.authors dd a')
        if 作者元素:
            作者 = 作者元素.text.strip()
    
    # 获取简介
    简介区块 = 详情soup.select_one('section .book-desc')
    if 简介区块:
        小说介绍 = 简介区块.get_text('\n', strip=True)
        打印信息("解析方式", "使用新的简介区块格式", Fore.CYAN)
    
    # 如果新格式无法获取，回退到旧格式
    if not 小说标题:
        小说标题 = 详情soup.select_one('#info h1').text.strip() if 详情soup.select_one('#info h1') else 小说名
        打印信息("解析方式", "使用旧的标题格式", Fore.CYAN)
    
    if not 小说介绍:
        小说介绍元素 = 详情soup.select_one('#intro')
        小说介绍 = 小说介绍元素.text.strip() if 小说介绍元素 else "暂无介绍"
        打印信息("解析方式", "使用旧的简介格式", Fore.CYAN)
    
    # 获取章节列表链接
    章节列表链接 = 浏览器.driver.current_url
    
    # 打印小说信息
    打印标题(f"《{小说标题}》 - 信息")
    打印信息("作者", 作者)
    打印信息("介绍", 小说介绍[:100] + "..." if len(小说介绍) > 100 else 小说介绍)
    
    # 保存小说信息到文件
    with open(f'{小说保存目录}/{小说标题}_信息.txt', 'w', encoding='utf-8') as f:
        f.write(f"标题: 《{小说标题}》\n")
        f.write(f"作者: {作者}\n\n")
        f.write("小说简介:\n")
        f.write(小说介绍)
    
    打印成功(f"小说介绍已保存至：{小说保存目录}/{小说标题}_信息.txt")
    
    # 获取章节列表 - 适配新的HTML结构
    章节列表元素 = None
    
    # 新格式: section > .book-chapter > a
    章节区块 = 详情soup.select_one('section .book-chapter')
    if 章节区块:
        章节列表元素 = 章节区块.select('a')
        if 章节列表元素:
            打印信息("解析方式", "使用新的章节列表格式", Fore.CYAN)
    
    # 如果新格式无法获取，尝试其他格式
    if not 章节列表元素:
        章节列表元素 = 详情soup.select('#list dd a')
        if 章节列表元素:
            打印信息("解析方式", "使用#list dd a格式", Fore.CYAN)
    if not 章节列表元素:
        章节列表元素 = 详情soup.select('.listmain dd a')
        if 章节列表元素:
            打印信息("解析方式", "使用.listmain dd a格式", Fore.CYAN)
    if not 章节列表元素:
        章节列表元素 = 详情soup.select('.article-list a')
        if 章节列表元素:
            打印信息("解析方式", "使用.article-list a格式", Fore.CYAN)
    if not 章节列表元素:
        章节列表元素 = 详情soup.select('.chapter-list a')
        if 章节列表元素:
            打印信息("解析方式", "使用.chapter-list a格式", Fore.CYAN)
    if not 章节列表元素:
        章节列表元素 = 详情soup.select('.catalog a')
        if 章节列表元素:
            打印信息("解析方式", "使用.catalog a格式", Fore.CYAN)
    if not 章节列表元素:
        章节列表元素 = 详情soup.select('.chapters a')
        if 章节列表元素:
            打印信息("解析方式", "使用.chapters a格式", Fore.CYAN)
    
    if not 章节列表元素:
        # 尝试直接查找所有a标签，可能需要过滤
        所有链接 = 详情soup.select('a')
        章节列表元素 = []
        for a in 所有链接:
            href = a.get('href', '')
            # 识别可能的章节链接模式
            if re.search(r'\/\d+\.html$|\/\d+\/$|chapter|chap|read|content', href):
                章节列表元素.append(a)
        if 章节列表元素:
            打印信息("解析方式", "使用智能章节匹配", Fore.YELLOW)
        
    if not 章节列表元素:
        # 如果还是找不到章节列表，可能需要点击"章节目录"或类似按钮
        try:
            # 尝试点击章节列表按钮
            浏览器.点击元素('xpath', '//a[contains(text(), "章节") or contains(text(), "目录") or contains(text(), "列表")]')
            time.sleep(2)  # 等待章节列表加载
            # 重新获取页面内容
            详情页源码 = 浏览器.driver.page_source
            详情soup = BeautifulSoup(详情页源码, 'html.parser')
            # 再次尝试获取章节列表
            章节列表元素 = 详情soup.select('#list dd a') or 详情soup.select('.listmain dd a') or 详情soup.select('.chapter-list a')
            if 章节列表元素:
                打印信息("解析方式", "点击章节目录后获取", Fore.CYAN)
        except:
            pass
    
    if not 章节列表元素:
        # 如果所有尝试都失败，保存页面源码以便调试
        with open(f'{小说保存目录}/详情页面.html', 'w', encoding='utf-8') as f:
            f.write(详情页源码)
        打印错误(f"无法获取章节列表，详情页已保存到'{小说保存目录}/详情页面.html'")
        浏览器.driver.quit()
        return
    
    章节总数 = len(章节列表元素)
    打印信息("章节总数", str(章节总数))
    
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
    
    # 创建章节下载队列
    章节队列 = Queue()
    小说目录 = []
    
    for i in range(开始章节, 结束章节):
        章节 = 章节列表元素[i]
        章节标题 = 章节.text.strip()
        章节链接 = 章节['href']
        # 构建完整的章节链接
        if not 章节链接.startswith('http'):
            if 章节链接.startswith('/'):
                章节链接 = f"https://www.aaqqcc.com{章节链接}"
            else:
                基础链接 = '/'.join(章节列表链接.split('/')[:-1])
                章节链接 = f"{基础链接}/{章节链接}"
        章节队列.put((i + 1, 章节标题, 章节链接))
    
    # 询问下载格式
    下载格式 = input(f"{Fore.YELLOW}选择下载格式 (1:TXT, 2:EPUB, 3:两种都要): {Style.RESET_ALL}")
    
    # 章节下载函数
    def 下载章节(任务队列, 结果列表, 浏览器会话):
        while not 任务队列.empty():
            try:
                序号, 章节标题, 章节链接 = 任务队列.get(block=False)
                
                尝试次数 = 0
                最大尝试次数 = 3
                成功 = False
                
                while 尝试次数 < 最大尝试次数 and not 成功:
                    try:
                        # 使用requests获取章节内容
                        响应 = 浏览器会话.get(章节链接, timeout=10)
                        响应.raise_for_status()
                        
                        # 使用BeautifulSoup解析内容
                        章节soup = BeautifulSoup(响应.text, 'html.parser')
                        
                        # 优先尝试新的内容元素布局(article.content)
                        内容元素 = 章节soup.select_one('article.content')
                        
                        if not 内容元素:
                            内容元素 = 章节soup.select_one('#content')
                        if not 内容元素:
                            内容元素 = 章节soup.select_one('.content')
                        if not 内容元素:
                            内容元素 = 章节soup.select_one('.article-content')
                        if not 内容元素:
                            内容元素 = 章节soup.select_one('.chapter-content')
                        if not 内容元素:
                            内容元素 = 章节soup.select_one('.read-content')
                        if not 内容元素:
                            内容元素 = 章节soup.select_one('.text')
                        
                        if 内容元素:
                            # 去除广告和脚本
                            for 脚本 in 内容元素.select('script'):
                                脚本.decompose()
                            for 广告 in 内容元素.select('.ads, .ad, ins, iframe'):
                                广告.decompose()
                            
                            # 获取文本并清理
                            内容 = 内容元素.get_text('\n', strip=True)
                            内容 = re.sub(r'\n+', '\n\n', 内容)  # 规范化换行
                            内容 = re.sub(r'(https?://[^\s]+)', '', 内容)  # 移除URL
                            
                            # 移除常见广告文本
                            广告词列表 = [
                                "笔趣阁", "本章未完，请点击下一页继续阅读", "手机阅读", 
                                "天才一秒记住", "全文阅读", "添加书签", "投推荐票",
                                "请记住本站域名", "最新章节", "请关注", "精彩小说网",
                                "章节目录", "加入书签", "点击下载", "手机版访问",
                                "访问下载", "本站网址", "手机请访问", "请牢记",
                                "免费阅读", "请收藏本站", "手机阅读器",
                                "本站永久域名", "aaqqcc.com", "请加入收藏", "方便下次访问"
                            ]
                            
                            for 广告词 in 广告词列表:
                                内容 = 内容.replace(广告词, "")
                            
                            # 使用正则表达式移除更多广告文本
                            内容 = re.sub(r'(www\.[a-zA-Z0-9]+\.[a-z]+)', '', 内容)
                            内容 = re.sub(r'([a-zA-Z0-9]+\.com)', '', 内容)
                            内容 = re.sub(r'([a-zA-Z0-9]+\.net)', '', 内容)
                            内容 = re.sub(r'([a-zA-Z0-9]+\.org)', '', 内容)
                            
                            # 移除特定格式的广告语句
                            内容 = re.sub(r'本站永久域名[：:].*?方便下次访问', '', 内容)
                            内容 = re.sub(r'请记住本站域名[：:].*?$', '', 内容, flags=re.MULTILINE)
                            内容 = re.sub(r'.*?永久网址[：:].*?$', '', 内容, flags=re.MULTILINE)
                            
                            # 移除开头和结尾的空行
                            内容 = 内容.strip()
                            
                            # 保存章节
                            结果列表.append((序号, 章节标题, 内容))
                            成功 = True
                        else:
                            尝试次数 += 1
                            time.sleep(1)
                    except Exception as e:
                        尝试次数 += 1
                        time.sleep(2)
                
                if not 成功:
                    print(f"{Fore.RED}下载章节 {章节标题} 失败{Style.RESET_ALL}")
                
                任务队列.task_done()
            except Exception:
                break
    
    # 下载所有章节
    打印标题("开始下载章节")
    
    # 创建复制的队列用于显示进度
    进度队列 = Queue()
    原始大小 = 章节队列.qsize()
    for _ in range(原始大小):
        item = 章节队列.get()
        章节队列.put(item)
        进度队列.put(item)
    
    # 创建进度条
    进度条 = tqdm(total=原始大小, desc="下载进度", unit="章")
    
    # 创建一个线程来更新进度条
    def 更新进度条():
        已完成 = 0
        总数 = 进度队列.qsize()
        
        while 已完成 < 总数:
            剩余任务 = 章节队列.qsize()
            新完成 = 总数 - 剩余任务 - 已完成
            if 新完成 > 0:
                进度条.update(新完成)
                已完成 += 新完成
            time.sleep(0.5)
    
    进度线程 = threading.Thread(target=更新进度条)
    进度线程.daemon = True
    进度线程.start()
    
    # 使用线程池下载章节
    线程数 = min(10, 原始大小)  # 最多10个线程
    下载结果 = []
    
    with requests.Session() as 会话:
        # 设置会话头信息
        会话.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        下载线程列表 = []
        for _ in range(线程数):
            线程 = threading.Thread(target=下载章节, args=(章节队列, 下载结果, 会话))
            线程.daemon = True
            线程.start()
            下载线程列表.append(线程)
        
        # 等待所有章节下载完成
        章节队列.join()
    
    # 关闭进度条
    进度条.close()
    
    # 对结果按章节序号排序
    下载结果.sort(key=lambda x: x[0])
    
    # 构建小说目录
    for 序号, 标题, 内容 in 下载结果:
        小说目录.append({"title": 标题, "content": 内容})
    
    打印成功(f"下载完成：共 {len(小说目录)} 章")
    
    # 根据选择生成电子书
    if 下载格式 in ["1", "3"]:
        生成TXT文件(小说标题, 作者, 小说介绍, 小说目录, 小说保存目录)
    
    if 下载格式 in ["2", "3"]:
        生成EPUB文件(小说标题, 作者, 小说介绍, 小说目录, 小说保存目录)
    
    打印标题("下载任务已完成")
    
    # 关闭浏览器
    浏览器.driver.quit()

def 生成TXT文件(小说标题, 作者, 小说介绍, 小说目录, 下载目录):
    # 生成TXT文件路径
    txt文件路径 = os.path.join(下载目录, f"{小说标题}.txt")
    
    # 写入TXT文件
    with open(txt文件路径, 'w', encoding='utf-8') as f:
        # 写入标题和作者
        f.write(f"{小说标题}\n")
        f.write(f"作者：{作者}\n\n")
        
        # 写入简介
        f.write("【简介】\n")
        f.write(f"{小说介绍}\n\n")
        
        # 写入正文
        f.write("【正文】\n\n")
        
        for 章节 in 小说目录:
            f.write(f"{章节['title']}\n\n")
            f.write(f"{章节['content']}\n\n")
            f.write("\n" + "=" * 50 + "\n\n")  # 分隔线
    
    打印成功(f"TXT文件已生成：{txt文件路径}")
    打印信息("文件大小", f"{os.path.getsize(txt文件路径) / 1024 / 1024:.2f} MB")

def 生成EPUB文件(小说标题, 作者, 小说介绍, 小说目录, 下载目录):
    # 创建EPUB文件
    书 = epub.EpubBook()
    
    # 设置元数据
    书.set_identifier(f'id-{小说标题}')
    书.set_title(小说标题)
    书.set_language('zh-CN')
    书.add_author(作者)
    
    # 添加CSS样式
    样式 = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: SimSun, serif;
        line-height: 1.6;
        padding: 5%;
    }
    h1, h2 {
        text-align: center;
        font-weight: bold;
    }
    p {
        text-indent: 2em;
        margin: 0.5em 0;
    }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=样式)
    书.add_item(nav_css)
    
    # 创建简介章节
    简介章节 = epub.EpubHtml(title='简介', file_name='intro.xhtml', lang='zh-CN')
    简介章节.content = f'<h1>{小说标题}</h1>\n<p>作者：{作者}</p>\n<h2>简介</h2>\n<p>{小说介绍.replace("\n", "</p><p>")}</p>'
    书.add_item(简介章节)
    
    # 创建章节
    epub章节列表 = [简介章节]
    for i, 章节 in enumerate(小说目录):
        c = epub.EpubHtml(title=章节['title'], file_name=f'chap_{i+1}.xhtml', lang='zh-CN')
        内容 = 章节['content'].replace("\n", "</p><p>")
        c.content = f'<h2>{章节["title"]}</h2>\n<p>{内容}</p>'
        书.add_item(c)
        epub章节列表.append(c)
    
    # 定义目录
    书.toc = epub章节列表
    
    # 添加NCX和导航文件
    书.add_item(epub.EpubNcx())
    书.add_item(epub.EpubNav())
    
    # 定义书脊
    书.spine = ['nav'] + epub章节列表
    
    # 生成EPUB文件路径
    epub文件路径 = os.path.join(下载目录, f"{小说标题}.epub")
    
    # 写入EPUB文件
    epub.write_epub(epub文件路径, 书, {})
    
    打印成功(f"EPUB文件已生成：{epub文件路径}")
    打印信息("文件大小", f"{os.path.getsize(epub文件路径) / 1024 / 1024:.2f} MB")
