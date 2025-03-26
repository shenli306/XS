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

class 辣文小说18下载器:
    def __init__(self):
        self.浏览器 = None
        self.progress_callback = None
        self.log_callback = None
        
    def 输出日志(self, 消息, 是否错误=False):
        if self.log_callback:
            self.log_callback(消息, 是否错误)
        else:
            if 是否错误:
                打印错误(消息)
            else:
                打印信息("信息", 消息)
    
    def 搜索小说(self, 搜索关键词):
        try:
            # 创建浏览器实例
            self.浏览器 = 增强web二次封装('edge', 是否无头=True)
            self.浏览器.打开地址('https://www.aaqqcc.com/')
            
            # 执行搜索
            try:
                self.浏览器.输入内容('name', 'keyboard', 搜索关键词)
                self.输出日志("使用keyboard搜索框")
            except:
                try:
                    self.浏览器.输入内容('name', 'searchkey', 搜索关键词)
                    self.输出日志("使用searchkey搜索框")
                except:
                    self.浏览器.输入内容('css', 'input.input', 搜索关键词)
                    self.输出日志("使用通用搜索框")
            
            # 提交搜索
            try:
                self.浏览器.脚本执行("document.querySelector('form.search').submit();")
                self.输出日志("使用表单提交")
            except:
                try:
                    self.浏览器.点击元素('css', 'form.search button[type="submit"]')
                    self.输出日志("点击搜索按钮")
                except:
                    try:
                        self.浏览器.点击元素('xpath', '//input[@type="submit"]')
                        self.输出日志("点击提交按钮")
                    except:
                        self.浏览器.按键('enter')
                        self.输出日志("使用回车键提交")
            
            time.sleep(3)  # 等待搜索结果加载
            
            # 获取搜索结果
            搜索结果页面 = self.浏览器.driver.page_source
            搜索结果soup = BeautifulSoup(搜索结果页面, 'html.parser')
            
            # 收集搜索结果
            所有搜索结果 = []
            
            # 尝试多种可能的搜索结果列表选择器
            结果列表 = 搜索结果soup.select('.novelslist2 li')
            if not 结果列表 or len(结果列表) == 0:
                结果列表 = 搜索结果soup.select('.searchlist .book_list')
            if not 结果列表 or len(结果列表) == 0:
                结果列表 = 搜索结果soup.select('.result-list .result-item')
            if not 结果列表 or len(结果列表) == 0:
                结果列表 = 搜索结果soup.select('li.bookitem')
            if not 结果列表 or len(结果列表) == 0:
                结果列表 = 搜索结果soup.select('.list-item')
            if not 结果列表 or len(结果列表) == 0:
                结果列表 = 搜索结果soup.select('.grid .grid-item')
            if not 结果列表 or len(结果列表) == 0:
                结果列表 = 搜索结果soup.select('.grid-item')
            
            for 小说 in 结果列表:
                # 优先尝试新的搜索结果格式（带图片）
                封面链接元素 = 小说.select_one('a.cover')
                小说名元素 = 小说.select_one('h3 a')
                
                if 封面链接元素 and 小说名元素:
                    # 新格式搜索结果
                    小说链接 = 小说名元素['href']
                    小说名 = 小说名元素.text.strip()
                    作者 = "未知"
                    最新章节 = "未知"
                    简介 = "暂无简介"
                else:
                    # 尝试常规文本链接格式
                    小说名元素 = 小说.select_one('span.s2 a') or 小说.select_one('.book_name a') or 小说.select_one('.name a') or 小说.select_one('a.bookname') or 小说.select_one('a')
                    
                    if 小说名元素:
                        小说名 = 小说名元素.text.strip()
                        小说链接 = 小说名元素['href']
                        
                        # 尝试获取作者信息
                        作者元素 = 小说.select_one('span.s4') or 小说.select_one('.author') or 小说.select_one('.book_author') or 小说.select_one('.info')
                        作者 = 作者元素.text.strip() if 作者元素 else "未知"
                        
                        # 尝试获取最新章节
                        最新章节元素 = 小说.select_one('.update') or 小说.select_one('.latest') or 小说.select_one('.new')
                        最新章节 = 最新章节元素.text.strip() if 最新章节元素 else "未知"
                        
                        # 尝试获取简介
                        简介元素 = 小说.select_one('.intro') or 小说.select_one('.description') or 小说.select_one('.summary')
                        简介 = 简介元素.text.strip() if 简介元素 else "暂无简介"
                
                # 确保链接是完整的
                if not 小说链接.startswith('http'):
                    基础URL = 'https://www.aaqqcc.com'
                    小说链接 = f"{基础URL}{小说链接}" if 小说链接.startswith('/') else f"{基础URL}/{小说链接}"
                
                # 清理简介长度
                简介 = 简介[:50] + "..." if len(简介) > 50 else 简介
                
                所有搜索结果.append((小说名, 小说链接, 作者, 最新章节, 简介))
            
            if not 所有搜索结果:
                self.输出日志("未找到相关小说，请尝试其他关键词", True)
                return []
            
            return 所有搜索结果
            
        except Exception as e:
            self.输出日志(f"搜索小说时出错: {str(e)}", True)
            return []
        finally:
            if self.浏览器:
                self.浏览器.driver.quit()
                self.浏览器 = None
    
    def 下载小说(self, 小说链接, 下载格式="epub"):
        try:
            if not self.浏览器:
                self.浏览器 = 增强web二次封装('edge', 是否无头=True)
            
            self.输出日志(f"开始下载小说，链接：{小说链接}")
            self.浏览器.打开地址(小说链接)
            time.sleep(2)
            
            # 获取小说信息
            详情页源码 = self.浏览器.driver.page_source
            详情soup = BeautifulSoup(详情页源码, 'html.parser')
            
            # 获取书籍区块
            书籍区块 = 详情soup.select_one('section.book')
            if not 书籍区块:
                raise Exception("无法获取书籍信息")
            
            # 获取小说标题
            小说标题 = 书籍区块.select_one('.txt h1').text.strip()
            
            # 获取作者
            作者 = "未知"
            作者元素 = 书籍区块.select_one('.authors dd a')
            if 作者元素:
                作者 = 作者元素.text.strip()
            
            # 获取小说状态
            状态 = "未知"
            状态元素 = 书籍区块.select_one('.status dd')
            if 状态元素:
                状态 = 状态元素.text.strip()
            
            # 获取评分
            评分 = "未知"
            评分元素 = 书籍区块.select_one('.score dd')
            if 评分元素:
                评分 = 评分元素.text.strip()
            
            # 获取肉量
            肉量 = "未知"
            肉量元素 = 书籍区块.select_one('.pornrate dd')
            if 肉量元素:
                肉量 = 肉量元素.text.strip()
            
            # 获取字数
            字数 = "未知"
            字数元素 = 书籍区块.select_one('.wordcount dd')
            if 字数元素:
                字数 = 字数元素.text.strip()
            
            # 获取分类
            分类 = "未知"
            分类元素 = 书籍区块.select_one('.categories dd a')
            if 分类元素:
                分类 = 分类元素.text.strip()
            
            # 获取最新章节
            最新章节 = "未知"
            最新章节元素 = 书籍区块.select_one('.new dd a')
            if 最新章节元素:
                最新章节 = 最新章节元素.text.strip()
            
            # 获取简介
            小说介绍 = "暂无简介"
            简介区块 = 详情soup.select_one('section .book-desc')
            if 简介区块:
                小说介绍 = 简介区块.get_text('\n', strip=True)
            
            # 下载封面图片
            封面链接 = None
            封面元素 = 书籍区块.select_one('.cover img')
            if 封面元素 and 'src' in 封面元素.attrs:
                封面链接 = 封面元素['src']
                if not 封面链接.startswith('http'):
                    封面链接 = f"https://www.aaqqcc.com{封面链接}"
            
            # 创建下载目录
            下载目录 = 'downloads'
            if not os.path.exists(下载目录):
                os.makedirs(下载目录)
            
            小说保存目录 = os.path.join(下载目录, 小说标题)
            if not os.path.exists(小说保存目录):
                os.makedirs(小说保存目录)
            
            # 下载封面图片
            if 封面链接:
                try:
                    封面响应 = requests.get(封面链接, timeout=10)
                    封面响应.raise_for_status()
                    封面路径 = os.path.join(小说保存目录, 'cover.jpg')
                    with open(封面路径, 'wb') as f:
                        f.write(封面响应.content)
                    self.输出日志("封面图片下载成功")
                except Exception as e:
                    self.输出日志(f"下载封面图片失败: {str(e)}", True)
            
            # 保存小说信息
            with open(f'{小说保存目录}/{小说标题}_信息.txt', 'w', encoding='utf-8') as f:
                f.write(f"标题: 《{小说标题}》\n")
                f.write(f"作者: {作者}\n")
                f.write(f"状态: {状态}\n")
                f.write(f"评分: {评分}\n")
                f.write(f"肉量: {肉量}\n")
                f.write(f"字数: {字数}\n")
                f.write(f"分类: {分类}\n")
                f.write(f"最新章节: {最新章节}\n\n")
                f.write("小说简介:\n")
                f.write(小说介绍)
            
            # 获取章节列表
            章节列表元素 = None
            章节区块 = 详情soup.select_one('section .book-chapter')
            if 章节区块:
                章节列表元素 = 章节区块.select('a')
            
            if not 章节列表元素:
                章节列表元素 = 详情soup.select('#list dd a')
            if not 章节列表元素:
                章节列表元素 = 详情soup.select('.listmain dd a')
            if not 章节列表元素:
                章节列表元素 = 详情soup.select('.article-list a')
            if not 章节列表元素:
                章节列表元素 = 详情soup.select('.chapter-list a')
            if not 章节列表元素:
                章节列表元素 = 详情soup.select('.catalog a')
            if not 章节列表元素:
                章节列表元素 = 详情soup.select('.chapters a')
            
            if not 章节列表元素:
                raise Exception("无法获取章节列表")
            
            # 创建章节列表和结果列表
            章节列表 = []
            章节结果 = [None] * len(章节列表元素)  # 预分配固定大小的列表
            
            # 收集所有章节信息
            for i, 章节 in enumerate(章节列表元素):
                章节标题 = 章节.text.strip()
                章节链接 = 章节['href']
                if not 章节链接.startswith('http'):
                    if 章节链接.startswith('/'):
                        章节链接 = f"https://www.aaqqcc.com{章节链接}"
                    else:
                        基础链接 = '/'.join(小说链接.split('/')[:-1])
                        章节链接 = f"{基础链接}/{章节链接}"
                章节列表.append((i, 章节标题, 章节链接))
            
            总章节数 = len(章节列表)
            
            # 创建线程池下载章节
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as 线程池:
                # 提交所有下载任务
                future_to_chapter = {}
                for 序号, 章节标题, 章节链接 in 章节列表:
                    future = 线程池.submit(self.下载单个章节, 序号, 章节标题, 章节链接)
                    future_to_chapter[future] = 序号
                
                # 等待所有任务完成并收集结果
                for future in concurrent.futures.as_completed(future_to_chapter):
                    序号 = future_to_chapter[future]
                    try:
                        章节内容 = future.result()
                        if 章节内容:
                            章节结果[序号] = 章节内容
                            # 更新进度
                            if self.progress_callback:
                                self.progress_callback(序号 + 1, 总章节数)
                    except Exception as e:
                        self.输出日志(f"下载章节 {序号 + 1} 时出错: {str(e)}", True)
            
            # 按顺序保存章节
            小说目录 = []
            for i, 章节内容 in enumerate(章节结果):
                if 章节内容:
                    章节标题, 内容 = 章节内容
                    # 保存章节内容
                    章节文件名 = f"{i:04d}_{章节标题}.txt"
                    with open(f'{小说保存目录}/{章节文件名}', 'w', encoding='utf-8') as f:
                        f.write(f"{章节标题}\n\n")
                        f.write(内容)
                    
                    # 添加到小说目录
                    小说目录.append({"title": 章节标题, "content": 内容})
            
            # 根据选择生成电子书
            if 下载格式 in ["txt", "both"]:
                生成TXT文件(小说标题, 作者, 小说介绍, 小说目录, 小说保存目录)
            
            if 下载格式 in ["epub", "both"]:
                生成EPUB文件(小说标题, 作者, 小说介绍, 小说目录, 小说保存目录, 封面路径 if 封面链接 else None)
            
            self.输出日志(f"下载完成：共 {len(小说目录)} 章")
            return True
            
        except Exception as e:
            self.输出日志(f"下载小说时出错: {str(e)}", True)
            return False
        finally:
            if self.浏览器:
                self.浏览器.driver.quit()
                self.浏览器 = None
    
    def 下载单个章节(self, 序号, 章节标题, 章节链接):
        try:
            # 使用requests获取章节内容，设置正确的编码
            响应 = requests.get(章节链接, timeout=10)
            响应.encoding = 'utf-8'  # 设置响应编码为utf-8
            响应.raise_for_status()
            
            # 使用BeautifulSoup解析内容
            章节soup = BeautifulSoup(响应.text, 'html.parser')
            
            # 尝试多种可能的内容选择器
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
                
                return (章节标题, 内容)
            else:
                self.输出日志(f"无法获取章节 {章节标题} 的内容", True)
                return None
                
        except Exception as e:
            self.输出日志(f"下载章节 {章节标题} 时出错: {str(e)}", True)
            return None

