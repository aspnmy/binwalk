#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
binwalk GUI - Windows中文环境下的binwalk图形界面工具

此脚本提供了一个图形界面，用于简化binwalk命令行工具在Windows中文环境下的使用。
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext
import threading


class BinwalkGUI:
    """
binwalk图形界面主类
    """
    
    def __init__(self, root):
        """
初始化GUI界面

参数:
    root: tkinter的根窗口对象
        """
        self.root = root
        self.root.title("Binwalk GUI - 公版固件BIn分析工具 v3.1.0 for devWin By support@e2bank.cn")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 确保中文显示正常
        self.setup_chinese_fonts()
        
        # 配置binwalk路径 - 支持独立运行模式
        self.binwalk_path = self.get_binwalk_path()
        print(f"[+] 使用的binwalk路径: {self.binwalk_path}")
    
    def get_binwalk_path(self):
        """
获取binwalk可执行文件的路径

返回值:
    str: binwalk可执行文件的完整路径
        """
        # 获取当前可执行文件的目录（无论是Python脚本还是编译后的exe）
        if getattr(sys, 'frozen', False):
            # 当程序被PyInstaller打包后
            base_dir = os.path.dirname(sys.executable)
        else:
            # 当程序作为Python脚本运行时
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 使用可执行文件所在目录的相对路径查找binwalk.exe
        self.binwalk_path = os.path.join(base_dir, "binwalk.exe")
        
        # 创建界面组件
        self.create_widgets()
        
        # 检查binwalk是否存在
        self.check_binwalk_exists()
        
        return self.binwalk_path
    
    def setup_chinese_fonts(self):
        """
设置中文字体支持
        """
        # 在Windows系统上，tkinter默认支持中文，不需要特别设置
        # 此处仅作为兼容性处理
        pass
    
    def check_binwalk_exists(self):
        """
检查binwalk可执行文件是否存在
        """
        if not os.path.exists(self.binwalk_path):
            messagebox.showerror("错误", f"未找到binwalk可执行文件！\n路径: {self.binwalk_path}\n\n请确保已编译binwalk。")
    
    def create_widgets(self):
        """
创建GUI界面组件
        """
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=70)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_button = ttk.Button(file_frame, text="浏览...", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # 参数设置区域
        params_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="10")
        params_frame.pack(fill=tk.X, pady=5)
        
        # 创建参数选项
        self.create_param_options(params_frame)
        
        # 提取目录设置
        extract_frame = ttk.Frame(params_frame)
        extract_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(extract_frame, text="提取目录: ").pack(side=tk.LEFT, padx=5)
        self.extract_dir_var = tk.StringVar(value="extractions")
        self.extract_dir_entry = ttk.Entry(extract_frame, textvariable=self.extract_dir_var, width=40)
        self.extract_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 运行按钮区域
        run_frame = ttk.Frame(main_frame)
        run_frame.pack(fill=tk.X, pady=5)
        
        self.run_button = ttk.Button(run_frame, text="运行分析", command=self.run_binwalk)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(run_frame, text="停止", command=self.stop_binwalk, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(run_frame, text="清空输出", command=self.clear_output)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # 结果显示区域
        output_frame = ttk.LabelFrame(main_frame, text="分析结果", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=90, height=20)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始化进程变量
        self.process = None
    
    def create_param_options(self, parent_frame):
        """
创建参数选项控件

参数:
    parent_frame: 父框架对象
        """
        # 基本选项
        basic_frame = ttk.LabelFrame(parent_frame, text="基本选项")
        basic_frame.pack(fill=tk.X, pady=5)
        
        # 提取文件选项
        self.extract_var = tk.BooleanVar()
        extract_check = ttk.Checkbutton(basic_frame, text="自动提取已知文件类型 (-e)", variable=self.extract_var)
        extract_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 雕刻文件选项
        self.carve_var = tk.BooleanVar()
        carve_check = ttk.Checkbutton(basic_frame, text="雕刻已知和未知文件内容 (-c)", variable=self.carve_var)
        carve_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 递归分析选项
        self.matryoshka_var = tk.BooleanVar()
        matryoshka_check = ttk.Checkbutton(basic_frame, text="递归分析提取的文件 (-M)", variable=self.matryoshka_var)
        matryoshka_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 熵分析选项
        self.entropy_var = tk.BooleanVar()
        entropy_check = ttk.Checkbutton(basic_frame, text="生成熵图 (-E)", variable=self.entropy_var)
        entropy_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 高级选项
        advanced_frame = ttk.LabelFrame(parent_frame, text="高级选项")
        advanced_frame.pack(fill=tk.X, pady=5)
        
        # 搜索全部选项
        self.search_all_var = tk.BooleanVar()
        search_all_check = ttk.Checkbutton(advanced_frame, text="在所有偏移位置搜索所有签名 (-a)", variable=self.search_all_var)
        search_all_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 静默模式
        self.quiet_var = tk.BooleanVar()
        quiet_check = ttk.Checkbutton(advanced_frame, text="静默模式，抑制标准输出 (-q)", variable=self.quiet_var)
        quiet_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 详细模式
        self.verbose_var = tk.BooleanVar()
        verbose_check = ttk.Checkbutton(advanced_frame, text="详细模式，显示所有结果 (-v)", variable=self.verbose_var)
        verbose_check.pack(anchor=tk.W, padx=5, pady=2)
        
        # 线程数设置
        threads_frame = ttk.Frame(advanced_frame)
        threads_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(threads_frame, text="线程数: ").pack(side=tk.LEFT, padx=5)
        self.threads_var = tk.StringVar()
        threads_combo = ttk.Combobox(threads_frame, textvariable=self.threads_var, values=["", "1", "2", "4", "8", "16"], width=5)
        threads_combo.pack(side=tk.LEFT, padx=5)
        threads_combo.current(0)  # 默认不设置
    
    def browse_file(self):
        """
打开文件选择对话框
        """
        file_path = filedialog.askopenfilename(
            title="选择要分析的文件",
            filetypes=[("所有文件", "*.*"), ("二进制文件", "*.bin;*.img;*.rom")]
        )
        if file_path:
            self.file_path_var.set(file_path)
    
    def run_binwalk(self):
        """
运行binwalk命令
        """
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("错误", "请选择要分析的文件！")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return
        
        # 构建命令参数
        cmd = [self.binwalk_path]
        
        # 添加基本选项
        if self.extract_var.get():
            cmd.append("-e")
        if self.carve_var.get():
            cmd.append("-c")
        if self.matryoshka_var.get():
            cmd.append("-M")
        if self.entropy_var.get():
            cmd.append("-E")
        
        # 添加高级选项
        if self.search_all_var.get():
            cmd.append("-a")
        if self.quiet_var.get():
            cmd.append("-q")
        if self.verbose_var.get():
            cmd.append("-v")
        
        # 添加线程数
        threads = self.threads_var.get()
        if threads:
            cmd.extend(["-t", threads])
        
        # 添加提取目录
        extract_dir = self.extract_dir_var.get()
        if extract_dir:
            cmd.extend(["-d", extract_dir])
        
        # 添加文件路径
        cmd.append(file_path)
        
        # 更新UI状态
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("分析中...")
        
        # 清空输出
        self.clear_output()
        
        # 在新线程中运行命令
        self.process = None
        thread = threading.Thread(target=self.execute_command, args=(cmd,))
        thread.daemon = True
        thread.start()
    
    def execute_command(self, cmd):
        """
执行命令并显示输出

参数:
    cmd: 要执行的命令列表
        """
        try:
            # 执行命令
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=False
            )
            
            # 读取输出
            for line in iter(self.process.stdout.readline, ''):
                self.append_output(line)
            
            # 等待进程结束
            self.process.wait()
            
            if self.process.returncode == 0:
                self.append_output("\n分析完成！")
                self.status_var.set("分析完成")
            else:
                self.append_output(f"\n分析失败，返回码: {self.process.returncode}")
                self.status_var.set("分析失败")
                
        except Exception as e:
            self.append_output(f"\n执行出错: {str(e)}")
            self.status_var.set("执行出错")
        finally:
            # 恢复UI状态
            self.root.after(0, lambda: self.run_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.process = None
    
    def append_output(self, text):
        """
向输出文本框添加内容

参数:
    text: 要添加的文本
        """
        self.root.after(0, lambda: self._append_output_safe(text))
    
    def _append_output_safe(self, text):
        """
安全地向输出文本框添加内容（在主线程中执行）

参数:
    text: 要添加的文本
        """
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def stop_binwalk(self):
        """
停止正在运行的binwalk进程
        """
        if self.process:
            try:
                self.process.terminate()
                self.append_output("\n分析已停止！")
                self.status_var.set("已停止")
            except Exception as e:
                self.append_output(f"\n停止出错: {str(e)}")
    
    def clear_output(self):
        """
清空输出文本框
        """
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)


def main():
    """
主函数，启动GUI应用

返回值:
    None
        """
    # 确保中文显示正常
    root = tk.Tk()
    
    # 创建并运行GUI
    app = BinwalkGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()