"""
首先打开言情小说网网站
"https://www.yqzwxs.com/"
然后安装各种库
pip install requests beautifulsoup4 ebooklib requests[socks]
ID为：5_13844这种格式
需要魔法上网
"""

import requests
from bs4 import BeautifulSoup
import os
import re
from dataclasses import dataclass
from datetime import datetime
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4.element import Tag
import ebooklib
from ebooklib import epub
from tqdm import tqdm
import html2text
import random
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class Chapter:
    title: str
    url: str
    chapter_number: int
    content: str = ""  # 添加content字段

@dataclass
class Book:
    title: str
    author: str
    word_count: str
    readers: str
    status: str
    cover_url: str
    description: str
    latest_chapter: str
    latest_chapter_url: str
    update_time: datetime
    book_id: str

def create_session() -> requests.Session:
    """创建一个带有重试机制的会话"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # 最多重试3次
        backoff_factor=0.5,  # 重试之间的等待时间
        status_forcelist=[500, 502, 503, 504, 429]  # 这些状态码会触发重试
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, 
                        pool_connections=100,  # 连接池大小
                        pool_maxsize=100)  # 最大连接数
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    })
    return session

def parse_book_info(html_content: str, book_id: str) -> Book:
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找书籍信息容器
    book_div = soup.find('div', class_='book')
    if not book_div:
        raise ValueError("未找到书籍信息")
    
    # 获取封面图片URL
    cover_url = ""
    cover_img = book_div.find('img', class_='thumbnail')
    if cover_img and cover_img.get('src'):
        cover_url = cover_img['src']
        if not cover_url.startswith('http'):
            cover_url = f"https:{cover_url}"
    
    # 获取标题
    title = ""
    title_elem = book_div.find('h1', class_='booktitle')
    if title_elem:
        title = title_elem.text.strip()
    
    # 获取作者、字数、阅读量和状态
    author = ""
    word_count = ""
    readers = ""
    status = ""
    
    booktag = book_div.find('p', class_='booktag')
    if booktag:
        # 获取作者
        author_link = booktag.find('a', class_='red')
        if author_link:
            author = author_link.text.strip()
        
        # 获取其他信息
        spans = booktag.find_all('span', class_='blue')
        if len(spans) >= 2:
            word_count = spans[0].text.strip()
            readers = spans[1].text.strip()
        
        # 获取状态
        status_span = booktag.find('span', class_='red')
        if status_span and status_span != author_link:
            status = status_span.text.strip()
    
    # 获取简介
    description = ""
    intro = book_div.find('p', class_='bookintro')
    if intro:
        # 移除简介中的图片标签
        for img in intro.find_all('img'):
            img.decompose()
        # 获取简介文本并清理
        description = intro.text.strip()
        # 移除相关推荐和网站信息
        description = re.sub(r'《.*?》是.*?最新章节.*$', '', description, flags=re.DOTALL).strip()
        description = re.sub(r'相关推荐：.*$', '', description, flags=re.DOTALL).strip()
        # 移除多余的空白字符
        description = re.sub(r'\s+', ' ', description).strip()
        # 只保留第一个<br>之前的内容（通常是真正的简介）
        if '<br>' in description:
            description = description.split('<br>')[0].strip()
    
    # 获取最新章节
    latest_chapter = ""
    latest_chapter_url = ""
    chapter_link = book_div.find('a', class_='bookchapter')
    if chapter_link:
        latest_chapter = chapter_link.text.strip()
        latest_chapter_url = chapter_link.get('href', '')
        if latest_chapter_url and not latest_chapter_url.startswith('http'):
            latest_chapter_url = f"https://www.yqzwxs.com{latest_chapter_url}"
    
    # 获取更新时间
    update_time = datetime.now()
    time_p = book_div.find('p', class_='booktime')
    if time_p:
        time_text = time_p.text.strip()
        time_match = re.search(r'更新时间：(.*)', time_text)
        if time_match:
            try:
                update_time = datetime.strptime(time_match.group(1).strip(), '%Y-%m-%d %H:%M:%S')
            except:
                pass
    
    return Book(
        title=title,
        author=author,
        word_count=word_count,
        readers=readers,
        status=status,
        cover_url=cover_url,
        description=description,
        latest_chapter=latest_chapter,
        latest_chapter_url=latest_chapter_url,
        update_time=update_time,
        book_id=book_id
    )

def validate_book_id(book_id: str) -> bool:
    """验证书籍ID格式是否正确"""
    return bool(re.match(r'^\d+_\d+$', book_id))

def download_book_info(book_id: str) -> Book:
    """下载书籍信息，包含重试机制"""
    session = create_session()
    urls = [
        f"https://www.yqzwxs.com/{book_id}",
        f"http://www.yqzwxs.com/{book_id}",
    ]
    
    last_error = None
    for url in urls:
        try:
            response = session.get(url, timeout=10)
            response.encoding = 'utf-8'
            return parse_book_info(response.text, book_id)
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"尝试访问 {url} 失败，尝试其他地址...")
            time.sleep(1)
            
    raise Exception(f"无法获取书籍信息: {str(last_error)}")

def parse_chapter_link(chapter_element) -> Chapter:
    """Parse a chapter link element into a Chapter object."""
    link = chapter_element.find('a')
    title = link.get('title', '').strip()
    url = link.get('href', '').strip()
    # Extract chapter number from the title (assuming format "第X章")
    chapter_match = re.search(r'第(\d+)章', title)
    chapter_number = int(chapter_match.group(1)) if chapter_match else 0
    return Chapter(title=title, url=url, chapter_number=chapter_number)

def get_chapter_list(book_id: str) -> list[Chapter]:
    """获取章节列表，包含重试机制"""
    session = create_session()
    urls = [
        f"https://www.yqzwxs.com/{book_id}",
        f"http://www.yqzwxs.com/{book_id}",
    ]
    
    last_error = None
    for url in urls:
        try:
            response = session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            chapters = []
            # 查找章节列表容器
            chapter_container = soup.find('div', id='list-chapterAll')
            if not chapter_container:
                chapter_container = soup.find('div', class_='book_list')
            
            if chapter_container:
                # 查找所有章节链接
                chapter_links = chapter_container.find_all('dd')
                if not chapter_links:  # 如果没有找到dd标签，尝试直接查找a标签
                    chapter_links = chapter_container.find_all('a')
                    
                for item in chapter_links:
                    link = item.find('a') if isinstance(item, Tag) else item
                    if not link:
                        continue
                        
                    title = link.text.strip()
                    url = link.get('href', '')
                    
                    # 确保URL是完整的
                    if url.startswith('/'):
                        url = f"https://www.yqzwxs.com{url}"
                    
                    # 提取章节号
                    chapter_match = re.search(r'第(\d+)章', title)
                    if chapter_match:
                        chapter_number = int(chapter_match.group(1))
                        chapters.append(Chapter(
                            title=title,
                            url=url,
                            chapter_number=chapter_number
                        ))
            
            if chapters:  # 只有在找到章节时才返回
                return sorted(chapters, key=lambda x: x.chapter_number)
            
        except Exception as e:
            last_error = e
            print(f"尝试访问 {url} 失败，尝试其他地址...")
            time.sleep(1)
            
    raise Exception(f"无法获取章节列表: {str(last_error) if last_error else '未找到任何章节'}")

def download_chapter_content(session: requests.Session, chapter: Chapter, page_url: str = None) -> tuple[Chapter, str]:
    """下载章节内容，支持分页"""
    try:
        # 使用传入的页面URL或章节URL
        url = page_url if page_url else chapter.url
        if not url.startswith('http'):
            url = f"https://www.yqzwxs.com{url}"
            
        response = session.get(url, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找内容容器 - 首先查找readcontent，然后是其他可能的容器
        content_div = soup.find('div', class_='readcontent')
        if not content_div:
            content_div = soup.find('div', id='content')
        if not content_div:
            content_div = soup.find('div', class_='content')
        if not content_div:
            return chapter, ""
            
        # 移除所有script标签
        for script in content_div.find_all('script'):
            script.decompose()
            
        # 移除所有广告div
        for div in content_div.find_all('div', class_=lambda x: x and ('ad' in x.lower() or 'google' in x.lower())):
            div.decompose()
            
        # 移除返回顶部链接
        for a in content_div.find_all('a'):
            if '返回顶部' in a.text:
                a.decompose()
                
        # 获取所有p标签内容
        paragraphs = []
        found_recommendations = False
        for p in content_div.find_all('p'):
            text = p.get_text().strip()
            # 如果遇到"相关推荐："就停止获取后续内容
            if '相关推荐：' in text:
                found_recommendations = True
                break
                
            if text and not any(skip in text for skip in [
                '最新章节', '言情中文网', '手机阅读', '首发网站', 
                '本章未完', '加入书签', '推荐上一页',
                '下载本书', '更新速度最快', '免费阅读'
            ]):
                # 清理特殊字符
                text = text.replace('&amp;#x38c9;', '入')  # 处理特殊字符
                text = re.sub(r'\s+', ' ', text)  # 规范化空白字符
                paragraphs.append(text)
        
        # 过滤重复内容
        unique_paragraphs = []
        seen = set()
        for p in paragraphs:
            if p not in seen and len(p) > 1:  # 只保留长度大于1的段落
                seen.add(p)
                unique_paragraphs.append(p)
        
        # 查找下一页链接 - 使用id="linkNext"
        next_page_url = None
        next_page_link = soup.find('a', id='linkNext')
        if next_page_link and '下一页' in next_page_link.text:
            next_page_url = next_page_link.get('href')
            if next_page_url and not next_page_url.startswith('http'):
                next_page_url = f"https://www.yqzwxs.com{next_page_url}"
        
        # 获取当前页内容
        current_content = '\n\n'.join('    ' + p for p in unique_paragraphs)
        
        # 如果有下一页，递归获取下一页内容
        if next_page_url and next_page_url != url:  # 避免重复获取同一页
            _, next_page_content = download_chapter_content(session, chapter, next_page_url)
            if next_page_content:
                current_content = current_content.strip() + '\n\n' + next_page_content.strip()
        
        return chapter, current_content.strip()
        
    except Exception as e:
        print(f"\n下载章节 {chapter.title} 失败: {str(e)}")
        return chapter, ""

def download_all_chapters(session: requests.Session, chapters: list[Chapter]) -> list[Chapter]:
    """并发下载所有章节内容"""
    print("\n开始下载章节内容...")
    failed_chapters = []
    max_workers = min(32, len(chapters))  # 最大并发数
    
    # 创建进度条
    pbar = tqdm(total=len(chapters), desc="下载进度")
    
    # 使用线程池进行并发下载
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有下载任务
        future_to_chapter = {
            executor.submit(download_chapter_content, session, chapter): chapter 
            for chapter in chapters
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_chapter):
            chapter, content = future.result()
            if content:
                chapter.content = content
            else:
                failed_chapters.append(chapter)
                print(f"\n警告: 章节 {chapter.title} 下载失败")
            pbar.update(1)
    
    pbar.close()
    
    if failed_chapters:
        print(f"\n总共有 {len(failed_chapters)} 个章节下载失败:")
        for chapter in failed_chapters:
            print(f"- {chapter.title}")
            
        # 重试失败的章节
        if failed_chapters:
            print("\n正在重试失败的章节...")
            retry_pbar = tqdm(total=len(failed_chapters), desc="重试进度")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_chapter = {
                    executor.submit(download_chapter_content, session, chapter): chapter 
                    for chapter in failed_chapters
                }
                
                for future in as_completed(future_to_chapter):
                    chapter, content = future.result()
                    if content:
                        chapter.content = content
                    retry_pbar.update(1)
            
            retry_pbar.close()
    
    return chapters

def create_epub(book: Book, chapters: list[Chapter], output_dir: str = "downloads") -> str:
    """创建EPUB电子书"""
    try:
        # 创建保存目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建epub书籍
        epub_book = epub.EpubBook()
        
        # 设置书籍信息
        epub_book.set_identifier(f'yqzw_{book.book_id}_{int(time.time())}')
        epub_book.set_title(book.title)
        epub_book.set_language('zh-CN')
        epub_book.add_author(book.author)
        
        # 下载并添加封面图片
        if book.cover_url:
            try:
                session = create_session()
                response = session.get(book.cover_url, timeout=10)
                if response.status_code == 200:
                    # 添加封面图片
                    epub_book.set_cover("cover.jpg", response.content)
            except Exception as e:
                print(f"下载封面图片失败: {str(e)}")
        
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
            img.cover {
                max-width: 100%;
                max-height: 100%;
                display: block;
                margin: 0 auto;
            }
        '''
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        epub_book.add_item(nav_css)
        
        # 添加封面页
        cover_content = f'''
            <html>
            <head>
                <title>{book.title}</title>
                <style>
                    body {{ margin: 5%; text-align: center; }}
                    h1 {{ margin: 2em 0; }}
                    .meta {{ margin: 1em 0; text-align: center; }}
                    .intro {{ margin: 2em; padding: 1em; border: 1px solid #ccc; text-align: justify; }}
                    .intro h2 {{ text-align: center; }}
                    img.cover {{ max-width: 100%; max-height: 80vh; display: block; margin: 2em auto; }}
                </style>
            </head>
            <body>
                <h1>{book.title}</h1>
                {'<img class="cover" src="cover.jpg" alt="封面"/>' if book.cover_url else ''}
                <div class="meta">
                    <p><strong>作者：</strong>{book.author}</p>
                    <p><strong>字数：</strong>{book.word_count}</p>
                    <p><strong>状态：</strong>{book.status}</p>
                    <p><strong>最新章节：</strong>{book.latest_chapter}</p>
                    <p><strong>更新时间：</strong>{book.update_time}</p>
                </div>
                <div class="intro">
                    <h2>简介</h2>
                    <p>{book.description}</p>
                </div>
            </body>
            </html>
        '''
        cover = epub.EpubHtml(title='封面', file_name='cover.xhtml', content=cover_content, lang='zh-CN')
        cover.add_item(nav_css)
        epub_book.add_item(cover)
        
        # 创建章节
        epub_chapters = [cover]  # 添加封面到目录
        for chapter in chapters:
            if not chapter.content:  # 跳过没有内容的章节
                continue
                
            # 创建章节
            epub_chapter = epub.EpubHtml(title=chapter.title,
                                       file_name=f'chapter_{chapter.chapter_number}.xhtml',
                                       lang='zh-CN')
            
            # 设置章节内容，将内容分段
            paragraphs = [p.strip() for p in chapter.content.split('\n\n') if p.strip()]
            chapter_html = f'<h1>{chapter.title}</h1>\n'
            chapter_html += '\n'.join(f'<p>{p.lstrip()}' for p in paragraphs)
            
            epub_chapter.content = chapter_html
            epub_chapter.add_item(nav_css)
            
            # 添加章节
            epub_book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
        
        # 创建目录
        epub_book.toc = epub_chapters
        epub_book.add_item(epub.EpubNcx())
        epub_book.add_item(epub.EpubNav())
        
        # 设置阅读顺序
        epub_book.spine = ['nav'] + epub_chapters
        
        # 生成文件名（移除文件名中的非法字符）
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', book.title)
        safe_author = re.sub(r'[<>:"/\\|?*]', '_', book.author)
        filename = f"{safe_title}_{safe_author}.epub"
        filepath = os.path.join(output_dir, filename)
        
        # 保存EPUB文件
        epub.write_epub(filepath, epub_book, {})
        
        return filepath
    except Exception as e:
        print(f"\n创建EPUB文件失败: {str(e)}")
        return ""

def main():
    while True:
        print("\n欢迎使用言情小说下载器")
        print("请输入小说ID（例如：5_13844）")
        print("输入 'q' 退出程序")
        
        book_id = input("请输入: ").strip().rstrip('/')
        
        if book_id.lower() == 'q':
            print("程序已退出")
            break
            
        if not validate_book_id(book_id):
            print("错误：ID格式不正确！请输入正确的格式：数字_数字（例如：5_13844）")
            continue
            
        try:
            print("\n正在获取书籍信息...")
            book = download_book_info(book_id)
            print(f"\n书籍信息:")
            print(f"标题: {book.title}")
            print(f"作者: {book.author}")
            print(f"字数: {book.word_count}")
            print(f"阅读量: {book.readers}")
            print(f"状态: {book.status}")
            print(f"最新章节: {book.latest_chapter}")
            print(f"更新时间: {book.update_time}")
            print("\n简介:")
            print(book.description)
            
            print("\n正在获取章节列表...")
            chapters = get_chapter_list(book_id)
            print(f"\n总共找到 {len(chapters)} 个章节")
            print("\n前5个章节:")
            for chapter in chapters[:5]:
                print(f"第{chapter.chapter_number}章: {chapter.title}")
            
            if len(chapters) > 5:
                print(f"\n最新5个章节:")
                for chapter in chapters[-5:]:
                    print(f"第{chapter.chapter_number}章: {chapter.title}")
            
            # 询问是否下载
            print("\n是否下载全部章节并保存为EPUB格式？(y/n)")
            if input().strip().lower() == 'y':
                session = create_session()
                chapters = download_all_chapters(session, chapters)
                
                print("\n正在生成EPUB文件...")
                epub_path = create_epub(book, chapters)
                if epub_path:
                    print(f"\nEPUB文件已保存到: {epub_path}")
                
            print("\n是否继续查看其他小说？(y/n)")
            choice = input().strip().lower()
            if choice != 'y':
                print("程序已退出")
                break
                
        except Exception as e:
            print(f"发生错误: {str(e)}")
            print("\n可能的解决方案:")
            print("1. 检查网络连接是否正常")
            print("2. 尝试使用VPN或代理")
            print("3. 网站域名可能已更改，请确认最新域名")
            print("4. 确认输入的小说ID是否正确")
            print("5. 等待一段时间后重试")

if __name__ == "__main__":
    main()

