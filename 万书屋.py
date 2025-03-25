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

#打开万书屋首页
def test_打开万书屋首页():
    # 默认使用无头模式
    打印标题("万书屋小说下载器")
    print(f"{Fore.CYAN}使用无头模式启动浏览器...{Style.RESET_ALL}")
    
    # 使用错误抑制上下文管理器屏蔽浏览器启动日志
    with 错误抑制():
        浏览器=web二次封装('edge', 是否无头=True)
        浏览器.打开地址('https://www.rrssk.com/?165')
    
    # 从终端获取用户输入
    搜索关键词 = input(f"{Fore.YELLOW}请输入要搜索的书籍名称：{Style.RESET_ALL}")
    
    with 错误抑制():
        浏览器.输入内容('class','input',搜索关键词)
        浏览器.点击元素('class','btnSearch')
        # 不要立即点击第一个结果，而是显示所有搜索结果
        # 浏览器.点击元素('class','btnBlue2')
    
    # 创建保存目录 - 修改为downloads
    下载目录 = 'downloads'
    if not os.path.exists(下载目录):
        os.makedirs(下载目录)
    
    # 获取搜索结果页面源码
    搜索结果页面 = 浏览器.driver.page_source
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
    # 万书屋特定的选择器
    if not 搜索结果列表:
        搜索结果列表 = 搜索结果soup.select('.novelslist2 li')
    if not 搜索结果列表:
        搜索结果列表 = 搜索结果soup.select('.conList .info')
    if not 搜索结果列表:
        搜索结果列表 = 搜索结果soup.select('.blue.btnBlue2')
    if not 搜索结果列表:
        # 如果实在找不到结果，记录页面以便分析
        with open('搜索结果页面.html', 'w', encoding='utf-8') as f:
            f.write(搜索结果页面)
        # 记录日志但尝试直接点击第一个结果
        打印警告(f"无法找到搜索结果列表，尝试直接点击第一个结果")
        try:
            with 错误抑制():
                浏览器.点击元素('class', 'btnBlue2')
                time.sleep(1)  # 等待页面加载
                # 获取当前页面URL和内容
                小说页面URL = 浏览器.driver.current_url
                页面源码 = 浏览器.driver.page_source
                soup = BeautifulSoup(页面源码, 'html.parser')
                # 继续原来的流程
                打印警告(f"已自动选择第一个搜索结果")
                # 获取小说标题
                小说标题 = soup.select_one('.conL .txtb .tit .name').text.strip()
                # 获取作者
                作者 = soup.select_one('.conL .txtb .tit .author a').text.strip()
                # 从这里继续原代码流程
                # 跳过搜索结果显示和用户选择部分
                return
        except Exception as e:
            打印错误(f"尝试点击第一个结果失败：{e}")
            打印错误(f"未找到相关小说，搜索页面已保存到'搜索结果页面.html'")
            浏览器.关闭浏览器()
            exit()

    # 如果找到了搜索结果列表但是为空
    if len(搜索结果列表) == 0:
        打印错误(f"搜索结果为空，请尝试其他关键词")
        浏览器.关闭浏览器()
        exit()

    # 尝试获取搜索结果总数信息
    搜索结果总数 = "未知"
    搜索结果信息 = 搜索结果soup.select_one('.rankIBox.searchIBox .tit .name')
    if 搜索结果信息:
        搜索结果文本 = 搜索结果信息.text.strip()
        总数匹配 = re.search(r'为您找到 .*?(\d+).*? 个', 搜索结果文本)
        if 总数匹配:
            搜索结果总数 = 总数匹配.group(1)

    打印成功(f"找到 {len(搜索结果列表)} 个搜索结果，总共约 {搜索结果总数} 个结果")

    # 处理搜索结果
    所有搜索结果 = []
    for 小说元素 in 搜索结果列表:
        try:
            # 尝试获取小说名和链接 - 万书屋特定的选择器
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
                打印信息("检测到小说", f"{小说名} - {作者}", Fore.CYAN)
        except Exception as e:
            打印警告(f"处理搜索结果时出错：{str(e)}")
            continue

    # 如果没有找到任何搜索结果
    if not 所有搜索结果:
        打印错误(f"未找到相关小说，请尝试其他关键词")
        浏览器.关闭浏览器()
        exit()

    打印标题("搜索结果")

    # 显示所有搜索结果
    for i, (小说名, 小说链接, 作者, 最新章节, 简介) in enumerate(所有搜索结果, 1):
        打印信息(f"{i}", f"{小说名}", Fore.YELLOW)
        打印信息("  作者", 作者)
        打印信息("  最新章节", 最新章节)
        打印信息("  简介", 简介)
        print()

    # 提示用户是否继续查看更多结果（如果有分页）
    是否查看更多 = "n"
    if 搜索结果总数 != "未知":
        try:
            搜索结果总数_数字 = int(搜索结果总数)
            if 搜索结果总数_数字 > len(所有搜索结果) and len(所有搜索结果) > 0:
                是否查看更多 = input(f"{Fore.YELLOW}是否查看更多结果？(y/n，默认n): {Style.RESET_ALL}").strip().lower() or "n"
        except ValueError:
            # 如果转换失败，说明搜索结果总数不是数字
            pass

    if 是否查看更多 == "y":
        try:
            # 获取下一页按钮并点击
            with 错误抑制():
                下一页元素 = 浏览器.driver.find_element("css selector", "a.next")
                浏览器.driver.execute_script("arguments[0].click();", 下一页元素)
                time.sleep(2)  # 等待页面加载
                
                # 重新获取页面源码并解析
                搜索结果页面 = 浏览器.driver.page_source
                搜索结果soup = BeautifulSoup(搜索结果页面, 'html.parser')
                
                # 重新获取搜索结果列表
                下一页搜索结果列表 = 搜索结果soup.select('.list.dList > ul > li')
                
                打印标题("更多搜索结果")
                
                # 处理下一页的搜索结果
                下一页搜索结果 = []
                for 小说元素 in 下一页搜索结果列表:
                    try:
                        小说名元素 = 小说元素.select_one('.txtb .name a')
                        if 小说名元素:
                            小说名 = 小说名元素.text.strip()
                            小说链接 = 小说名元素['href']
                            
                            作者元素 = 小说元素.select_one('.info dl:first-child dd a')
                            作者 = 作者元素.text.strip() if 作者元素 else "未知"
                            
                            最新章节元素 = 小说元素.select_one('.info dl:last-child dd a')
                            最新章节 = 最新章节元素.text.strip() if 最新章节元素 else "未知"
                            
                            简介元素 = 小说元素.select_one('.intro')
                            简介 = 简介元素.text.strip() if 简介元素 else "暂无简介"
                            简介 = 简介[:50] + "..." if len(简介) > 50 else 简介
                            
                            # 确保链接是完整的
                            if not 小说链接.startswith('http'):
                                基础URL = 'https://www.shuwuwan.com'
                                小说链接 = f"{基础URL}{小说链接}" if 小说链接.startswith('/') else f"{基础URL}/{小说链接}"
                            
                            下一页搜索结果.append((小说名, 小说链接, 作者, 最新章节, 简介))
                            打印信息("检测到小说", f"{小说名} - {作者}", Fore.CYAN)
                    except Exception as e:
                        continue
                
                # 添加到总结果列表
                所有搜索结果.extend(下一页搜索结果)
                
                # 显示下一页的搜索结果
                起始索引 = len(所有搜索结果) - len(下一页搜索结果) + 1
                for i, (小说名, 小说链接, 作者, 最新章节, 简介) in enumerate(下一页搜索结果, 起始索引):
                    打印信息(f"{i}", f"{小说名}", Fore.YELLOW)
                    打印信息("  作者", 作者)
                    打印信息("  最新章节", 最新章节)
                    打印信息("  简介", 简介)
                    print()
        except Exception as e:
            打印警告(f"获取更多结果失败：{e}")

    # 选择要下载的小说
    选择索引 = int(input(f"{Fore.YELLOW}请输入要下载的小说编号（1-{len(所有搜索结果)}）：{Style.RESET_ALL}")) - 1

    if 选择索引 < 0 or 选择索引 >= len(所有搜索结果):
        打印错误("无效的选择")
        浏览器.关闭浏览器()
        exit()

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

    # 从HTML结构中提取信息
    try:
        # 获取小说标题
        小说标题 = soup.select_one('.conL .txtb .tit .name').text.strip()
        
        # 获取作者
        作者 = soup.select_one('.conL .txtb .tit .author a').text.strip()
        
        # 获取小说分类、状态、人气、更新时间
        小说信息_列表 = soup.select('.conL .txtb .about ul li')
        小说分类 = ""
        小说状态 = ""
        人气 = ""
        更新时间 = ""
        
        for 信息 in 小说信息_列表[:4]:  # 前4个li包含基本信息
            信息文本 = 信息.text.strip()
            if "分类：" in 信息文本:
                小说分类 = 信息文本.replace("分类：", "")
            elif "状态：" in 信息文本:
                小说状态 = 信息文本.replace("状态：", "")
            elif "人气：" in 信息文本:
                人气 = 信息文本.replace("人气：", "")
            elif "更新时间：" in 信息文本:
                更新时间 = 信息文本.replace("更新时间：", "")
        
        # 获取主角
        主角元素 = soup.select_one('.conL .txtb .about ul li:nth-of-type(5) a')
        主角 = 主角元素.text.strip() if 主角元素 else "未知"
        
        # 获取最新章节
        最新章节元素 = soup.select_one('.conL .txtb .lastChapter a')
        最新章节 = 最新章节元素.text.strip() if 最新章节元素 else "未知"
        最新章节链接 = 最新章节元素['href'] if 最新章节元素 else ""
        
        # 获取小说介绍
        小说介绍 = soup.select_one('.conL .txtb .intro').text.strip()
        
        # 打印获取到的信息
        打印标题(f"《{小说标题}》 - 信息")
        打印信息("作者", 作者)
        打印信息("分类", 小说分类)
        打印信息("状态", 小说状态)
        打印信息("人气", 人气)
        打印信息("更新时间", 更新时间)
        打印信息("主角", 主角)
        打印信息("最新章节", 最新章节)
        
        # 保存小说信息到文件
        with open(f'{下载目录}/{小说标题}_信息.txt', 'w', encoding='utf-8') as f:
            f.write(f"标题: 《{小说标题}》\n")
            f.write(f"作者: {作者}\n")
            f.write(f"分类: {小说分类}\n")
            f.write(f"状态: {小说状态}\n")
            f.write(f"人气: {人气}\n")
            f.write(f"更新时间: {更新时间}\n")
            f.write(f"主角: {主角}\n")
            f.write(f"最新章节: {最新章节}\n\n")
            f.write("小说简介:\n")
            f.write(小说介绍)
        
        打印成功(f"小说介绍已保存至：{下载目录}/{小说标题}_信息.txt")
        
        # 获取封面图片URL
        封面元素 = soup.select_one('.conL .txtb .about .pic img')
        if not 封面元素:
            封面元素 = soup.select_one('.conL .picb .pic img')
        if not 封面元素:
            封面元素 = soup.select_one('.txtb .picb .pic img')  # 新增支持的DOM结构
        if not 封面元素:
            封面元素 = soup.select_one('.about .picb .pic img')  # 新增支持的DOM结构
        if not 封面元素:
            封面元素 = soup.select_one('.pic img')  # 最宽松的选择器，尝试匹配任何带有class为pic的img
            
        封面URL = None    
        if 封面元素 and 封面元素.has_attr('src'):
            封面URL = 封面元素['src']
            
            # 确保封面URL是正确的格式
            if 封面URL.startswith("//"):
                封面URL = "https:" + 封面URL
            # 如果URL是相对路径，转为绝对路径
            elif not 封面URL.startswith('http'):
                # 正确构建基础URL
                if 小说页面URL.startswith('https://'):
                    基础URL = '/'.join(小说页面URL.split('/')[:3])
                    封面URL = f"{基础URL}{封面URL}" if 封面URL.startswith('/') else f"{基础URL}/{封面URL}"
                else:
                    # 如果当前URL不是https开头，尝试使用固定的网站域名
                    基础URL = "https://www.shuwuwan.com"
                    封面URL = f"{基础URL}{封面URL}" if 封面URL.startswith('/') else f"{基础URL}/{封面URL}"
            
            # 支持直接输入的完整URL
            if 'bookimg' in 封面URL and '封面URL' not in 封面URL:
                print(f"{Fore.CYAN}检测到封面URL: {封面URL}{Style.RESET_ALL}")
            else:
                print(f"{Fore.CYAN}尝试修复封面URL: {封面URL}{Style.RESET_ALL}")
                
                # 尝试提取URL中的bookID
                book_id_match = re.search(r'/book/(\w+)(-\d+)?\.html', 小说页面URL)
                if book_id_match:
                    book_id = book_id_match.group(1)
                    # 构造可能的封面URL
                    封面URL = f"https://www.shuwuwan.com/bookimg/{book_id}.jpg"
                    print(f"{Fore.CYAN}根据书籍ID构造封面URL: {封面URL}{Style.RESET_ALL}")
        else:
            打印警告("未在页面中找到小说封面图片链接")
            
        # 允许用户手动输入封面URL
        手动封面URL = input(f"{Fore.YELLOW}请输入封面URL(直接回车使用自动检测): {Style.RESET_ALL}").strip()
        if 手动封面URL:
            封面URL = 手动封面URL
            print(f"{Fore.CYAN}使用手动输入的封面URL: {封面URL}{Style.RESET_ALL}")
        
        if 封面URL:
            # 下载封面
            print(f"{Fore.CYAN}正在下载小说封面...{Style.RESET_ALL}")
            try:
                # 添加请求头，模拟浏览器请求，绕过防盗链
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                    'Referer': 小说页面URL,  # 添加Referer头，解决防盗链问题
                }
                response = requests.get(封面URL, headers=headers, timeout=10)
                if response.status_code == 200:
                    # 获取文件扩展名
                    文件扩展名 = os.path.splitext(封面URL)[1]
                    if not 文件扩展名:
                        文件扩展名 = '.jpg'  # 默认扩展名
                    
                    # 保存封面
                    封面保存路径 = f'{下载目录}/{小说标题}_封面{文件扩展名}'
                    with open(封面保存路径, 'wb') as f:
                        f.write(response.content)
                    打印成功(f"小说封面已保存")
                else:
                    打印警告(f"下载封面失败 (HTTP {response.status_code})")
            except Exception as e:
                打印警告(f"下载封面失败")
        else:
            打印警告("已跳过下载封面")
        
        # 获取所有章节列表
        所有章节列表 = []
        打印标题("获取章节列表")

        # 创建小说内容目录
        小说目录 = f'{下载目录}/{小说标题}_章节'
        if not os.path.exists(小说目录):
            os.makedirs(小说目录)

        最大页数 = 10  # 设置最大页数限制，防止无限循环
        当前页数 = 1
        连续无新增章节次数 = 0  # 初始化连续无新增章节计数器

        while 当前页数 <= 最大页数:  # 添加最大页数限制
            print(f"{Fore.CYAN}正在获取第 {当前页数} 页章节列表...{Style.RESET_ALL}")
            
            # 获取当前页面的章节列表
            页面源码 = 浏览器.driver.page_source
            soup = BeautifulSoup(页面源码, 'html.parser')
            
            # 获取开始爬取前的章节数量
            开始章节数量 = len(所有章节列表)
            
            # 查找章节列表容器
            章节列表容器 = soup.select_one('.chapterList .list')
            if not 章节列表容器:
                print(f"{Fore.YELLOW}未找到章节列表容器，章节获取结束{Style.RESET_ALL}")
                break
            
            # 获取章节元素
            章节元素列表 = 章节列表容器.select('li .name a')
            if not 章节元素列表:
                print(f"{Fore.YELLOW}当前页面未找到章节列表，章节获取结束{Style.RESET_ALL}")
                break
            
            # 处理当前页面的章节
            for 章节元素 in 章节元素列表:
                章节名 = 章节元素.text.strip()
                章节链接 = 章节元素['href']
                
                # 如果链接是相对路径，转为绝对路径
                if not 章节链接.startswith('http'):
                    基础URL = '/'.join(小说页面URL.split('/')[:3])
                    章节链接 = f"{基础URL}{章节链接}" if 章节链接.startswith('/') else f"{基础URL}/{章节链接}"
                
                # 检查是否已经存在该章节，避免重复添加
                已存在章节链接 = [链接 for _, 链接 in 所有章节列表]
                if 章节链接 not in 已存在章节链接:
                    所有章节列表.append((章节名, 章节链接))
                else:
                    print(f"{Fore.YELLOW}检测到重复章节：{章节名}{Style.RESET_ALL}")
            
            # 获取结束后的章节数量，检查是否有新章节添加
            结束章节数量 = len(所有章节列表)
            新增章节数 = 结束章节数量 - 开始章节数量
            
            # 检查当前页是否为最后一页
            是否最后一页 = False
            下一页按钮 = soup.select_one('.next')
            没有了按钮 = soup.select_one('.noNext.disabled')
            
            if 没有了按钮 and 'display: none' not in 没有了按钮.get('style', '') and 没有了按钮.text.strip() == "没有了":
                是否最后一页 = True
                print(f"{Fore.YELLOW}已到达最后页（找到'没有了'标记）{Style.RESET_ALL}")
            
            # 如果没有新增章节或已到最后页，则退出循环
            if 新增章节数 == 0:
                连续无新增章节次数 += 1
                print(f"{Fore.YELLOW}当前页未获取到新章节，可能是重复页面或已获取完毕{Style.RESET_ALL}")
                
                # 如果连续两页都没有新增章节，强制终止
                if 连续无新增章节次数 >= 2 or 是否最后一页:
                    print(f"{Fore.YELLOW}连续多页未获取到新章节或已到达最后页，强制终止获取{Style.RESET_ALL}")
                    break
            else:
                # 重置连续无新增计数
                连续无新增章节次数 = 0
            
            # 尝试查找并点击下一页按钮
            try:
                下一页按钮元素 = 浏览器.driver.find_element('css selector', '.next')
                if 下一页按钮元素:
                    浏览器.driver.execute_script("arguments[0].click();", 下一页按钮元素)
                    print(f"{Fore.CYAN}点击了下一页按钮，准备获取下一页章节列表{Style.RESET_ALL}")
                    time.sleep(1)  # 等待页面加载
                    当前页数 += 1
                else:
                    # 尝试使用下拉框选择页码
                    try:
                        选择框 = 浏览器.driver.find_element('css selector', '.select')
                        # 获取下一个选项值
                        浏览器.driver.execute_script(f"arguments[0].value = '{当前页数 + 1}';", 选择框)
                        浏览器.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", 选择框)
                        print(f"{Fore.CYAN}通过下拉框选择了新的页码分组{Style.RESET_ALL}")
                        time.sleep(1)
                        当前页数 += 1
                    except Exception as e:
                        print(f"{Fore.RED}无法继续获取章节，{e}{Style.RESET_ALL}")
                        break
            except Exception as e:
                print(f"{Fore.RED}获取下一页失败：{e}，章节列表获取完毕{Style.RESET_ALL}")
                break
            
            # 页数检查 - 如果超过了最大页数限制则终止
            if 当前页数 > 最大页数:
                print(f"{Fore.RED}已达到最大页数限制（{最大页数}页），强制终止获取{Style.RESET_ALL}")
                break
        
        # 确保章节按正确顺序排列 - 根据章节URL中的序号或按添加顺序排序
        所有章节列表_排序 = []
        for 章节名, 章节链接 in 所有章节列表:
            # 尝试从URL中提取章节序号
            章节序号匹配 = re.search(r'(\d+)\.html$', 章节链接)
            if 章节序号匹配:
                序号 = int(章节序号匹配.group(1))
                所有章节列表_排序.append((序号, 章节名, 章节链接))
            else:
                # 如果无法提取序号，则使用当前列表长度作为序号
                所有章节列表_排序.append((len(所有章节列表_排序), 章节名, 章节链接))
        
        # 按序号排序
        所有章节列表_排序.sort(key=lambda x: x[0])
        # 转换回原来的格式
        所有章节列表 = [(章节名, 章节链接) for _, 章节名, 章节链接 in 所有章节列表_排序]
        
        打印成功(f"共获取到 {len(所有章节列表)} 个章节，总共爬取了 {当前页数} 页")
        打印分隔线()
        
        # 询问是否下载所有章节
        下载选择 = input(f"{Fore.YELLOW}是否下载所有章节？(y/n): {Style.RESET_ALL}").strip().lower()
        
        if 下载选择 == 'y':
            # 询问下载格式选择
            格式选择 = input(f"{Fore.YELLOW}选择下载格式：1=EPUB（默认）, 2=TXT: {Style.RESET_ALL}").strip() or "1"
            
            print(f"{Fore.CYAN}\n开始下载章节内容...{Style.RESET_ALL}")
            打印分隔线()
            
            # 创建进度条
            进度条 = tqdm(total=len(所有章节列表), desc="下载进度", unit="章", 
                    bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL))
            
            # 单线程顺序下载章节
            下载结果 = []
            
            for idx, (章节名, 章节链接) in enumerate(所有章节列表):
                try:
                    # 使用同一个浏览器窗口
                    with 错误抑制():
                        浏览器.打开地址(章节链接)
                    time.sleep(0.5)  # 等待页面加载
                    
                    # 获取章节内容
                    章节页面源码 = 浏览器.driver.page_source
                    章节soup = BeautifulSoup(章节页面源码, 'html.parser')
                    
                    # 提取章节内容
                    章节内容元素 = 章节soup.select_one('#content')
                    if 章节内容元素:
                        章节内容 = 章节内容元素.text.strip()
                        
                        # 清理章节内容
                        章节内容 = 章节内容.replace('    ', '\n\n')  # 替换多个空格为换行
                        
                        # 清洗内容，移除广告和不必要的文本
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
                        
                        # 移除形如@http://www.shuwuwan.com/book/F72W-834.html的网址
                        章节内容 = re.sub(r'@https?://www\.shuwuwan\.com/book/\w+-\d+\.html', '', 章节内容)
                        # 移除任何网址格式
                        章节内容 = re.sub(r'@https?://[^\s]+', '', 章节内容)
                        
                        # 移除空行
                        章节内容行 = 章节内容.split('\n')
                        清洗后章节内容 = []
                        
                        for 行 in 章节内容行:
                            行 = 行.strip()
                            # 忽略空行和只包含特殊字符的行
                            if 行 and not all(c in ',.!?;:。，！？；：-—_=+~`@#$%^&*()[]{}<>/\\|\'"' for c in 行):
                                清洗后章节内容.append(行)
                        
                        章节内容 = '\n\n'.join(清洗后章节内容)
                        
                        # 保存章节内容
                        章节文件名 = f"{idx+1:04d}_{章节名}.txt"  # 格式化章节序号为4位数
                        with open(f'{小说目录}/{章节文件名}', 'w', encoding='utf-8') as f:
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
            打印成功(f"章节下载完成！成功：{成功数量}/{len(所有章节列表)}")
            
            # 创建完整小说文件
            print(f"{Fore.CYAN}正在生成完整小说文件...{Style.RESET_ALL}")
            
            # 根据用户选择的格式生成对应文件
            if 格式选择 == "2":  # TXT格式
                生成TXT文件(小说标题, 作者, 小说介绍, 小说目录, 下载目录)
            else:  # EPUB格式（默认）
                生成EPUB文件(小说标题, 作者, 小说介绍, 小说目录, 下载目录)
        else:
            打印警告("已跳过下载章节内容")
    
    except Exception as e:
        打印错误(f"获取小说信息出错：{e}")
        import traceback
        traceback.print_exc()

    with 错误抑制():
        浏览器.关闭浏览器()

