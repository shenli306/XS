# -*- coding: utf-8 -*-
import sys
import os
import time
import pytest
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
                             QTabWidget, QListWidget, QListWidgetItem, QMessageBox,
                             QFileDialog, QProgressBar, QGroupBox, QSplitter, QDialog, QRadioButton)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QLinearGradient, QBrush
import threading
import queue

# 导入项目中的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Public.Logs import 日志记录类

# 创建一个自定义的日志处理类，将日志输出到GUI界面
class GUILogger(日志记录类):
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        # 设置UI回调函数
        self.set_ui_callback(self.update_ui_log)
        
    def update_ui_log(self, msg, is_error):
        """更新UI日志显示"""
        try:
            if is_error:
                self.text_edit.append(f"<span style='color:red'>[错误] {msg}</span>")
            else:
                self.text_edit.append(f"[信息] {msg}")
            self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())
        except Exception:
            pass  # 忽略所有日志相关错误
        
    def info(self, msg, anti_recursion=False):
        try:
            if not anti_recursion:
                self.logger.info(msg)
        except Exception:
            pass  # 忽略所有日志相关错误
        
    def error(self, msg, anti_recursion=False):
        try:
            if not anti_recursion:
                self.logger.error(msg)
        except Exception:
            pass  # 忽略所有日志相关错误

# 创建一个工作线程类，用于在后台执行小说下载任务
class DownloadThread(QThread):
    # 定义信号
    log_signal = pyqtSignal(str, bool)  # 参数：消息内容，是否为错误
    progress_signal = pyqtSignal(int, int)   # 参数：当前进度，总进度
    complete_signal = pyqtSignal(str)        # 参数：完成消息
    search_result_signal = pyqtSignal(list)       # 参数：搜索结果列表
    
    # 类属性，用于存储下载器实例
    下载器 = None
    
    def __init__(self, 下载源, 搜索关键词, 小说链接=None, 下载格式="epub"):
        super().__init__()
        self.下载源 = 下载源
        self.搜索关键词 = 搜索关键词
        self.小说链接 = 小说链接
        self.下载格式 = 下载格式
        self.运行中 = True
        
        # 如果下载器实例不存在，创建一个新的
        if DownloadThread.下载器 is None:
            try:
                from TestCase.万书屋 import 万书屋下载器
                DownloadThread.下载器 = 万书屋下载器()
                # 设置进度回调
                DownloadThread.下载器.progress_callback = self.update_progress
                # 设置日志回调
                DownloadThread.下载器.log_callback = self.log_callback
            except Exception as e:
                self.log_signal.emit(f"创建下载器失败: {str(e)}", True)
        
    def run(self):
        try:
            # 根据选择的下载源执行相应的操作
            if self.下载源 == "万书屋":
                try:
                    if self.小说链接:
                        # 下载模式
                        self.log_signal.emit("开始下载小说...", False)
                        下载结果 = DownloadThread.下载器.下载小说(self.小说链接, self.下载格式)
                        if 下载结果:
                            self.complete_signal.emit("下载完成！")
                        else:
                            self.log_signal.emit("下载失败，请检查网络连接或重试", True)
                            self.complete_signal.emit("下载失败！")
                    else:
                        # 搜索模式
                        self.log_signal.emit("开始搜索小说...", False)
                        搜索结果 = DownloadThread.下载器.搜索小说(self.搜索关键词)
                        self.search_result_signal.emit(搜索结果)
                        self.complete_signal.emit("搜索完成！")
                        
                except Exception as e:
                    self.log_signal.emit(f"执行失败: {str(e)}", True)
                    self.complete_signal.emit("操作失败！")
            
        except Exception as e:
            import traceback
            error_msg = f"发生错误: {str(e)}\n{traceback.format_exc()}"
            self.log_signal.emit(error_msg, True)
            self.complete_signal.emit("操作失败！")
            
    def stop(self):
        self.运行中 = False
        self.terminate()
        
    @classmethod
    def 清理下载器(cls):
        if cls.下载器:
            cls.下载器 = None

    def update_progress(self, current, total):
        # 发送进度信号
        self.progress_signal.emit(current, total)

    def log_callback(self, message, is_error):
        # 发送日志信号
        self.log_signal.emit(message, is_error)