# 修改原有的测试函数
def test_打开辣文小说18首页():
    # 创建下载器实例
    下载器 = 辣文小说18下载器()
    
    # 获取用户输入
    搜索关键词 = input(f"{Fore.YELLOW}请输入要搜索的书籍名称：{Style.RESET_ALL}")
    
    # 执行搜索
    搜索结果 = 下载器.搜索小说(搜索关键词)
    
    if not 搜索结果:
        return
    
    # 显示搜索结果
    打印标题("搜索结果")
    for i, (小说名, 小说链接, 作者, 最新章节, 简介) in enumerate(搜索结果, 1):
        打印信息(f"{i}", f"{小说名} - {作者}")
        打印信息("  最新章节", 最新章节)
        打印信息("  简介", 简介)
        print()
    
    # 选择要下载的小说
    选择索引 = int(input(f"{Fore.YELLOW}请输入要下载的小说编号（1-{len(搜索结果)}）：{Style.RESET_ALL}")) - 1
    
    if 选择索引 < 0 or 选择索引 >= len(搜索结果):
        打印错误("无效的选择")
        return
    
    小说名, 小说链接, 作者, _, _ = 搜索结果[选择索引]
    
    # 询问下载格式
    下载格式 = input(f"{Fore.YELLOW}选择下载格式 (1:TXT, 2:EPUB, 3:两种都要): {Style.RESET_ALL}")
    格式映射 = {"1": "txt", "2": "epub", "3": "both"}
    下载格式 = 格式映射.get(下载格式, "epub")
    
    # 开始下载
    下载器.下载小说(小说链接, 下载格式)

