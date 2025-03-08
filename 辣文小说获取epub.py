"""
https://www.aaqqcc.com/book/
辣文小说获取epub.py
获取小说信息
获取小说章节列表
获取小说章节内容
获取小说封面图片
生成epub文件
首先安装这些库 pip install requests beautifulsoup4 ebooklib tqdm concurrent-futures

18+小说
下载需要魔法
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
import concurrent.futures
from tqdm import tqdm

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
        self.max_workers = 5  # 并发下载线程数
        self.timeout = 10

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
        """获取章节内容"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout)
                if response.status_code != 200:
                    raise ValueError(f"HTTP请求失败，状态码: {response.status_code}")
                    
                response.encoding = response.apparent_encoding or 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 获取章节内容
                content_div = soup.select_one('div#content')
                if not content_div:
                    raise ValueError("未找到章节内容")

                # 1. 清理广告和无用内容
                for tag in content_div.find_all(['script', 'style', 'a']):
                    tag.decompose()
                
                # 2. 获取原始文本并分行
                lines = []
                for line in content_div.stripped_strings:
                    line = line.strip()
                    if line:
                        # 过滤广告和无用内容
                        if any(ad in line.lower() for ad in ['aaqqcc', 'jizai', '.com', 'www', 'http', '最新章节', '加入书签', '投票推荐']):
                            continue
                        if len(line) < 2:  # 跳过太短的行
                            continue
                        lines.append(line)

                # 3. 智能分段处理
                paragraphs = []
                current_paragraph = []
                
                for line in lines:
                    # 处理对话
                    is_dialogue = line.startswith(("「", "『", """, """, "'", '"'))
                    
                    # 如果是对话或者很短的句子，单独成段
                    if is_dialogue or len(line) < 20:
                        if current_paragraph:
                            paragraphs.append(''.join(current_paragraph))
                            current_paragraph = []
                        paragraphs.append(line)
                        continue
                    
                    # 处理普通段落
                    if any(line.endswith(end) for end in ["。", "！", "？", "…", "!", "?", "...", '"', "」", "』"]):
                        current_paragraph.append(line)
                        paragraphs.append(''.join(current_paragraph))
                        current_paragraph = []
                    else:
                        current_paragraph.append(line)
                
                # 处理最后一个段落
                if current_paragraph:
                    paragraphs.append(''.join(current_paragraph))

                # 4. 格式化HTML
                formatted_content = []
                for p in paragraphs:
                    p = p.strip()
                    if not p:  # 跳过空段落
                        continue
                        
                    # 处理对话和普通段落
                    if any(p.startswith(quote) for quote in ["「", "『", """, """, "'", '"']):
                        formatted_content.append(f'<p class="dialogue">{p}</p>')
                    else:
                        formatted_content.append(f'<p>{p}</p>')

                content = '\n'.join(formatted_content)
                
                # 5. 验证内容
                if not content or len(content) < 50:  # 内容太短可能是错误的
                    raise ValueError("章节内容异常")
                    
                return content

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))
                    continue
                raise

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

    def download_chapter(self, chapter_title, chapter_url):
        """下载单个章节的包装函数"""
        try:
            content = self.get_chapter_content(chapter_url)
            return {'title': chapter_title, 'content': content}
        except Exception as e:
            logging.error(f"下载章节失败 {chapter_title}: {str(e)}")
            return None

