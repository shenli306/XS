#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import json
import shutil
import zipfile
import tempfile
import argparse
import subprocess
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm.auto import tqdm

def find_ffmpeg():
    """查找系统中的FFmpeg路径"""
    path_ffmpeg = shutil.which('ffmpeg')
    if path_ffmpeg:
        return path_ffmpeg

    possible_paths = [
        os.path.expandvars("%USERPROFILE%/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg.exe"),
        os.path.expandvars("%USERPROFILE%/AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"),
        os.path.expandvars("%PROGRAMFILES%/ffmpeg/bin/ffmpeg.exe"),
        os.path.expandvars("%PROGRAMFILES(X86)%/ffmpeg/bin/ffmpeg.exe"),
        os.path.expandvars("%LOCALAPPDATA%/Programs/ffmpeg/bin/ffmpeg.exe"),
        "C:/ffmpeg/bin/ffmpeg.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def extract_text_from_epub(epub_path):
    """从EPUB文件中提取文本内容并保存为TXT文件"""
    print(f"\n📖 正在解析EPUB文件: {epub_path}")
    
    try:
        epub_path = Path(epub_path)
        if not epub_path.exists():
            raise FileNotFoundError(f"找不到EPUB文件: {epub_path}")
        
        # 设置输出TXT文件路径
        output_txt = epub_path.parent / f"{epub_path.stem}.txt"
        
        with zipfile.ZipFile(epub_path, 'r') as epub:
            # 列出EPUB文件中的所有文件
            file_list = epub.namelist()
            print(f"EPUB文件包含 {len(file_list)} 个文件")
            
            # 检查是否包含必要的文件
            if 'META-INF/container.xml' not in file_list:
                raise ValueError("EPUB文件格式错误: 缺少 META-INF/container.xml")
            
            # 查找OPF文件
            container = epub.read('META-INF/container.xml').decode('utf-8')
            opf_match = re.search(r'full-path="([^"]+)"', container)
            if not opf_match:
                raise ValueError("无法在container.xml中找到OPF文件路径")
                
            opf_path = opf_match.group(1)
            print(f"找到OPF文件: {opf_path}")
            
            if opf_path not in file_list:
                raise ValueError(f"OPF文件不存在: {opf_path}")
            
            # 读取OPF文件
            opf_content = epub.read(opf_path).decode('utf-8')
            opf_dir = os.path.dirname(opf_path)
            
            # 检测EPUB版本
            epub_version_match = re.search(r'version="([^"]+)"', opf_content)
            epub_version = epub_version_match.group(1) if epub_version_match else "2.0"
            print(f"EPUB版本: {epub_version}")
            
            # 提取元数据
            title_match = re.search(r'<dc:title[^>]*>([^<]+)</dc:title>', opf_content)
            title = title_match.group(1) if title_match else epub_path.stem
            
            creator_match = re.search(r'<dc:creator[^>]*>([^<]+)</dc:creator>', opf_content)
            creator = creator_match.group(1) if creator_match else "未知作者"
            
            print(f"书籍信息: {title} - {creator}")
            
            # 提取章节
            spine_items = re.findall(r'<itemref idref="([^"]+)"', opf_content)
            if not spine_items:
                raise ValueError("未找到spine中的itemrefs")
                
            print(f"找到 {len(spine_items)} 个spine项")
            
            # 查找manifest中的items
            manifest_items = {}
            
            # 支持EPUB 3.0格式
            for item in re.finditer(r'<item\s+[^>]*href="([^"]+)"[^>]*id="([^"]+)"[^>]*media-type="([^"]+)"[^>]*/?>', opf_content):
                href, item_id, media_type = item.groups()
                manifest_items[item_id] = {
                    'href': os.path.join(opf_dir, href),
                    'media_type': media_type
                }
            
            # 如果上面的正则表达式没有匹配到任何项，尝试另一种格式
            if not manifest_items:
                for item in re.finditer(r'<item\s+[^>]*id="([^"]+)"[^>]*href="([^"]+)"[^>]*media-type="([^"]+)"[^>]*/?>', opf_content):
                    item_id, href, media_type = item.groups()
                    manifest_items[item_id] = {
                        'href': os.path.join(opf_dir, href),
                        'media_type': media_type
                    }
            
            if not manifest_items:
                # 直接提取manifest部分
                manifest_match = re.search(r'<manifest>(.*?)</manifest>', opf_content, re.DOTALL)
                if manifest_match:
                    manifest_content = manifest_match.group(1)
                    # 逐行解析
                    for line in manifest_content.split('\n'):
                        item_match = re.search(r'<item\s+[^>]*id="([^"]+)"[^>]*href="([^"]+)"[^>]*media-type="([^"]+)"[^>]*/?>', line)
                        if item_match:
                            item_id, href, media_type = item_match.groups()
                            manifest_items[item_id] = {
                                'href': os.path.join(opf_dir, href),
                                'media_type': media_type
                            }
            
            if not manifest_items:
                raise ValueError("未找到manifest中的items")
                
            print(f"找到 {len(manifest_items)} 个manifest项")
            
            # 提取章节内容
            chapters = []
            chapter_index = 0
            
            for item_id in spine_items:
                if item_id in manifest_items and manifest_items[item_id]['media_type'] == 'application/xhtml+xml':
                    href = manifest_items[item_id]['href']
                    try:
                        # 检查文件是否存在，考虑到可能的路径格式差异
                        file_exists = False
                        possible_paths = [
                            href,  # 原始路径
                            href.replace('\\', '/'),  # 替换反斜杠为正斜杠
                            href.replace('/', '\\')   # 替换正斜杠为反斜杠
                        ]
                        
                        for path in possible_paths:
                            if path in file_list:
                                file_exists = True
                                href = path
                                break
                        
                        if not file_exists:
                            print(f"警告: 章节文件不存在: {href}")
                            continue
                            
                        content = epub.read(href).decode('utf-8')
                        
                        # 提取标题
                        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content)
                        if title_match:
                            title = title_match.group(1)
                        else:
                            # 尝试从h1或h2标签中提取标题
                            title_match = re.search(r'<h1[^>]*>([^<]+)</h1>|<h2[^>]*>([^<]+)</h2>', content)
                            if title_match:
                                title = title_match.group(1) or title_match.group(2)
                            else:
                                title = f"第{chapter_index+1}章"
                        
                        # 提取正文内容
                        # 移除HTML标签，保留文本
                        text = re.sub(r'<[^>]+>', ' ', content)
                        text = re.sub(r'\s+', ' ', text)
                        text = text.strip()
                        
                        # 如果文本太短，可能不是正文章节
                        if len(text) > 100:
                            chapters.append({
                                'index': chapter_index,
                                'title': title,
                                'text': text
                            })
                            chapter_index += 1
                        
                    except Exception as e:
                        print(f"警告: 提取章节 {href} 时出错: {e}")
            
            print(f"成功提取 {len(chapters)} 个章节")
            
            # 生成TXT文件
            with open(output_txt, 'w', encoding='utf-8') as f:
                for chapter in chapters:
                    f.write(f"\n\n{chapter['title']}\n\n")
                    f.write(chapter['text'])
                    f.write("\n\n" + "="*50 + "\n\n")
            
            print(f"已生成TXT文件: {output_txt}")
            return output_txt
            
    except Exception as e:
        print(f"✗ 解析EPUB文件失败: {e}")
        return None