# 主窗口类
class NovelDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def closeEvent(self, event):
        # 清理下载器实例
        DownloadThread.清理下载器()
        event.accept()
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('小说下载器')
        self.resize(1000, 700)
        
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标题标签
        title_label = QLabel('小说下载器')
        title_font = QFont('微软雅黑', 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #333; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 创建选项卡部件
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 创建搜索选项卡
        self.search_tab = QWidget()
        self.tabs.addTab(self.search_tab, '搜索下载')
        
        # 创建下载管理选项卡
        self.download_tab = QWidget()
        self.tabs.addTab(self.download_tab, '下载管理')
        
        # 创建设置选项卡
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, '设置')
        
        # 创建日志选项卡
        self.log_tab = QWidget()
        self.tabs.addTab(self.log_tab, '日志')
        
        # 初始化日志选项卡（最先初始化，因为其他选项卡需要用到日志功能）
        self.init_log_tab()
        
        # 初始化其他选项卡
        self.init_search_tab()
        self.init_download_tab()
        self.init_settings_tab()
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #E6F3FF, stop:1 #87cefa);
            }
            QTabWidget::pane {
                border: 2px solid #87cefa;
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
            }
            QTabBar::tab {
                background-color: #E6F3FF;
                border: 2px solid #87cefa;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 16px;
                margin-right: 2px;
                color: #4682B4;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #87cefa;
                color: white;
                border-bottom: 1px solid white;
            }
            QPushButton {
                background-color: #87cefa;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4682B4;
            }
            QPushButton:pressed {
                background-color: #1E90FF;
            }
            QLineEdit, QComboBox, QTextEdit {
                border: 2px solid #87cefa;
                border-radius: 10px;
                padding: 6px;
                background-color: rgba(255, 255, 255, 0.9);
            }
            QProgressBar {
                border: 2px solid #87cefa;
                border-radius: 10px;
                text-align: center;
                background-color: rgba(255, 255, 255, 0.9);
            }
            QProgressBar::chunk {
                background-color: #4682B4;
                width: 10px;
                margin: 0.5px;
                border-radius: 5px;
            }
            QGroupBox {
                border: 2px solid #87cefa;
                border-radius: 10px;
                margin-top: 1em;
                padding-top: 10px;
                background-color: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #4682B4;
                font-weight: bold;
            }
            QLabel {
                color: #4682B4;
            }
            QListWidget {
                border: 2px solid #87cefa;
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.9);
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #E6F3FF;
            }
            QListWidget::item:selected {
                background-color: #87cefa;
                color: white;
            }
        """)
        
        # 显示窗口
        self.show()
    
    def init_search_tab(self):
        # 创建搜索选项卡的布局
        layout = QVBoxLayout(self.search_tab)
        
        # 创建搜索区域
        search_group = QGroupBox('搜索')
        search_layout = QHBoxLayout(search_group)
        
        # 创建搜索框和按钮
        search_label = QLabel('搜索关键词:')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('请输入小说名称或作者')
        
        # 添加书源选择
        source_label = QLabel('书源:')
        self.source_combo = QComboBox()
        self.source_combo.addItems(['万书屋', '辣文小说18+'])
        self.source_combo.setCurrentText('万书屋')  # 设置默认值
        
        self.search_button = QPushButton('搜索')
        self.search_button.clicked.connect(self.start_search)
        
        # 添加到搜索布局
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(source_label)
        search_layout.addWidget(self.source_combo)
        search_layout.addWidget(self.search_button)
        
        # 创建搜索结果区域
        results_group = QGroupBox('搜索结果')
        results_layout = QVBoxLayout(results_group)
        
        # 创建搜索结果列表
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.download_selected)
        results_layout.addWidget(self.results_list)
        
        # 创建下载按钮
        download_layout = QHBoxLayout()
        self.download_button = QPushButton('下载选中小说')
        self.download_button.clicked.connect(self.download_selected)
        download_layout.addStretch(1)
        download_layout.addWidget(self.download_button)
        results_layout.addLayout(download_layout)
        
        # 创建进度条
        progress_group = QGroupBox('下载进度')
        progress_layout = QVBoxLayout(progress_group)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # 添加所有组件到主布局
        layout.addWidget(search_group)
        layout.addWidget(results_group)
        layout.addWidget(progress_group)
        
        # 初始化日志处理器
        self.logger = GUILogger(self.full_log_display)
    
    def init_download_tab(self):
        # 创建下载管理选项卡的布局
        layout = QVBoxLayout(self.download_tab)
        
        # 创建下载列表
        downloads_group = QGroupBox('下载任务')
        downloads_layout = QVBoxLayout(downloads_group)
        
        self.downloads_list = QListWidget()
        downloads_layout.addWidget(self.downloads_list)
        
        # 创建下载操作按钮
        buttons_layout = QHBoxLayout()
        self.open_folder_button = QPushButton('打开下载文件夹')
        self.open_folder_button.clicked.connect(self.open_download_folder)
        self.clear_list_button = QPushButton('清空列表')
        self.clear_list_button.clicked.connect(self.clear_download_list)
        
        buttons_layout.addWidget(self.open_folder_button)
        buttons_layout.addWidget(self.clear_list_button)
        downloads_layout.addLayout(buttons_layout)
        
        # 添加到主布局
        layout.addWidget(downloads_group)
        layout.addStretch(1)
    
    def init_settings_tab(self):
        # 创建设置选项卡的布局
        layout = QVBoxLayout(self.settings_tab)
        
        # 创建基本设置组
        basic_group = QGroupBox('基本设置')
        basic_layout = QVBoxLayout(basic_group)
        
        # 下载路径设置
        path_layout = QHBoxLayout()
        path_label = QLabel('下载路径:')
        self.path_input = QLineEdit('downloads')
        self.path_input.setReadOnly(True)
        self.browse_button = QPushButton('浏览')
        self.browse_button.clicked.connect(self.browse_download_path)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        basic_layout.addLayout(path_layout)
        
        # 浏览器设置
        browser_layout = QHBoxLayout()
        browser_label = QLabel('浏览器:')
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(['Edge', 'Chrome', 'Firefox'])
        
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.browser_combo)
        browser_layout.addStretch(1)
        basic_layout.addLayout(browser_layout)
        
        # 无头模式设置
        headless_layout = QHBoxLayout()
        headless_label = QLabel('无头模式:')
        self.headless_combo = QComboBox()
        self.headless_combo.addItems(['是', '否'])
        
        headless_layout.addWidget(headless_label)
        headless_layout.addWidget(self.headless_combo)
        headless_layout.addStretch(1)
        basic_layout.addLayout(headless_layout)
        
        # 保存设置按钮
        save_layout = QHBoxLayout()
        self.save_settings_button = QPushButton('保存设置')
        save_layout.addStretch(1)
        save_layout.addWidget(self.save_settings_button)
        basic_layout.addLayout(save_layout)
        
        # 添加到主布局
        layout.addWidget(basic_group)
        
        # 创建作者说明组
        about_group = QGroupBox('关于')
        about_layout = QVBoxLayout(about_group)
        
        # 添加作者说明文本
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #4682B4;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        about_text.setText("""
        小说下载器 v1.0

        功能说明：
        1. 支持多个书源搜索和下载小说(书源为作者手搓，后面慢慢增加)
        2. 支持EPUB和TXT两种下载格式
        3. 实时显示下载进度
        4. 支持下载任务管理
        5. 详细的日志记录
        6. 可自定义下载路径
      

        使用说明：
        1. 在搜索框输入小说名称或作者
        2. 选择要使用的书源
        3. 点击搜索按钮
        4. 在搜索结果中选择要下载的小说
        5. 选择下载格式（EPUB或TXT）
        6. 等待下载完成

        注意事项：
        1. 下载的小说将保存在downloads文件夹中
        2. 建议使用EPUB格式，支持目录和排版
        3. 如遇到下载失败，请检查网络连接或尝试其他书源
        4. 部分书源可能需要使用代理才能访问（辣文小说18+需要魔法，万书屋只能使用国内IP）

        作者：shenli306
        
        """)
        about_layout.addWidget(about_text)
        
        # 添加到主布局
        layout.addWidget(about_group)
        layout.addStretch(1)
    
    def init_log_tab(self):
        # 创建日志选项卡的布局
        layout = QVBoxLayout(self.log_tab)
        
        # 创建日志显示区域
        self.full_log_display = QTextEdit()
        self.full_log_display.setReadOnly(True)
        layout.addWidget(self.full_log_display)
        
        # 创建日志操作按钮
        buttons_layout = QHBoxLayout()
        self.clear_log_button = QPushButton('清空日志')
        self.clear_log_button.clicked.connect(self.clear_log)
        self.export_log_button = QPushButton('导出日志')
        self.export_log_button.clicked.connect(self.export_log)
        
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.clear_log_button)
        buttons_layout.addWidget(self.export_log_button)
        layout.addLayout(buttons_layout)
    
    def start_search(self):
        # 获取搜索关键词和书源
        搜索关键词 = self.search_input.text().strip()
        下载源 = self.source_combo.currentText()
        
        if not 搜索关键词:
            QMessageBox.warning(self, '警告', '请输入搜索关键词')
            return
        
        # 清空搜索结果列表
        self.results_list.clear()
        
        # 更新日志
        self.logger.info(f"开始搜索: {搜索关键词} (书源: {下载源})")
        
        # 创建并启动下载线程
        self.download_thread = DownloadThread(下载源, 搜索关键词)
        self.download_thread.log_signal.connect(self.update_log)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.complete_signal.connect(self.download_finished)
        self.download_thread.search_result_signal.connect(self.update_search_results)
        self.download_thread.start()
        
        # 禁用搜索按钮
        self.search_button.setEnabled(False)
    
    def update_log(self, message, is_error):
        if is_error:
            self.logger.error(message, anti_recursion=True)
        else:
            self.logger.info(message, anti_recursion=True)
        
        # 更新完整日志选项卡
        if is_error:
            self.full_log_display.append(f"<span style='color:red'>[错误] {message}</span>")
        else:
            self.full_log_display.append(f"[信息] {message}")
        self.full_log_display.verticalScrollBar().setValue(self.full_log_display.verticalScrollBar().maximum())
    
    def update_progress(self, current, total):
        percentage = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        # 更新进度条文本
        self.progress_bar.setFormat(f"下载进度: {percentage}%")
    
    def update_search_results(self, results):
        # 清空结果列表
        self.results_list.clear()
        
        # 添加搜索结果到列表
        for result in results:
            小说名, 小说链接, 作者, 最新章节, 简介 = result
            item_text = f"{小说名} - {作者}\n最新章节: {最新章节}\n{简介}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, 小说链接)  # 存储小说链接
            self.results_list.addItem(item)
    
    def download_selected(self):
        # 获取选中的小说
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', '请选择要下载的小说')
            return
        
        # 获取选中小说的信息和当前选择的书源
        selected_item = selected_items[0]
        小说名 = selected_item.text().split(' - ')[0]
        小说链接 = selected_item.data(Qt.UserRole)
        下载源 = self.source_combo.currentText()
        
        # 弹出格式选择对话框
        format_dialog = QDialog(self)
        format_dialog.setWindowTitle('选择下载格式')
        format_dialog.setFixedWidth(300)
        
        layout = QVBoxLayout(format_dialog)
        
        # 添加说明标签
        label = QLabel('请选择要下载的文件格式：')
        layout.addWidget(label)
        
        # 创建单选按钮
        epub_radio = QRadioButton('EPUB格式（推荐）')
        txt_radio = QRadioButton('TXT格式')
        epub_radio.setChecked(True)  # 默认选择EPUB
        
        layout.addWidget(epub_radio)
        layout.addWidget(txt_radio)
        
        # 添加按钮
        button_box = QHBoxLayout()
        ok_button = QPushButton('确定')
        cancel_button = QPushButton('取消')
        
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)
        
        # 连接按钮信号
        ok_button.clicked.connect(format_dialog.accept)
        cancel_button.clicked.connect(format_dialog.reject)
        
        # 显示对话框
        if format_dialog.exec_() == QDialog.Accepted:
            # 获取用户选择的格式
            下载格式 = "epub" if epub_radio.isChecked() else "txt"
            
            # 更新日志
            self.logger.info(f"开始下载小说: {小说名} (格式: {下载格式.upper()})")
            
            # 创建并启动下载线程
            self.download_thread = DownloadThread(下载源, None, 小说链接, 下载格式)
            self.download_thread.log_signal.connect(self.update_log)
            self.download_thread.progress_signal.connect(self.update_progress)
            self.download_thread.complete_signal.connect(self.download_finished)
            self.download_thread.start()
            
            # 添加到下载列表
            download_item = QListWidgetItem(f"{小说名} - 下载中...")
            self.downloads_list.addItem(download_item)
        else:
            self.logger.info("已取消下载")
    
    def download_finished(self, message):
        # 更新日志
        self.logger.info(message)
        
        # 启用搜索按钮
        self.search_button.setEnabled(True)
        
        # 重置进度条
        self.progress_bar.setValue(0)
        
        # 显示完成消息
        QMessageBox.information(self, '完成', message)
        
        # 更新下载列表中的状态
        for i in range(self.downloads_list.count()):
            item = self.downloads_list.item(i)
            if "下载中" in item.text():
                item.setText(item.text().replace("下载中", "已完成"))
    
    def open_download_folder(self):
        # 打开下载文件夹
        download_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        
        # 使用系统默认的文件浏览器打开文件夹
        os.startfile(download_path)
    
    def browse_download_path(self):
        # 打开文件夹选择对话框
        folder = QFileDialog.getExistingDirectory(self, '选择下载文件夹', 'downloads')
        if folder:
            self.path_input.setText(folder)
    
    def clear_log(self):
        # 清空日志显示
        self.full_log_display.clear()
    
    def export_log(self):
        # 导出日志到文件
        file_name, _ = QFileDialog.getSaveFileName(self, '导出日志', '', 'Text Files (*.txt);;All Files (*)')
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(self.full_log_display.toPlainText())
            QMessageBox.information(self, '成功', f'日志已导出到 {file_name}')

    def clear_download_list(self):
        # 弹出确认对话框
        reply = QMessageBox.question(self, '确认清空', 
                                   '确定要清空下载列表吗？\n此操作不可恢复。',
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 清空下载列表
            self.downloads_list.clear()
            # 更新日志
            self.logger.info("已清空下载列表")

# 主函数
def main():
    app = QApplication(sys.argv)
    window = NovelDownloader()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()