class EpubCreator:
    def __init__(self, novel_info, cover_data=None):
        self.novel_info = novel_info
        self.book = epub.EpubBook()
        self.chapters = []
        self.cover_data = cover_data
        self.css_style = '''
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

    def create_epub(self, output_file):
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
                self.book.set_cover("cover.jpg", self.cover_data)

            # 添加CSS样式
            nav_css = epub.EpubItem(
                uid="style_nav",
                file_name="style/nav.css",
                media_type="text/css",
                content=self.css_style
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
                chapter.content = f'''<html>
                <head></head>
                <body>
                    <h1>{title}</h1>
                    <div class="chapter-content">
                        {content}
                    </div>
                </body>
                </html>'''
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
            epub.write_epub(output_file, self.book, {})
            logging.info(f'已成功生成epub文件: {output_file}')
            return True

        except Exception as e:
            logging.error(f'生成epub文件时出错: {str(e)}')
            return False

    def add_chapter(self, title, content):
        self.chapters.append((title, content))

def main():
    try:
        while True:
            # 获取用户输入
            print("\n小说ID格式说明：")
            print("1. ID是网址中的数字，例如：https://www.aaqqcc.com/book/4210 中的 4210")
            print("2. 可以直接复制完整网址，程序会自动提取ID")
            print("3. 也可以直接输入数字ID\n")
            
            while True:
                novel_id = input("请输入小说ID或网址: ").strip()
                
                # 如果输入的是完整URL，提取ID
                if 'aaqqcc.com' in novel_id:
                    try:
                        novel_id = re.search(r'/book/(\d+)', novel_id).group(1)
                    except:
                        print("无法从URL中提取ID，请直接输入数字ID")
                        continue
                
                # 验证ID是否为纯数字
                if not novel_id.isdigit():
                    print("ID格式错误！请输入纯数字ID或完整网址")
                    continue
                    
                break
            
            # 创建下载器
            downloader = NovelDownloader()
            
            # 获取小说信息
            logging.info('正在获取小说信息...')
            try:
                novel_info = downloader.get_novel_info(f'https://www.aaqqcc.com/book/{novel_id}')
            except Exception as e:
                logging.error(f"获取小说信息失败: {str(e)}")
                continue
                
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
                continue
            
            # 获取封面图片
            logging.info('正在获取封面图片...')
            cover_data = downloader.get_cover_image(f'https://www.aaqqcc.com/book/{novel_id}')
            
            # 创建EPUB生成器
            epub_creator = EpubCreator(novel_info, cover_data)
            
            # 使用线程池并发下载章节
            logging.info('开始下载章节...')
            chapters = novel_info['chapters']
            downloaded_chapters = []  # 用于保存下载的章节
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=downloader.max_workers) as executor:
                # 创建一个字典来跟踪每个章节的原始索引
                chapter_indices = {(title, url): idx for idx, (title, url) in enumerate(chapters)}
                futures = {executor.submit(downloader.download_chapter, title, url): (idx, title, url) 
                         for idx, (title, url) in enumerate(chapters)}
                
                with tqdm(total=len(chapters), desc="下载进度", unit="章") as pbar:
                    # 预分配空间
                    downloaded_chapters = [None] * len(chapters)
                    
                    for future in concurrent.futures.as_completed(futures):
                        idx, title, url = futures[future]
                        try:
                            result = future.result()
                            if result:
                                # 按原始顺序保存章节
                                downloaded_chapters[idx] = result
                        except Exception as e:
                            logging.error(f"\n下载章节 {title} 失败: {str(e)}")
                        pbar.update(1)
            
            # 过滤掉下载失败的章节并添加到epub
            successful_chapters = [chapter for chapter in downloaded_chapters if chapter is not None]
            
            if not successful_chapters:
                logging.error("所有章节下载失败")
                continue
                
            if len(successful_chapters) < len(chapters):
                logging.warning(f"部分章节下载失败: 成功 {len(successful_chapters)}/{len(chapters)}")
                
            # 添加到epub创建器
            for chapter in successful_chapters:
                epub_creator.add_chapter(chapter['title'], chapter['content'])
            
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
            
            # 询问是否继续下载其他小说
            while True:
                choice = input("\n是否继续下载其他小说？(y/q): ").lower().strip()
                if choice in ['y', 'q']:
                    break
                print("无效的输入，请输入 y 继续下载或 q 退出")
            
            if choice == 'q':
                print("\n感谢使用，再见！")
                break
                
    except KeyboardInterrupt:
        logging.info('\n用户中断下载')
    except Exception as e:
        logging.error(f'发生错误: {str(e)}')
        # 发生错误时也询问是否继续
        while True:
            choice = input("\n是否重试？(y/q): ").lower().strip()
            if choice in ['y', 'q']:
                break
            print("无效的输入，请输入 y 重试或 q 退出")
        
        if choice == 'y':
            print("\n重新开始...")
            main()  # 递归调用
        else:
            print("\n感谢使用，再见！")

if __name__ == '__main__':
    main()