class TextToAudiobookConverter:
    def __init__(self, txt_path, output_dir=None, language="zh-CN", 
                 voice_rate=150, voice_volume=1.0, max_workers=4):
        """初始化TXT到有声书转换器"""
        self.txt_path = Path(txt_path)
        if not self.txt_path.exists():
            raise FileNotFoundError(f"找不到TXT文件: {txt_path}")
        
        # 设置输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.txt_path.parent
        
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
        
        # 设置TTS参数
        self.language = language
        self.voice_rate = voice_rate
        self.voice_volume = voice_volume
        self.max_workers = max_workers
        
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # 设置输出文件名
        self.output_m4b = self.output_dir / f"{self.txt_path.stem}.m4b"
        
        # 查找ffmpeg
        self.ffmpeg_path = find_ffmpeg()
        if not self.ffmpeg_path:
            raise FileNotFoundError("找不到ffmpeg。请确保ffmpeg已安装并添加到系统PATH中。")
        
        # 存储章节信息
        self.chapters = []
        self.metadata = {
            "title": self.txt_path.stem,
            "artist": "TXT to Audiobook",
            "album": self.txt_path.stem,
            "date": time.strftime("%Y")
        }

    def extract_chapters(self):
        """从TXT文件中提取章节"""
        print(f"\n📖 正在解析TXT文件: {self.txt_path}")
        
        try:
            with open(self.txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用正则表达式分割章节
            # 匹配常见的章节标记，如"第X章"、"第X回"、"Chapter X"等
            chapter_pattern = r'(?:第[一二三四五六七八九十百千万\d]+[章节回]|Chapter\s*\d+|[第]?\d+[章节回])[^\n]*\n'
            chapters = re.split(chapter_pattern, content)
            chapter_titles = re.findall(chapter_pattern, content)
            
            # 如果没有找到章节标记，尝试按照分隔符分割
            if len(chapters) <= 1:
                chapters = content.split('\n\n=====\n\n')
                chapter_titles = [f"第{i+1}章" for i in range(len(chapters))]
            
            # 清理章节内容
            chapters = [chapter.strip() for chapter in chapters if chapter.strip()]
            chapter_titles = [title.strip() for title in chapter_titles]
            
            # 确保章节标题和内容数量匹配
            if len(chapters) > len(chapter_titles):
                chapter_titles.extend([f"第{i+1}章" for i in range(len(chapter_titles), len(chapters))])
            
            # 存储章节信息
            self.chapters = []
            for i, (title, content) in enumerate(zip(chapter_titles, chapters)):
                if len(content) > 10:  # 忽略过短的章节
                    self.chapters.append({
                        'index': i,
                        'title': title,
                        'text': content
                    })
            
            print(f"✓ 成功提取 {len(self.chapters)} 个章节")
            return True
            
        except Exception as e:
            print(f"✗ 解析TXT文件失败: {e}")
            return False

    async def text_to_speech(self, text, output_path):
        """将文本转换为语音"""
        try:
            import edge_tts
        except ImportError:
            print("正在安装edge-tts...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
            import edge_tts
        
        try:
            # 获取可用的语音列表
            voices = await edge_tts.list_voices()
            
            # 选择中文女声
            voice = None
            for v in voices:
                if v["Locale"] == self.language and "Female" in v["Gender"]:
                    voice = v
                    break
            
            # 如果没有找到指定语言的女声，尝试其他中文语音
            if not voice:
                for v in voices:
                    if v["Locale"].startswith("zh"):
                        voice = v
                        break
            
            # 如果仍然没有找到，使用第一个可用的语音
            if not voice and voices:
                voice = voices[0]
            
            if not voice:
                raise Exception("没有找到可用的语音")
            
            # 创建通信对象
            communicate = edge_tts.Communicate(
                text,
                voice["ShortName"],
                rate=f"+{self.voice_rate}%",
                volume=f"+{int(self.voice_volume * 100)}%"
            )
            
            # 转换文本为语音
            await communicate.save(str(output_path))
            return True
            
        except Exception as e:
            print(f"✗ 文本转语音失败: {e}")
            return False

    def process_chapter(self, chapter):
        """处理单个章节"""
        try:
            # 创建章节目录
            chapter_dir = self.temp_dir / "chapters"
            chapter_dir.mkdir(exist_ok=True)
            
            # 生成音频文件路径
            audio_path = chapter_dir / f"{chapter['index']:03d}_{chapter['title'][:50]}.mp3"
            
            # 转换文本为语音
            success = asyncio.run(self.text_to_speech(chapter['text'], audio_path))
            
            if success and audio_path.exists():
                print(f"✓ 章节 {chapter['title']} 处理完成")
                return {
                    'index': chapter['index'],
                    'title': chapter['title'],
                    'audio_path': audio_path,
                    'status': 'success'
                }
            else:
                print(f"✗ 章节 {chapter['title']} 处理失败")
                return {
                    'index': chapter['index'],
                    'title': chapter['title'],
                    'status': 'failed'
                }
        except Exception as e:
            print(f"✗ 章节 {chapter['title']} 处理失败: {e}")
            return {
                'index': chapter['index'],
                'title': chapter['title'],
                'status': 'failed'
            }

    def convert_chapters_to_audio(self):
        """将所有章节转换为音频文件"""
        print("\n🎵 开始将文本转换为语音...")
        
        with tqdm(total=len(self.chapters), desc="章节转换", unit="章节") as pbar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self.process_chapter, chapter) for chapter in self.chapters]
                
                processed_chapters = []
                for future in futures:
                    try:
                        result = future.result()
                        processed_chapters.append(result)
                        pbar.update(1)
                    except Exception as e:
                        print(f"章节处理失败: {e}")
                        pbar.update(1)
        
        success_count = sum(1 for chapter in processed_chapters if chapter['status'] == 'success')
        failed_count = sum(1 for chapter in processed_chapters if chapter['status'] == 'failed')
        
        print(f"\n✓ 成功转换 {success_count}/{len(self.chapters)} 个章节")
        if failed_count > 0:
            print(f"⚠ {failed_count} 个章节转换失败")
        
        return processed_chapters

    def merge_audio_files(self, processed_chapters):
        """合并所有章节的音频文件"""
        print("\n🎵 正在合并音频文件...")
        
        # 过滤出成功处理的章节
        successful_chapters = [chapter for chapter in processed_chapters if chapter['status'] == 'success']
        
        if not successful_chapters:
            raise ValueError("没有成功转换的章节，无法合并音频")
        
        # 创建进度条
        pbar = tqdm(total=len(successful_chapters), desc="音频合并", unit="章节")
        
        # 合并音频文件
        combined_mp3 = self.temp_dir / "combined.mp3"
        
        # 使用ffmpeg合并音频文件
        with open(self.temp_dir / "file_list.txt", "w", encoding="utf-8") as f:
            for chapter in successful_chapters:
                f.write(f"file '{chapter['audio_path'].resolve()}'\n")
        
        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", str(self.temp_dir / "file_list.txt"),
            "-c", "copy",
            str(combined_mp3)
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("💾 正在导出合并后的音频...")
            pbar.update(len(successful_chapters))
            pbar.close()
            print("✓ 音频合并完成")
            return combined_mp3
        except subprocess.CalledProcessError as e:
            pbar.close()
            print(f"✗ 音频合并失败: {e}")
            print(f"错误输出: {e.stderr.decode('utf-8', errors='ignore')}")
            raise RuntimeError(f"音频合并失败: {e}")

    def create_m4b(self, temp_mp3):
        """创建M4B文件"""
        print("\n📚 正在创建有声书文件...")
        
        # 构建ffmpeg命令
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(temp_mp3),
            "-c:a", "aac",
            "-b:a", "192k",
            "-metadata", f"title={self.metadata['title']}",
            "-metadata", f"artist={self.metadata['artist']}",
            "-metadata", f"album={self.metadata['album']}",
            "-metadata", f"date={self.metadata['date']}",
            str(self.output_m4b)
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"✓ 有声书创建完成: {self.output_m4b}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 有声书创建失败: {e}")
            return False

    def convert(self):
        """执行完整的转换流程"""
        try:
            # 提取章节
            if not self.extract_chapters():
                return False
            
            # 转换章节为音频
            processed_chapters = self.convert_chapters_to_audio()
            
            # 合并音频文件
            merged_file = self.merge_audio_files(processed_chapters)
            
            # 创建M4B文件
            if not self.create_m4b(merged_file):
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ 转换失败: {e}")
            return False
        finally:
            # 清理临时文件
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

