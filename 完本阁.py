"""
首先打开完本阁小说网站
"https://www.jizai22.com/"
然后安装各种库
pip install requests beautifulsoup4 ebooklib tqdm concurrent-futures

https://www.jizai22.com/info/80815.html

id=80815

18+

需要魔法才能下载
"""
import requests
from bs4 import BeautifulSoup
from ebooklib import epub
import time
import logging
from urllib.parse import urljoin
import re
import concurrent.futures
from tqdm import tqdm
import os

class NovelDownloader:
    def __init__(self):
        self.base_url = "https://www.jizai22.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.jizai22.com/'
        }
        self.timeout = 10
        self.max_retries = 3
        self.retry_delay = 1
        self.session = requests.Session()
        self.max_workers = 5  # 并发下载线程数

    def get_novel_info(self, novel_id):
        """获取小说信息"""
        try:
            url = f"{self.base_url}/info/{novel_id}.html"
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            response.encoding = response.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # 获取小说信息
            info = {}
            
            # 获取标题
            title_elem = soup.find('h1', class_='bookTitle')
            info['title'] = title_elem.text.strip() if title_elem else "未知标题"
            
            # 获取作者、分类、字数等信息
            # 找到所有booktag，排除text-center的
            booktags = soup.find_all('p', class_='booktag')
            booktag = None
            for tag in booktags:
                if 'text-center' not in tag.get('class', []):
                    booktag = tag
                    break
                    
            if booktag:
                # 获取作者
                author_link = booktag.find('a', title=lambda x: x and x.startswith('作者：'))
                info['author'] = author_link.text.strip() if author_link else '未知'
                
                # 获取分类
                category_link = booktag.find('a', href=lambda x: x and '/list/' in x)
                info['category'] = category_link.text.strip() if category_link else '未知'
                
                # 获取字数和状态
                for span in booktag.find_all('span', class_='blue'):
                    text = span.text.strip()
                    if '字数：' in text:
                        info['word_count'] = text.replace('字数：', '').strip()
                    elif any(s in text for s in ['连载中', '已完结']):
                        info['status'] = text.strip()
            
            # 获取最后更新时间
            update_p = soup.find('p', text=lambda x: x and '更新时间：' in x)
            if update_p:
                info['update_time'] = update_p.text.replace('更新时间：', '').strip()
            else:
                latest_chapter = soup.find('p', text=lambda x: x and '最新章节：' in x)
                if latest_chapter:
                    time_span = latest_chapter.find('span', class_='hidden-xs')
                    if time_span:
                        time_text = time_span.text.strip('()')
                        info['update_time'] = time_text
                    else:
                        info['update_time'] = time.strftime('%Y-%m-%d %H:%M')
            
            # 获取简介
            intro_p = soup.find('p', class_='text-muted', id='bookIntro')
            if intro_p:
                # 移除简介中的图片元素
                for img in intro_p.find_all('img'):
                    img.decompose()
                info['intro'] = intro_p.text.strip()
            else:
                info['intro'] = "暂无简介"

            # 获取封面图片
            cover_img = soup.find('img', class_='img-thumbnail', alt=lambda x: x and x == info['title'])
            if cover_img and cover_img.get('src'):
                cover_url = cover_img['src']
                if not cover_url.startswith('http'):
                    if cover_url.startswith('//'):
                        cover_url = 'https:' + cover_url
                    else:
                        cover_url = urljoin(self.base_url, cover_url)
                info['cover_url'] = cover_url

            # 设置默认值
            for key in ['author', 'category', 'word_count', 'status', 'update_time']:
                if key not in info:
                    info[key] = '未知'

            return info

        except Exception as e:
            logging.error(f"获取小说信息失败: {str(e)}")
            return {
                'title': "未知标题",
                'author': "未知",
                'category': "网络小说",
                'word_count': "未知",
                'status': "未知",
                'update_time': time.strftime('%Y-%m-%d'),
                'intro': "暂无简介"
            }

    def get_chapter_list(self, novel_id):
        """获取小说章节列表"""
        try:
            url = f"{self.base_url}/info/{novel_id}.html"
            response = self.session.get(url, headers=self.headers)
            if response.status_code != 200:
                raise ValueError(f"HTTP请求失败，状态码: {response.status_code}")
                
            response.encoding = response.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            chapter_list = []
            chapter_items = soup.find_all('dd', class_='col-md-3')
            
            for item in chapter_items:
                link = item.find('a')
                if link:
                    chapter_url = link.get('href')
                    chapter_title = link.get('title') or link.text.strip()
                    
                    try:
                        chapter_title = chapter_title.encode('utf-8').decode('utf-8')
                    except UnicodeError:
                        chapter_title = chapter_title.encode('latin1').decode('utf-8', errors='ignore')
                    
                    chapter_title = re.sub(r'\s+[a-zA-Z0-9.]+\s*$', '', chapter_title)
                    chapter_title = re.sub(r'\s*\([^)]*\)\s*$', '', chapter_title)
                    
                    if chapter_url:
                        if chapter_url.startswith('http'):
                            chapter_url = '/' + '/'.join(chapter_url.split('/')[3:])
                        if not chapter_url.startswith('/'):
                            chapter_url = '/' + chapter_url
                        
                        full_url = urljoin(self.base_url, chapter_url)
                        
                        if chapter_title and full_url:
                            chapter_list.append({
                                'title': chapter_title,
                                'url': full_url
                            })

            if not chapter_list:
                raise ValueError("未找到任何章节")

            return chapter_list

        except Exception as e:
            logging.error(f"获取章节列表失败: {str(e)}")
            raise

    def get_chapter_content(self, chapter_url):
        """获取章节内容"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(chapter_url, headers=self.headers, timeout=self.timeout)
                if response.status_code != 200:
                    raise ValueError(f"HTTP请求失败，状态码: {response.status_code}")
                    
                response.encoding = response.apparent_encoding or 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')

                title = soup.find('h1', class_='readTitle')
                chapter_title = title.text.strip() if title else ""
                
                try:
                    chapter_title = chapter_title.encode('utf-8').decode('utf-8')
                except UnicodeError:
                    chapter_title = chapter_title.encode('latin1').decode('utf-8', errors='ignore')

                content_div = soup.find('div', id='content')
                if not content_div:
                    raise ValueError("未找到章节内容")

                # 移除导航和功能按钮
                for tag in content_div.find_all('p', class_='text-center'):
                    tag.decompose()
                
                # 移除所有的链接
                for tag in content_div.find_all('a'):
                    tag.decompose()

                # 优化文本处理
                content = content_div.get_text('\n')
                
                # 1. 移除广告和无用内容
                content = re.sub(r'[（(].{1,30}[)）]', '', content)  # 移除括号中的广告
                content = re.sub(r'.*[jJ][iI][zZ][aA][iI].*\n?', '', content)  # 移除包含jizai的行
                content = re.sub(r'.*[.][cC][oO][mM].*\n?', '', content)  # 移除包含.com的行
                content = re.sub(r'.*www.*\n?', '', content)  # 移除包含www的行
                content = re.sub(r'.*http.*\n?', '', content)  # 移除包含http的行
                content = re.sub(r'.*投票推荐.*\n?', '', content)  # 移除投票推荐
                content = re.sub(r'.*加入书签.*\n?', '', content)  # 移除加入书签
                content = re.sub(r'.*留言反馈.*\n?', '', content)  # 移除留言反馈
                content = re.sub(r'.*催更报错.*\n?', '', content)  # 移除催更报错
                content = re.sub(r'.*fa-\w+.*\n?', '', content)  # 移除font-awesome图标相关文本
                
                # 2. 分段处理
                paragraphs = []
                # 按照换行符分割文本
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                
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
                
                # 3. 格式化HTML
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
                    
                return chapter_title, content

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise

    def download_chapter(self, chapter):
        """下载单个章节的包装函数"""
        try:
            title, content = self.get_chapter_content(chapter['url'])
            return {'title': title, 'content': content}
        except Exception as e:
            logging.error(f"下载章节失败 {chapter['title']}: {str(e)}")
            return None

    def create_epub(self, novel_info, chapters):
        """创建epub电子书"""
        try:
            book = epub.EpubBook()

            # 设置元数据
            book.set_identifier(f'novel_{int(time.time())}')
            book.set_title(novel_info['title'])
            book.set_language('zh-CN')
            book.add_author(novel_info['author'])

            # 添加封面图片
            if novel_info.get('cover_url'):
                try:
                    cover_response = self.session.get(novel_info['cover_url'], headers=self.headers)
                    if cover_response.status_code == 200:
                        book.set_cover("cover.jpg", cover_response.content)
                except Exception as e:
                    logging.warning(f"下载封面图片失败: {str(e)}")

            # 创建简介章节
            intro = epub.EpubHtml(title='简介', file_name='intro.xhtml')
            intro_content = f"""<html>
            <head></head>
            <body>
                <h1>{novel_info['title']}</h1>
                <p><strong>作者：</strong>{novel_info['author']}</p>
                <p><strong>分类：</strong>{novel_info['category']}</p>
                <p><strong>字数：</strong>{novel_info['word_count']}</p>
                <p><strong>状态：</strong>{novel_info['status']}</p>
                <p><strong>最后更新：</strong>{novel_info['update_time']}</p>
                <h2>简介</h2>
                <p>{novel_info['intro']}</p>
            </body>
            </html>"""
            intro.content = intro_content
            book.add_item(intro)

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
            nav_css = epub.EpubItem(
                uid="style_nav",
                file_name="style/nav.css",
                media_type="text/css",
                content=style
            )
            book.add_item(nav_css)

            # 添加章节
            chapter_items = []
            for i, chapter in enumerate(chapters, 1):
                if not chapter.get('content'):
                    continue
                    
                c = epub.EpubHtml(
                    title=chapter['title'],
                    file_name=f'chapter_{i}.xhtml',
                    lang='zh-CN'
                )
                c.content = f'''<html>
                <head></head>
                <body>
                    <h1>{chapter["title"]}</h1>
                    <div class="chapter-content">
                        {chapter["content"]}
                    </div>
                </body>
                </html>'''
                c.add_item(nav_css)
                book.add_item(c)
                chapter_items.append(c)

            # 创建目录
            book.toc = [intro] + chapter_items
            book.spine = ['nav', intro] + chapter_items

            # 添加导航
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # 生成epub文件
            filename = f"{novel_info['title']}.epub"
            # 处理文件名中的非法字符
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            epub.write_epub(filename, book)
            return True

        except Exception as e:
            logging.error(f"创建epub失败: {str(e)}")
            raise

def main():
    try:
        downloader = NovelDownloader()
        novel_id = input("请输入小说ID: ")
        
        print("获取小说信息...")
        novel_info = downloader.get_novel_info(novel_id)
        print(f"书名：{novel_info['title']}")
        print(f"作者：{novel_info['author']}")
        
        print("\n获取章节列表...")
        chapters = downloader.get_chapter_list(novel_id)
        print(f"找到 {len(chapters)} 个章节")

        # 使用线程池并发下载章节
        print("\n开始下载章节...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=downloader.max_workers) as executor:
            # 创建进度条
            futures = {executor.submit(downloader.download_chapter, chapter): chapter for chapter in chapters}
            
            with tqdm(total=len(chapters), desc="下载进度", unit="章") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    chapter = futures[future]
                    try:
                        result = future.result()
                        if result:
                            chapter.update(result)
                    except Exception as e:
                        print(f"\n下载章节 {chapter['title']} 失败: {str(e)}")
                    pbar.update(1)

        print("\n创建电子书...")
        if downloader.create_epub(novel_info, chapters):
            filename = re.sub(r'[<>:"/\\|?*]', '_', f"{novel_info['title']}.epub")
            print(f"\n电子书已生成: {filename}")

    except KeyboardInterrupt:
        print("\n用户取消下载")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == '__main__':
    main()

