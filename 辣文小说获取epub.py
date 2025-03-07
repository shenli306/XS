"""
https://www.aaqqcc.com/book/
辣文小说获取epub.py
获取小说信息
获取小说章节列表
获取小说章节内容
获取小说封面图片
生成epub文件
首先安装这些库 pip install requests beautifulsoup4 ebooklib
"""

import requests
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
import time
import os
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class NovelSite:
    def __init__(self, domain, selectors):
        self.domain = domain
        self.selectors = selectors

# 支持的网站配置
SUPPORTED_SITES = {
    'aaqqcc.com': NovelSite('aaqqcc.com', {
        'title': 'h1',
        'content': 'div#content',
        'author': 'dl.authors dd a',
        'chapter_links': 'div.book-chapter a',
        'next_page': 'a.next',
        'cover_image': 'div.cover img',
        'status': 'dl.status dd',
        'score': 'dl.score dd',
        'categories': 'dl.categories dd a',
        'word_count': 'dl.wordcount dd',
    }),
    # 可以添加更多网站的配置
}

class NovelDownloader:
    def __init__(self, max_retries=3, delay=1):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.max_retries = max_retries
        self.delay = delay
        self.session = requests.Session()

    def get_site_config(self, url):
        domain = urlparse(url).netloc
        for site_domain, config in SUPPORTED_SITES.items():
            if site_domain in domain:
                return config
        raise ValueError(f"不支持的网站: {domain}")

    def get_page_content(self, url):
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    response.encoding = response.apparent_encoding
                    content = response.text
                    if content and len(content) > 0:
                        return content
                    else:
                        logging.error(f"页面内容为空: {url}")
                else:
                    logging.error(f"HTTP错误 {response.status_code}: {url}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.delay * (attempt + 1)
                    logging.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    
            except requests.Timeout:
                logging.error(f"请求超时: {url}")
            except requests.ConnectionError:
                logging.error(f"连接错误: {url}")
            except Exception as e:
                logging.error(f"获取页面失败 {url}: {str(e)}")
            
            if attempt < self.max_retries - 1:
                wait_time = self.delay * (attempt + 1)
                logging.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                
        return None

    def get_novel_info(self, url):
        site_config = self.get_site_config(url)
        html_content = self.get_page_content(url)
        
        if not html_content:
            raise ValueError(f"无法获取页面内容: {url}")
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 获取标题
            title = soup.select_one(site_config.selectors['title'])
            if not title:
                logging.warning("未找到标题，使用默认标题")
                title = '未知标题'
            else:
                title = title.text.strip()
            
            # 获取作者
            author = soup.select_one(site_config.selectors['author'])
            if not author:
                logging.warning("未找到作者，使用默认作者")
                author = '未知作者'
            else:
                author = author.text.strip()

            # 获取状态
            status = soup.select_one(site_config.selectors['status'])
            status = status.text.strip() if status else '未知状态'

            # 获取评分
            score = soup.select_one(site_config.selectors['score'])
            score = score.text.strip() if score else '暂无评分'

            # 获取分类
            categories = soup.select(site_config.selectors['categories'])
            categories = [cat.text.strip() for cat in categories] if categories else ['未分类']

            # 获取字数
            word_count = soup.select_one(site_config.selectors['word_count'])
            word_count = word_count.text.strip() if word_count else '未知字数'

            # 获取章节列表
            chapter_links = soup.select(site_config.selectors['chapter_links'])
            if not chapter_links:
                raise ValueError("未找到任何章节链接")
                
            chapters = []
            for link in chapter_links:
                try:
                    chapter_url = urljoin(url, link['href'])
                    chapter_title = link.text.strip()
                    if chapter_title and chapter_url:
                        chapters.append((chapter_title, chapter_url))
                except Exception as e:
                    logging.warning(f"处理章节链接时出错: {str(e)}")
                    continue

            if not chapters:
                raise ValueError("未能成功获取任何章节信息")

            return {
                'title': title,
                'author': author,
                'chapters': chapters,
                'status': status,
                'score': score,
                'categories': categories,
                'word_count': word_count
            }
            
        except Exception as e:
            logging.error(f"解析页面内容时出错: {str(e)}")
            raise

    def get_chapter_content(self, url):
        site_config = self.get_site_config(url)
        html_content = self.get_page_content(url)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        content = soup.select_one(site_config.selectors['content'])
        if content:
            # 清理文本内容
            text = content.get_text('\n').strip()
            text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
            return text
        return None

    def get_cover_image(self, url):
        """获取封面图片"""
        try:
            site_config = self.get_site_config(url)
            html_content = self.get_page_content(url)
            if not html_content:
                return None
                
            soup = BeautifulSoup(html_content, 'html.parser')
            img_tag = soup.select_one(site_config.selectors['cover_image'])
            
            if img_tag and img_tag.get('src'):
                img_url = urljoin(url, img_tag['src'])
                response = self.session.get(img_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    return response.content
                    
            logging.warning("未找到封面图片")
            return None
            
        except Exception as e:
            logging.error(f"获取封面图片失败: {str(e)}")
            return None

class EpubCreator:
    def __init__(self, novel_info, cover_data=None):
        self.novel_info = novel_info
        self.book = epub.EpubBook()
        self.chapters = []
        self.cover_data = cover_data

    def create_epub(self, output_path):
        try:
            # 设置元数据
            self.book.set_identifier(f'novel_{int(time.time())}')
            self.book.set_title(self.novel_info['title'])
            self.book.set_language('zh-CN')
            self.book.add_author(self.novel_info['author'])
            self.book.add_metadata('DC', 'date', datetime.now().strftime('%Y-%m-%d'))

            # 添加更多元数据
            self.book.add_metadata('DC', 'description', f'''
状态：{self.novel_info.get('status', '未知状态')}
评分：{self.novel_info.get('score', '暂无评分')}
分类：{', '.join(self.novel_info.get('categories', ['未分类']))}
字数：{self.novel_info.get('word_count', '未知字数')}
            '''.strip())

            # 添加封面
            if self.cover_data:
                cover_image = epub.EpubImage()
                cover_image.file_name = 'cover.jpg'
                cover_image.media_type = 'image/jpeg'
                cover_image.content = self.cover_data
                self.book.add_item(cover_image)
                
                # 创建封面页
                cover_page = epub.EpubHtml(
                    title='Cover',
                    file_name='cover.xhtml',
                    lang='zh-CN'
                )
                cover_page.content = f'<img src="cover.jpg" alt="cover" style="max-width: 100%;"/>'
                self.book.add_item(cover_page)
                self.book.set_cover("cover.jpg", self.cover_data)

            # 添加CSS样式
            style = '''
            @namespace epub "http://www.idpf.org/2007/ops";
            body { font-family: SimSun, serif; }
            h1 { text-align: center; }
            '''
            nav_css = epub.EpubItem(
                uid="style_nav",
                file_name="style/nav.css",
                media_type="text/css",
                content=style
            )
            self.book.add_item(nav_css)

            # 创建章节
            spine = ['nav']
            for i, (title, content) in enumerate(self.chapters, 1):
                chapter = epub.EpubHtml(
                    title=title,
                    file_name=f'chapter_{i}.xhtml',
                    lang='zh-CN'
                )
                chapter.content = f'<h1>{title}</h1>\n' + '\n'.join(f'<p>{line}</p>' for line in content.split('\n'))
                chapter.add_item(nav_css)
                self.book.add_item(chapter)
                self.book.toc.append(epub.Link(f'chapter_{i}.xhtml', title, f'chapter_{i}'))
                spine.append(chapter)

            # 添加导航
            nav = epub.EpubNav()
            nav.add_item(nav_css)
            self.book.add_item(nav)
            self.book.add_item(epub.EpubNcx())

            # 设置 spine
            self.book.spine = spine
            
            # 生成epub文件
            epub.write_epub(output_path, self.book, {})
            logging.info(f'已成功生成epub文件: {output_path}')
            return True

        except Exception as e:
            logging.error(f'生成epub文件时出错: {str(e)}')
            return False

    def add_chapter(self, title, content):
        self.chapters.append((title, content))

def main():
    try:
        # 获取用户输入
        print('请输入小说目录页面URL，直接回车将使用默认URL')
        url = input('> ').strip()
        if not url:
            url = 'https://www.aaqqcc.com/book/4210/'  # 默认URL
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # 验证URL格式
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("无效的URL格式")
        except Exception as e:
            logging.error(f"URL格式错误: {str(e)}")
            return

        # 创建下载器
        downloader = NovelDownloader()
        
        # 获取小说信息
        logging.info('正在获取小说信息...')
        try:
            novel_info = downloader.get_novel_info(url)
        except Exception as e:
            logging.error(f"获取小说信息失败: {str(e)}")
            return
            
        # 显示下载信息
        logging.info(f'书名: {novel_info["title"]}')
        logging.info(f'作者: {novel_info["author"]}')
        logging.info(f'状态: {novel_info["status"]}')
        logging.info(f'评分: {novel_info["score"]}')
        logging.info(f'分类: {", ".join(novel_info["categories"])}')
        logging.info(f'字数: {novel_info["word_count"]}')
        logging.info(f'总章节数: {len(novel_info["chapters"])}')
        
        # 确认是否继续
        confirm = input('确认下载？(y/n): ').strip().lower()
        if confirm != 'y':
            logging.info('已取消下载')
            return
        
        # 获取封面图片
        logging.info('正在获取封面图片...')
        cover_data = downloader.get_cover_image(url)
        
        # 创建EPUB生成器
        epub_creator = EpubCreator(novel_info, cover_data)
        
        # 下载所有章节
        total_chapters = len(novel_info['chapters'])
        for i, (chapter_title, chapter_url) in enumerate(novel_info['chapters'], 1):
            logging.info(f'正在下载章节 {i}/{total_chapters}: {chapter_title}')
            content = downloader.get_chapter_content(chapter_url)
            if content:
                epub_creator.add_chapter(chapter_title, content)
            else:
                logging.warning(f'章节 {chapter_title} 下载失败')
            time.sleep(1)  # 防止请求过快
        
        # 生成文件名
        output_file = f"{novel_info['title']}_{novel_info['author']}.epub"
        output_file = ''.join(c for c in output_file if c.isalnum() or c in (' ', '-', '_', '.'))
        
        # 生成EPUB文件
        logging.info('正在生成EPUB文件...')
        if epub_creator.create_epub(output_file):
            logging.info('转换完成！')
            logging.info(f'文件保存为: {output_file}')
        else:
            logging.error('转换失败。')
            
    except KeyboardInterrupt:
        logging.info('\n用户中断下载')
    except Exception as e:
        logging.error(f'发生错误: {str(e)}')

if __name__ == '__main__':
    main()