def main():
    print("\n📚 EPUB/TXT转有声书转换器")
    print("=" * 50)
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print("\n💡 请将EPUB或TXT文件拖拽到此窗口，然后按回车键开始转换...")
        file_path = input().strip().strip('"')
    
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            sys.exit(1)
        
        # 根据文件类型选择转换流程
        if file_path.suffix.lower() == '.epub':
            print("\n📖 检测到EPUB文件，将先转换为TXT...")
            txt_path = extract_text_from_epub(file_path)
            if not txt_path:
                print("\n❌ EPUB转TXT失败！")
                sys.exit(1)
            print("\n✅ EPUB转TXT完成！")
            
            print("\n💫 是否要将TXT转换为有声书？(y/n)")
            if input().lower().strip() != 'y':
                sys.exit(0)
            
            file_path = txt_path
        
        if file_path.suffix.lower() != '.txt':
            print(f"❌ 不支持的文件类型: {file_path.suffix}")
            sys.exit(1)
        
        # 转换TXT为有声书
        print("\n🎵 开始转换TXT为有声书...")
        converter = TextToAudiobookConverter(
            file_path,
            language="zh-CN",
            voice_rate=150,
            voice_volume=1.0,
            max_workers=4
        )
        
        if converter.convert():
            print("\n✅ 转换完成！")
            print(f"输出文件：{converter.output_m4b}")
        else:
            print("\n❌ 转换失败！")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
