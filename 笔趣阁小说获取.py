"""
首先打开笔趣阁小说网站
"https://www.tpyyc.com"
然后安装各种库
pip install requests beautifulsoup4 ebooklib
"""

import requests
from bs4 import BeautifulSoup
import os
import re
from ebooklib import epub
import time
from urllib.parse import urljoin
import concurrent.futures
import threading
from queue import Queue

class NovelDownloader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = "https://www.tpyyc.com"
        self.download_queue = Queue()
        self.chapter_contents = {}
        self.thread_lock = threading.Lock()
        self.max_workers = 5  # 最大线程数
        
    def get_novel_info(self, novel_id):
        """获取小说基本信息"""
        try:
            # 验证输入格式
            if not re.match(r'^\d+$', novel_id):
                raise ValueError("ID格式错误！请使用类似'213940'的格式。")
            
            # 构建URL
            url = f"{self.base_url}/{novel_id}/"
            print(f"正在访问URL: {url}")
            
            response = requests.get(url, headers=self.headers)
            response.encoding = 'utf-8'
            
            # 打印响应状态码和内容长度
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容长度: {len(response.text)}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取封面图片URL
            cover_img = soup.find('div', id='fmimg').find('img')
            if cover_img and cover_img.get('src'):
                cover_url = cover_img['src']
                # 如果是相对路径，转为完整URL
                if not cover_url.startswith('http'):
                    cover_url = urljoin(self.base_url, cover_url)
            else:
                cover_url = None
            
            # 获取标题
            title_elem = soup.find('div', id='info').find('h1')
            if not title_elem:
                raise ValueError("未找到标题元素")
            title = title_elem.text.strip()
            
            # 获取作者、状态和更新时间
            info_div = soup.find('div', id='info')
            if not info_div:
                raise ValueError("未找到info div元素")
            
            info_paragraphs = info_div.find_all('p', class_='tpyyc')
            author = ""
            status = ""
            update_time = ""
            
            for p in info_paragraphs:
                text = p.text.strip()
                if '作' in text:
                    author = text.replace('作', '').replace('者', '').replace('：', '').replace(':', '').strip()
                elif '状' in text:
                    status = text.replace('状', '').replace('态', '').replace('：', '').replace(':', '').strip()
                elif '最后更新' in text:
                    update_time = text.replace('最后更新：', '').strip()
            
            # 获取简介
            intro_div = soup.find('div', id='intro')
            if not intro_div:
                raise ValueError("未找到简介div元素")
            intro_p = intro_div.find('p', class_='tpyyc')
            if not intro_p:
                raise ValueError("未找到简介p元素")
            intro = intro_p.text.strip()
            
            # 获取章节列表
            chapters = []
            chapter_list_div = soup.find('dl', class_='tpyyc')
            if chapter_list_div:
                chapter_links = chapter_list_div.find_all('a', class_='tpyyc')
                for link in chapter_links:
                    chapter_url = urljoin(url, link['href'])
                    chapter_title = link.text.strip()
                    # 提取章节号
                    match = re.search(r'第(\d+)章', chapter_title)
                    if match:
                        chapter_num = int(match.group(1))
                        chapters.append((chapter_num, chapter_title, chapter_url))
                
                # 按章节号排序
                chapters.sort(key=lambda x: x[0])
                # 移除章节号，只保留标题和URL
                chapters = [(title, url) for _, title, url in chapters]
            
            if not chapters:
                raise ValueError("未找到任何章节")
            
            return {
                'title': title,
                'author': author,
                'status': status,
                'update_time': update_time,
                'intro': intro,
                'chapters': chapters,
                'cover_url': cover_url
            }
            
        except Exception as e:
            print(f"获取小说信息时出错: {str(e)}")
            print(f"请检查小说ID是否正确，当前ID: {novel_id}")
            raise
    
    def get_chapter_content(self, url):
        """获取章节内容"""
        try:
            response = requests.get(url, headers=self.headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新的内容容器 - div#article
            content = soup.find('div', id='article')
            if content:
                # 获取所有段落
                paragraphs = content.find_all('p', class_='tpyyc')
                if paragraphs:
                    # 过滤掉第一个段落（标题）和重复的内容
                    unique_paragraphs = []
                    seen = set()
                    for p in paragraphs[1:]:  # 跳过第一个段落（标题）
                        text = p.text.strip()
                        if text and text not in seen:
                            seen.add(text)
                            unique_paragraphs.append(text)
                    
                    # 添加缩进并用双换行连接段落
                    formatted_text = '\n\n'.join('    ' + p for p in unique_paragraphs)
                    return formatted_text
            return ""
        except Exception as e:
            print(f"获取章节内容失败: {str(e)}")
            return ""
            
    def download_chapter(self, chapter_info):
        """下载单个章节的内容"""
        chapter_num, (chapter_title, chapter_url) = chapter_info
        try:
            content = self.get_chapter_content(chapter_url)
            if content:
                with self.thread_lock:
                    self.chapter_contents[chapter_num] = (chapter_title, content)
                print(f"下载完成: {chapter_title}")
            return True
        except Exception as e:
            print(f"下载章节失败 {chapter_title}: {str(e)}")
            return False

    def create_epub(self, novel_info):
        """创建epub电子书"""
        book = epub.EpubBook()
        
        # 设置元数据
        book.set_identifier(f'xuanyge_{int(time.time())}')
        book.set_title(novel_info['title'])
        book.set_language('zh-CN')
        book.add_author(novel_info['author'])
        
        # 添加封面 - 只在这里处理一次封面
        cover_item = None
        if novel_info.get('cover_url'):
            try:
                # 下载封面图片
                cover_response = requests.get(novel_info['cover_url'], headers=self.headers)
                cover_response.raise_for_status()
                
                # 创建封面图片
                book.set_cover("cover.jpg", cover_response.content)
                
                # 创建封面页
                cover_item = epub.EpubHtml(title='封面', file_name='cover.xhtml')
                cover_item.content = f'<html><body><img src="cover.jpg" alt="cover"/></body></html>'
                book.add_item(cover_item)
            except Exception as e:
                print(f"添加封面失败: {str(e)}")
                cover_item = None
        
        # 添加简介章节
        intro_chapter = epub.EpubHtml(title='简介', file_name='intro.xhtml')
        intro_content = f"""
        <html>
        <head>
            <style>
                body {{ margin: 5%; text-align: justify; }}
                h1 {{ text-align: center; }}
                .meta {{ margin: 1em 0; }}
            </style>
        </head>
        <body>
            <h1>{novel_info['title']}</h1>
            <div class="meta">
                <p><strong>作者：</strong>{novel_info['author']}</p>
                <p><strong>状态：</strong>{novel_info['status']}</p>
                <p><strong>更新时间：</strong>{novel_info['update_time']}</p>
            </div>
            <h2>简介：</h2>
            <div>{novel_info['intro']}</div>
        </body>
        </html>
        """
        intro_chapter.content = intro_content
        book.add_item(intro_chapter)
        
        # 添加章节
        chapters = []
        chapter_items = []
        
        # 准备下载队列
        for idx, (chapter_title, chapter_url) in enumerate(novel_info['chapters']):
            if chapter_title.startswith('第'):
                # 提取章节号用作索引
                match = re.search(r'第(\d+)章', chapter_title)
                if match:
                    chapter_num = int(match.group(1))
                    chapter_items.append((chapter_num, (chapter_title, chapter_url)))
        
        # 按章节号排序
        chapter_items.sort(key=lambda x: x[0])
        
        # 使用线程池下载章节
        print(f"开始下载 {len(chapter_items)} 个章节...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.download_chapter, item) for item in chapter_items]
            concurrent.futures.wait(futures)
        
        # 添加CSS样式
        style = '''
        @namespace epub "http://www.idpf.org/2007/ops";
        body {
            margin: 5% 8%;
            font-family: SimSun, "Microsoft YaHei", serif;
            text-align: justify;
            line-height: 1.8;
        }
        h1 {
            text-align: center;
            margin: 2em 0;
            font-weight: bold;
            font-size: 1.5em;
        }
        p {
            text-indent: 2em;
            margin: 0.8em 0;
            line-height: 1.8;
        }
        '''
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)
        
        # 修改章节内容的处理方式
        for idx in sorted(self.chapter_contents.keys()):
            chapter_title, content = self.chapter_contents[idx]
            
            # 将内容分段并添加HTML格式
            paragraphs = content.split('\n\n')
            chapter = epub.EpubHtml(
                title=chapter_title,
                file_name=f'chapter_{idx}.xhtml',
                lang='zh-CN'
            )
            chapter.content = f'<h1>{chapter_title}</h1>\n' + '\n'.join(f'<p>{p}</p>' for p in paragraphs)
            chapter.add_item(nav_css)
            book.add_item(chapter)
            chapters.append(chapter)
        
        # 修改目录生成部分
        # 创建目录
        toc = []
        if cover_item:  # 使用之前创建的cover_item
            toc.append(cover_item)
        
        toc.append(intro_chapter)
        toc.extend(chapters)
        
        # 设置目录和阅读顺序
        book.toc = toc
        book.spine = ['nav'] + toc
        
        # 添加默认NCX和Nav文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        return book
        
    def download_novel(self, novel_id):
        """下载小说并保存为epub"""
        try:
            print("获取小说信息...")
            novel_info = self.get_novel_info(novel_id)
            
            # 清空之前的下载内容
            self.chapter_contents.clear()
            
            print("创建epub...")
            book = self.create_epub(novel_info)
            
            # 保存文件
            filename = f"{novel_info['title']}.epub"
            epub.write_epub(filename, book)
            print(f"下载完成: {filename}")
            
        except Exception as e:
            print(f"下载失败: {str(e)}")

def main():
    downloader = NovelDownloader()
    print("=" * 50)
    print("玄幻阁小说下载器")
    print("格式说明：")
    print("- 必须使用'213940'的格式")
    print("- 例如：213940")
    print("=" * 50)
    novel_id = input("请输入小说ID: ")
    downloader.download_novel(novel_id)

if __name__ == "__main__":
    main()

