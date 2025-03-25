# 自动化小说下载器

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![更新时间](https://img.shields.io/badge/更新-2024年6月-orange.svg)

## 项目介绍

这是一个用Python编写的高效小说下载工具，专门针对"万书屋"网站进行优化，能够自动搜索、获取和下载小说内容，并生成标准TXT和精美EPUB电子书。本项目采用Selenium进行网页自动化操作，BeautifulSoup进行HTML解析，支持章节智能排序和广告内容过滤。

## 主要功能

- 📚 支持小说搜索和智能匹配下载
- 📖 支持生成TXT和EPUB双格式电子书
- 🖼️ 自动获取小说封面和完整元数据
- 🧹 自动清理广告和不必要内容
- 📊 智能排序章节，确保阅读顺序正确
- 🎨 美化的命令行界面和实时进度展示

## 近期更新

- ⚡ 重写章节获取逻辑，解决无限循环问题
- 🔄 优化章节去重算法，避免重复内容
- 🛠️ 完善错误处理机制，提高爬取稳定性
- 📏 减少最大页数限制，加快获取速度
- 🔎 改进页面导航逻辑，适应不同页面结构

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 克隆仓库到本地：

```bash
git clone https://github.com/yourusername/小说下载器.git
cd 小说下载器
```

2. 安装所需依赖：

```bash
pip install -r requirements.txt
```

3. 运行程序：

```bash
python Run.py
```

4. 根据提示输入要搜索的小说名称，系统会自动搜索、匹配并下载

## 项目结构

```
小说下载器/
├── Run.py                # 主程序入口
├── Public/               # 公共函数模块
│   └── Base.py           # 浏览器操作的二次封装
├── TestCase/             # 测试用例目录
│   └── 万书屋.py          # 万书屋网站爬虫主要逻辑
└── downloads/            # 下载的小说存放目录
```

## 功能特点

- **无头模式**：支持在后台运行，不显示浏览器界面
- **智能分析**：自动识别章节结构和内容
- **内容清洗**：自动过滤广告和无关内容
- **自动排序**：确保章节按正确顺序排列
- **多格式支持**：单次下载可生成多种电子书格式
- **美化输出**：使用彩色命令行界面，提供友好的用户体验

## 依赖库

- pytest - 自动化测试框架
- selenium - 浏览器自动化
- beautifulsoup4 - HTML解析
- requests - 网络请求
- ebooklib - EPUB电子书生成
- colorama - 命令行彩色输出
- tqdm - 进度条展示

## 注意事项

1. 本工具仅用于个人学习研究，请勿用于任何商业用途
2. 请尊重版权，不要过度爬取或分享受版权保护的内容
3. 使用过程中请遵守相关网站的robots协议
4. 建议使用无头模式运行，减少资源占用

## 贡献指南

欢迎提交问题和功能请求。如果您想贡献代码，请先fork本仓库并提交拉取请求。

## 许可证

本项目采用MIT许可证 - 详情请参阅 [LICENSE](LICENSE) 文件 