if __name__ == "__main__":
    test_打开辣文小说18首页()

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

def 生成EPUB文件(小说标题, 作者, 小说介绍, 小说目录, 下载目录, 封面路径=None):
    try:
        # 创建EPUB文件
        书 = epub.EpubBook()
        
        # 设置元数据
        书.set_identifier(f'id-{小说标题}')
        书.set_title(小说标题)
        书.set_language('zh-CN')
        书.add_author(作者)
        
        # 添加封面图片
        if 封面路径 and os.path.exists(封面路径):
            with open(封面路径, 'rb') as f:
                封面数据 = f.read()
            封面 = epub.EpubItem(
                uid='cover',
                file_name='cover.jpg',
                media_type='image/jpeg',
                content=封面数据
            )
            书.add_item(封面)
            书.set_cover('cover.jpg', 封面数据)
        
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
            # 使用序号作为文件名前缀，确保正确排序
            c = epub.EpubHtml(
                title=章节['title'],
                file_name=f'chap_{i+1:04d}.xhtml',  # 使用4位数字序号
                lang='zh-CN'
            )
            内容 = 章节['content'].replace("\n", "</p><p>")
            c.content = f'<h2>{章节["title"]}</h2>\n<p>{内容}</p>'
            书.add_item(c)
            epub章节列表.append(c)
        
        # 定义目录，确保按照章节顺序排列
        书.toc = epub章节列表
        
        # 添加NCX和导航文件
        书.add_item(epub.EpubNcx())
        书.add_item(epub.EpubNav())
        
        # 定义书脊，确保按照章节顺序排列
        书.spine = ['nav'] + epub章节列表
        
        # 生成EPUB文件路径
        epub文件路径 = os.path.join(下载目录, f"{小说标题}.epub")
        
        # 写入EPUB文件
        epub.write_epub(epub文件路径, 书, {})
        
        打印成功(f"EPUB文件已生成：{epub文件路径}")
        打印信息("文件大小", f"{os.path.getsize(epub文件路径) / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        打印错误(f"生成EPUB文件时出错: {str(e)}")