# 生成TXT格式小说文件
def 生成TXT文件(小说标题, 作者, 小说介绍, 小说目录, 下载目录):
    # 生成TXT文件路径
    txt文件路径 = f'{下载目录}/{小说标题}.txt'
    
    # 检查是否已存在同名文件，如果存在则先删除
    if os.path.exists(txt文件路径):
        try:
            os.remove(txt文件路径)
            print(f"{Fore.YELLOW}已删除旧的TXT文件{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}删除旧文件失败: {e}{Style.RESET_ALL}")
    
    with open(txt文件路径, 'w', encoding='utf-8') as outfile:
        # 写入小说信息
        outfile.write(f"书名：{小说标题}\n")
        outfile.write(f"作者：{作者}\n")
        outfile.write(f"简介：\n{小说介绍}\n\n")
        outfile.write("=" * 50 + "\n\n")
        
        # 按顺序写入章节内容
        章节文件列表 = sorted(os.listdir(小说目录))
        总字数 = 0
        总章节数 = 0
        
        # 添加进度条
        with tqdm(total=len(章节文件列表), desc="生成TXT文件", unit="章",
                 bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL)) as pbar:
            for 章节文件 in 章节文件列表:
                if 章节文件.endswith('.txt'):
                    try:
                        with open(f'{小说目录}/{章节文件}', 'r', encoding='utf-8') as infile:
                            章节内容 = infile.read()
                            outfile.write(章节内容)
                            outfile.write("\n\n" + "=" * 30 + "\n\n")  # 章节分隔符
                            
                            # 统计字数（去除章节标题和空白后）
                            章节正文 = '\n'.join(章节内容.split('\n')[2:])  # 前两行是章节标题和空行
                            章节字数 = len(章节正文.replace('\n', '').replace(' ', ''))
                            总字数 += 章节字数
                            总章节数 += 1
                    except Exception:
                        # 忽略错误，继续处理下一章节
                        pass
                    finally:
                        # 无论成功与否，都更新进度条
                        pbar.update(1)
        
        # 在文件末尾添加统计信息
        outfile.write(f"\n\n完结统计：\n")
        outfile.write(f"总章节数：{总章节数}\n")
        outfile.write(f"总字数：{总字数} 字\n")
        outfile.write(f"下载时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    打印成功(f"完整TXT小说文件已生成：{下载目录}/{小说标题}.txt")
    打印信息("总章节数", 总章节数, Fore.CYAN)
    打印信息("总字数", f"{总字数} 字", Fore.CYAN)
    打印标题("下载完成")

# 生成EPUB格式小说文件
def 生成EPUB文件(小说标题, 作者, 小说介绍, 小说目录, 下载目录):
    # 生成EPUB文件路径
    epub_文件路径 = f'{下载目录}/{小说标题}.epub'
    
    # 检查是否已存在同名文件，如果存在则先删除
    if os.path.exists(epub_文件路径):
        try:
            os.remove(epub_文件路径)
            print(f"{Fore.YELLOW}已删除旧的EPUB文件{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}删除旧文件失败: {e}{Style.RESET_ALL}")
            
    # 检查是否存在TXT文件，确认只生成EPUB（防止出现选择EPUB但同时生成TXT的情况）
    txt文件路径 = f'{下载目录}/{小说标题}.txt'
    if os.path.exists(txt文件路径):
        try:
            os.remove(txt文件路径)
            print(f"{Fore.YELLOW}删除已存在的TXT文件，仅生成EPUB格式{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}删除旧TXT文件失败: {e}{Style.RESET_ALL}")
    
    # 创建EPUB书籍
    book = epub.EpubBook()
    
    # 设置元数据
    book.set_identifier(f'id{int(time.time())}')
    book.set_title(小说标题)
    book.set_language('zh-CN')
    book.add_author(作者)
    
    # 添加CSS样式
    css_style = """
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: SimSun, serif;
        line-height: 1.5;
        padding: 0 1em;
    }
    h1 {
        text-align: center;
        padding: 0.5em 0;
        margin: 0;
    }
    p {
        text-indent: 2em;
        margin: 0;
        padding: 0.3em 0;
    }
    """
    style = epub.EpubItem(uid="style_default", file_name="style/default.css", 
                         media_type="text/css", content=css_style)
    book.add_item(style)
    
    # 创建简介页
    介绍页 = epub.EpubHtml(title='简介', file_name='intro.xhtml', lang='zh-CN')
    介绍页.content = f'<h1>{小说标题}</h1>\n<p>作者：{作者}</p>\n<h2>简介</h2>\n<p>{"</p>\n<p>".join(小说介绍.split("\n"))}</p>'
    介绍页.add_item(style)
    book.add_item(介绍页)
    
    章节列表 = []
    章节文件列表 = sorted(os.listdir(小说目录))
    
    # 添加封面图片
    封面路径 = f'{下载目录}/{小说标题}_封面.jpg'
    if os.path.exists(封面路径):
        with open(封面路径, 'rb') as f:
            book.set_cover('cover.jpg', f.read())
        打印成功("已添加封面图片")
    
    # 创建各章节
    print(f"{Fore.CYAN}正在生成EPUB章节...{Style.RESET_ALL}")
    
    # 首先按文件名排序以确保章节顺序正确
    章节文件列表 = sorted(os.listdir(小说目录))
    
    with tqdm(total=len([f for f in 章节文件列表 if f.endswith('.txt')]), desc="创建章节", unit="章",
             bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Style.RESET_ALL)) as pbar:
        for i, 章节文件 in enumerate(章节文件列表):
            if 章节文件.endswith('.txt'):
                try:
                    with open(f'{小说目录}/{章节文件}', 'r', encoding='utf-8') as infile:
                        章节内容 = infile.read()
                        章节行 = 章节内容.split('\n')
                        章节标题 = 章节行[0]  # 第一行是标题
                        章节正文 = '\n'.join(章节行[2:])  # 从第3行开始是正文（第2行是空行）
                        
                        # 格式化正文，将段落包装在<p>标签中
                        章节正文HTML = ""
                        for 段落 in re.split(r'\n\s*\n', 章节正文):
                            if 段落.strip():
                                # 再次移除可能的网址
                                段落 = re.sub(r'@https?://[^\s]+', '', 段落)
                                章节正文HTML += f"<p>{段落.strip()}</p>\n"
                        
                        # 创建章节
                        章节 = epub.EpubHtml(title=章节标题, file_name=f'chapter_{i+1}.xhtml', lang='zh-CN')
                        章节.content = f'<h1>{章节标题}</h1>\n{章节正文HTML}'
                        章节.add_item(style)
                        
                        book.add_item(章节)
                        章节列表.append(章节)
                except Exception:
                    # 忽略错误，继续处理下一章节
                    pass
                finally:
                    # 无论成功与否，都更新进度条
                    pbar.update(1)
    
    # 创建目录页
    print(f"{Fore.CYAN}正在生成目录...{Style.RESET_ALL}")
    book.toc = [epub.Link('intro.xhtml', '简介', 'intro')] + 章节列表
    
    # 添加默认NCX和Nav
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # 定义书籍线性阅读顺序
    book.spine = ['nav', 介绍页] + 章节列表
    
    # 生成EPUB文件
    print(f"{Fore.CYAN}正在写入EPUB文件...{Style.RESET_ALL}")
    epub.write_epub(epub_文件路径, book, {})
    
    打印成功(f"完整EPUB电子书已生成：{epub_文件路径}")
    打印信息("总章节数", len(章节列表), Fore.CYAN)
    打印信息("下载时间", time.strftime('%Y-%m-%d %H:%M:%S'), Fore.CYAN)
    打印标题("下载完成")


