#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WSL Docker binwalk 图形化管理工具

本工具提供图形界面来管理WSL环境中的binwalk-docker容器，
支持文件上传下载、命令执行和容器管理等功能。

参数：
    无

返回值：
    无
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import shutil
import time
import re

def run_command(command, shell=True, capture_output=True):
    """
    运行命令并返回结果
    
    参数:
        command: str, 要执行的命令
        shell: bool, 是否在shell中执行
        capture_output: bool, 是否捕获输出
    
    返回:
        tuple: (返回码, 标准输出, 标准错误)
    """
    try:
        if capture_output:
            process = subprocess.Popen(
                command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        else:
            process = subprocess.Popen(command, shell=shell)
            process.wait()
            return process.returncode, "", ""
    except Exception as e:
        return 1, "", str(e)

def run_wsl_command(command):
    """
    在WSL中运行命令
    
    参数:
        command: str, 要在WSL中执行的命令
    
    返回:
        tuple: (返回码, 标准输出, 标准错误)
    """
    full_command = f'wsl -d kali-linux -e bash -c "{command}"'
    return run_command(full_command)

def is_wsl_running():
    """
    检查WSL是否正在运行
    
    返回:
        bool: True表示正在运行，False表示未运行
    """
    code, output, _ = run_command("wsl -l -v")
    return code == 0 and "running" in output.lower()

def is_docker_running():
    """
    检查Docker是否正在运行
    
    返回:
        bool: True表示正在运行，False表示未运行
    """
    code, output, _ = run_wsl_command("docker info")
    return code == 0

def start_docker():
    """
    启动Docker服务
    
    返回:
        bool: True表示启动成功，False表示失败
    """
    code, output, error = run_wsl_command("sudo service docker start")
    if code != 0:
        print(f"启动Docker失败: {error}")
        return False
    return True

def ensure_docker_volume():
    """
    确保binwalk Docker卷存在
    
    返回:
        bool: True表示卷存在，False表示创建失败
    """
    code, output, _ = run_wsl_command("docker volume ls")
    if "binwalkv3" in output:
        return True
    
    # 创建卷
    code, output, error = run_wsl_command("docker volume create binwalkv3")
    if code != 0:
        print(f"创建Docker卷失败: {error}")
        return False
    return True

def get_volume_mount_point():
    """
    获取Docker卷的挂载点
    
    返回:
        str: 卷的挂载点路径，失败返回空字符串
    """
    code, output, error = run_wsl_command(
        "docker volume inspect -f '{{.Mountpoint}}' binwalkv3"
    )
    if code != 0:
        print(f"获取卷挂载点失败: {error}")
        return ""
    return output.strip()

class BinwalkGUI:
    """
    Binwalk WSL Docker 图形化管理类
    """
    
    def __init__(self, root):
        """
        初始化GUI界面
        
        参数:
            root: tk.Tk, 主窗口对象
        """
        self.root = root
        self.root.title("Binwalk WSL Docker 管理工具")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 设置中文字体
        self.setup_fonts()
        
        # 状态变量
        self.docker_volume_path = ""
        self.current_container_id = ""
        
        # 创建主界面
        self.create_main_frame()
        
        # 初始化检查
        self.initialize_check()
    
    def setup_fonts(self):
        """
        设置中文字体配置
        """
        # 尝试设置不同的中文字体以确保兼容性
        self.font_families = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC", "Arial"]
    
    def create_main_frame(self):
        """
        创建主界面框架
        """
        # 创建选项卡控件
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(expand=1, fill="both")
        
        # 创建各个选项卡
        self.tab_status = ttk.Frame(self.tab_control)
        self.tab_file_manage = ttk.Frame(self.tab_control)
        self.tab_command = ttk.Frame(self.tab_control)
        self.tab_container = ttk.Frame(self.tab_control)
        self.tab_help = ttk.Frame(self.tab_control)
        
        # 添加选项卡到控件
        self.tab_control.add(self.tab_status, text="状态监控")
        self.tab_control.add(self.tab_file_manage, text="文件管理")
        self.tab_control.add(self.tab_command, text="命令执行")
        self.tab_control.add(self.tab_container, text="容器管理")
        self.tab_control.add(self.tab_help, text="帮助信息")
        
        # 创建各个选项卡的内容
        self.create_status_tab()
        self.create_file_manage_tab()
        self.create_command_tab()
        self.create_container_tab()
        self.create_help_tab()
    
    def create_status_tab(self):
        """
        创建状态监控选项卡
        """
        # 创建框架
        frame_wsl = ttk.LabelFrame(self.tab_status, text="WSL状态")
        frame_wsl.pack(fill="x", padx=10, pady=5)
        
        frame_docker = ttk.LabelFrame(self.tab_status, text="Docker状态")
        frame_docker.pack(fill="x", padx=10, pady=5)
        
        frame_volume = ttk.LabelFrame(self.tab_status, text="Docker卷状态")
        frame_volume.pack(fill="x", padx=10, pady=5)
        
        frame_container = ttk.LabelFrame(self.tab_status, text="容器状态")
        frame_container.pack(fill="x", padx=10, pady=5)
        
        # WSL状态
        self.label_wsl_status = ttk.Label(frame_wsl, text="未检查")
        self.label_wsl_status.pack(side="left", padx=10, pady=5)
        
        self.btn_refresh_wsl = ttk.Button(frame_wsl, text="刷新", command=self.refresh_wsl_status)
        self.btn_refresh_wsl.pack(side="right", padx=10, pady=5)
        
        # Docker状态
        self.label_docker_status = ttk.Label(frame_docker, text="未检查")
        self.label_docker_status.pack(side="left", padx=10, pady=5)
        
        self.btn_start_docker = ttk.Button(frame_docker, text="启动Docker", command=self.start_docker_service)
        self.btn_start_docker.pack(side="right", padx=10, pady=5)
        
        # Docker卷状态
        self.label_volume_status = ttk.Label(frame_volume, text="未检查")
        self.label_volume_status.pack(side="left", padx=10, pady=5)
        
        self.btn_create_volume = ttk.Button(frame_volume, text="创建卷", command=self.create_docker_volume)
        self.btn_create_volume.pack(side="right", padx=10, pady=5)
        
        # 容器状态
        self.label_container_status = ttk.Label(frame_container, text="未检查")
        self.label_container_status.pack(side="left", padx=10, pady=5)
        
        self.btn_refresh_container = ttk.Button(frame_container, text="刷新", command=self.refresh_container_status)
        self.btn_refresh_container.pack(side="right", padx=10, pady=5)
        
        # 状态栏按钮
        self.btn_full_refresh = ttk.Button(self.tab_status, text="全部刷新", command=self.refresh_all_status)
        self.btn_full_refresh.pack(pady=10)
    
    def create_file_manage_tab(self):
        """
        创建文件管理选项卡
        """
        # 创建主框架
        main_frame = ttk.Frame(self.tab_file_manage)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建左右分栏
        left_frame = ttk.LabelFrame(main_frame, text="本地文件")
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        right_frame = ttk.LabelFrame(main_frame, text="Docker卷文件")
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # 左侧本地文件列表
        self.local_files_tree = ttk.Treeview(left_frame)
        self.local_files_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.local_files_tree["columns"] = ("name", "size", "date")
        self.local_files_tree.column("#0", width=20)
        self.local_files_tree.column("name", width=150, anchor="w")
        self.local_files_tree.column("size", width=80, anchor="e")
        self.local_files_tree.column("date", width=150, anchor="w")
        
        self.local_files_tree.heading("#0", text="")
        self.local_files_tree.heading("name", text="文件名")
        self.local_files_tree.heading("size", text="大小")
        self.local_files_tree.heading("date", text="修改日期")
        
        # 右侧Docker卷文件列表
        self.docker_files_tree = ttk.Treeview(right_frame)
        self.docker_files_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.docker_files_tree["columns"] = ("name", "size", "date")
        self.docker_files_tree.column("#0", width=20)
        self.docker_files_tree.column("name", width=150, anchor="w")
        self.docker_files_tree.column("size", width=80, anchor="e")
        self.docker_files_tree.column("date", width=150, anchor="w")
        
        self.docker_files_tree.heading("#0", text="")
        self.docker_files_tree.heading("name", text="文件名")
        self.docker_files_tree.heading("size", text="大小")
        self.docker_files_tree.heading("date", text="修改日期")
        
        # 操作按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=5)
        
        # 文件操作按钮
        self.btn_upload = ttk.Button(button_frame, text="上传到Docker卷 ->", command=self.upload_files)
        self.btn_upload.pack(side="left", padx=5)
        
        self.btn_download = ttk.Button(button_frame, text="<- 从Docker卷下载", command=self.download_files)
        self.btn_download.pack(side="left", padx=5)
        
        self.btn_refresh_local = ttk.Button(button_frame, text="刷新本地", command=self.refresh_local_files)
        self.btn_refresh_local.pack(side="left", padx=5)
        
        self.btn_refresh_docker = ttk.Button(button_frame, text="刷新Docker", command=self.refresh_docker_files)
        self.btn_refresh_docker.pack(side="left", padx=5)
        
        self.btn_select_folder = ttk.Button(button_frame, text="选择本地文件夹", command=self.select_local_folder)
        self.btn_select_folder.pack(side="right", padx=5)
        
        # 当前路径显示
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill="x", pady=5)
        
        self.label_local_path = ttk.Label(path_frame, text="本地路径:")
        self.label_local_path.pack(side="left", padx=5)
        
        self.entry_local_path = ttk.Entry(path_frame)
        self.entry_local_path.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_local_path.insert(0, os.getcwd())
        
        self.label_docker_path = ttk.Label(path_frame, text="Docker卷路径:")
        self.label_docker_path.pack(side="left", padx=5)
        
        self.entry_docker_path = ttk.Entry(path_frame)
        self.entry_docker_path.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_docker_path.insert(0, "/analysis")
    
    def create_command_tab(self):
        """
        创建命令执行选项卡
        """
        # 命令输入框
        input_frame = ttk.Frame(self.tab_command)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.label_command = ttk.Label(input_frame, text="Binwalk命令:")
        self.label_command.pack(side="left", padx=5)
        
        self.entry_command = ttk.Entry(input_frame)
        self.entry_command.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_command.insert(0, "binwalk ")
        
        self.btn_run_command = ttk.Button(input_frame, text="执行", command=self.run_binwalk_command)
        self.btn_run_command.pack(side="right", padx=5)
        
        # 常用命令按钮
        common_commands_frame = ttk.LabelFrame(self.tab_command, text="常用命令")
        common_commands_frame.pack(fill="x", padx=10, pady=5)
        
        commands = [
            ("基本扫描", "binwalk -B "),
            ("详细扫描", "binwalk -e "),
            ("深度扫描", "binwalk -Me "),
            ("熵分析", "binwalk -E "),
            ("提取固件", "binwalk -eM ")
        ]
        
        for text, cmd in commands:
            btn = ttk.Button(common_commands_frame, text=text, 
                            command=lambda c=cmd: self.entry_command.insert(tk.END, c))
            btn.pack(side="left", padx=5, pady=5)
        
        # 输出显示区域
        output_frame = ttk.LabelFrame(self.tab_command, text="命令输出")
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.text_output = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD)
        self.text_output.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_output.config(state=tk.DISABLED)
    
    def create_container_tab(self):
        """
        创建容器管理选项卡
        """
        # 容器操作按钮
        buttons_frame = ttk.Frame(self.tab_container)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_start_container = ttk.Button(buttons_frame, text="启动容器", command=self.start_container)
        self.btn_start_container.pack(side="left", padx=5)
        
        self.btn_stop_container = ttk.Button(buttons_frame, text="停止容器", command=self.stop_container)
        self.btn_stop_container.pack(side="left", padx=5)
        
        self.btn_restart_container = ttk.Button(buttons_frame, text="重启容器", command=self.restart_container)
        self.btn_restart_container.pack(side="left", padx=5)
        
        self.btn_remove_container = ttk.Button(buttons_frame, text="移除容器", command=self.remove_container)
        self.btn_remove_container.pack(side="left", padx=5)
        
        # 容器信息
        info_frame = ttk.LabelFrame(self.tab_container, text="容器信息")
        info_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.text_container_info = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD)
        self.text_container_info.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_container_info.config(state=tk.DISABLED)
        
        # 容器列表
        list_frame = ttk.LabelFrame(self.tab_container, text="容器列表")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.containers_tree = ttk.Treeview(list_frame)
        self.containers_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.containers_tree["columns"] = ("id", "image", "status", "ports", "names")
        self.containers_tree.column("#0", width=20)
        self.containers_tree.column("id", width=100, anchor="w")
        self.containers_tree.column("image", width=150, anchor="w")
        self.containers_tree.column("status", width=100, anchor="w")
        self.containers_tree.column("ports", width=100, anchor="w")
        self.containers_tree.column("names", width=100, anchor="w")
        
        self.containers_tree.heading("#0", text="")
        self.containers_tree.heading("id", text="ID")
        self.containers_tree.heading("image", text="镜像")
        self.containers_tree.heading("status", text="状态")
        self.containers_tree.heading("ports", text="端口")
        self.containers_tree.heading("names", text="名称")
        
        self.btn_refresh_containers = ttk.Button(list_frame, text="刷新容器列表", command=self.refresh_containers_list)
        self.btn_refresh_containers.pack(pady=5)
    
    def create_help_tab(self):
        """
        创建帮助信息选项卡
        """
        # 创建帮助文本
        help_text = """
        Binwalk WSL Docker 管理工具使用指南
        
        1. 状态监控
           - 显示WSL、Docker、Docker卷和容器的状态
           - 可以启动Docker服务和创建Docker卷
        
        2. 文件管理
           - 左侧显示本地文件，右侧显示Docker卷中的文件
           - 可以上传文件到Docker卷或从Docker卷下载文件
           - 可以选择本地文件夹和刷新文件列表
        
        3. 命令执行
           - 可以在Docker容器中执行Binwalk命令
           - 提供常用命令快捷按钮
           - 显示命令执行输出结果
        
        4. 容器管理
           - 可以启动、停止、重启和移除容器
           - 显示容器信息和容器列表
        
        注意事项：
        - 使用前请确保WSL和Docker已正确安装
        - 文件上传下载操作需要容器正在运行
        - 执行命令时请确保指定正确的文件路径
        """
        
        # 创建文本区域显示帮助信息
        self.text_help = scrolledtext.ScrolledText(self.tab_help, wrap=tk.WORD)
        self.text_help.pack(fill="both", expand=True, padx=10, pady=10)
        self.text_help.insert(tk.END, help_text)
        self.text_help.config(state=tk.DISABLED)
    
    def initialize_check(self):
        """
        初始化检查
        """
        # 在单独的线程中执行初始化检查，避免界面卡顿
        thread = threading.Thread(target=self._initialize_check_thread)
        thread.daemon = True
        thread.start()
    
    def _initialize_check_thread(self):
        """
        初始化检查线程函数
        """
        # 刷新所有状态
        self.refresh_all_status()
        
        # 刷新文件列表
        self.refresh_local_files()
        self.refresh_docker_files()
        
        # 刷新容器列表
        self.refresh_containers_list()
    
    def refresh_wsl_status(self):
        """
        刷新WSL状态
        """
        if is_wsl_running():
            self.label_wsl_status.config(text="运行中", foreground="green")
        else:
            self.label_wsl_status.config(text="未运行", foreground="red")
    
    def refresh_docker_status(self):
        """
        刷新Docker状态
        """
        if is_docker_running():
            self.label_docker_status.config(text="运行中", foreground="green")
        else:
            self.label_docker_status.config(text="未运行", foreground="red")
    
    def refresh_volume_status(self):
        """
        刷新Docker卷状态
        """
        if ensure_docker_volume():
            self.label_volume_status.config(text="存在", foreground="green")
            self.docker_volume_path = get_volume_mount_point()
        else:
            self.label_volume_status.config(text="不存在", foreground="red")
    
    def refresh_container_status(self):
        """
        刷新容器状态
        """
        code, output, _ = run_wsl_command("docker ps | grep binwalk")
        if code == 0 and output.strip():
            self.label_container_status.config(text="运行中", foreground="green")
            # 提取容器ID
            match = re.search(r'^([0-9a-f]+)', output.strip())
            if match:
                self.current_container_id = match.group(1)
        else:
            self.label_container_status.config(text="未运行", foreground="red")
            self.current_container_id = ""
    
    def refresh_all_status(self):
        """
        刷新所有状态
        """
        self.refresh_wsl_status()
        self.refresh_docker_status()
        self.refresh_volume_status()
        self.refresh_container_status()
    
    def start_docker_service(self):
        """
        启动Docker服务
        """
        # 在单独的线程中执行，避免界面卡顿
        thread = threading.Thread(target=self._start_docker_thread)
        thread.daemon = True
        thread.start()
    
    def _start_docker_thread(self):
        """
        启动Docker线程函数
        """
        if start_docker():
            self.root.after(1000, self.refresh_docker_status)
            messagebox.showinfo("成功", "Docker服务已成功启动")
        else:
            messagebox.showerror("失败", "Docker服务启动失败，请检查WSL环境")
    
    def create_docker_volume(self):
        """
        创建Docker卷
        """
        # 在单独的线程中执行，避免界面卡顿
        thread = threading.Thread(target=self._create_volume_thread)
        thread.daemon = True
        thread.start()
    
    def _create_volume_thread(self):
        """
        创建Docker卷线程函数
        """
        if ensure_docker_volume():
            self.root.after(1000, self.refresh_volume_status)
            messagebox.showinfo("成功", "Docker卷已成功创建")
        else:
            messagebox.showerror("失败", "Docker卷创建失败")
    
    def select_local_folder(self):
        """
        选择本地文件夹
        """
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.entry_local_path.delete(0, tk.END)
            self.entry_local_path.insert(0, folder_path)
            self.refresh_local_files()
    
    def refresh_local_files(self):
        """
        刷新本地文件列表
        """
        folder_path = self.entry_local_path.get()
        
        # 清空现有列表
        for item in self.local_files_tree.get_children():
            self.local_files_tree.delete(item)
        
        # 检查路径是否存在
        if not os.path.exists(folder_path):
            messagebox.showerror("错误", f"路径不存在: {folder_path}")
            return
        
        try:
            # 获取文件列表
            items = os.listdir(folder_path)
            
            for item in items:
                item_path = os.path.join(folder_path, item)
                try:
                    # 获取文件信息
                    stat_info = os.stat(item_path)
                    size = stat_info.st_size
                    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat_info.st_mtime))
                    
                    # 判断是否为目录
                    if os.path.isdir(item_path):
                        self.local_files_tree.insert("", "end", values=(item, "文件夹", date), tags=("folder",))
                    else:
                        # 格式化文件大小
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size/1024:.2f} KB"
                        elif size < 1024 * 1024 * 1024:
                            size_str = f"{size/(1024*1024):.2f} MB"
                        else:
                            size_str = f"{size/(1024*1024*1024):.2f} GB"
                        
                        self.local_files_tree.insert("", "end", values=(item, size_str, date), tags=("file",))
                except Exception as e:
                    print(f"获取文件信息失败: {item_path}, {e}")
        
        except Exception as e:
            messagebox.showerror("错误", f"读取文件夹失败: {str(e)}")
    
    def refresh_docker_files(self):
        """
        刷新Docker卷文件列表
        """
        # 清空现有列表
        for item in self.docker_files_tree.get_children():
            self.docker_files_tree.delete(item)
        
        # 检查Docker是否运行
        if not is_docker_running():
            messagebox.showinfo("提示", "Docker未运行，请先启动Docker服务")
            return
        
        # 检查卷是否存在
        if not ensure_docker_volume():
            messagebox.showinfo("提示", "Docker卷不存在，请先创建卷")
            return
        
        # 获取卷挂载点
        volume_path = get_volume_mount_point()
        if not volume_path:
            messagebox.showinfo("提示", "无法获取Docker卷挂载点")
            return
        
        # 读取Docker卷中的文件
        code, output, error = run_wsl_command(f"ls -la {volume_path}")
        if code != 0:
            messagebox.showerror("错误", f"读取Docker卷失败: {error}")
            return
        
        # 解析输出并添加到列表
        lines = output.strip().split("\n")
        for line in lines[1:]:  # 跳过标题行
            parts = line.split(" ")
            parts = [p for p in parts if p]
            if len(parts) >= 6:
                # 解析文件信息
                file_type = "文件夹" if parts[0].startswith("d") else "文件"
                size = parts[4]
                date = f"{parts[5]} {parts[6]} {parts[7]}"
                name = " ".join(parts[8:])
                
                if name not in (".", ".."):
                    self.docker_files_tree.insert("", "end", values=(name, size, date), tags=("folder" if file_type == "文件夹" else "file",))
    
    def upload_files(self):
        """
        上传文件到Docker卷
        """
        # 检查Docker是否运行
        if not is_docker_running():
            messagebox.showinfo("提示", "Docker未运行，请先启动Docker服务")
            return
        
        # 检查卷是否存在
        if not ensure_docker_volume():
            messagebox.showinfo("提示", "Docker卷不存在，请先创建卷")
            return
        
        # 获取选中的文件
        selected_items = self.local_files_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请选择要上传的文件")
            return
        
        # 获取本地路径和Docker路径
        local_folder = self.entry_local_path.get()
        docker_path = self.entry_docker_path.get()
        
        # 获取卷挂载点
        volume_path = get_volume_mount_point()
        if not volume_path:
            messagebox.showinfo("提示", "无法获取Docker卷挂载点")
            return
        
        # 在单独的线程中执行上传，避免界面卡顿
        thread = threading.Thread(target=self._upload_files_thread, 
                                args=(selected_items, local_folder, volume_path, docker_path))
        thread.daemon = True
        thread.start()
    
    def _upload_files_thread(self, selected_items, local_folder, volume_path, docker_path):
        """
        上传文件线程函数
        
        参数:
            selected_items: list, 选中的文件项
            local_folder: str, 本地文件夹路径
            volume_path: str, Docker卷挂载点
            docker_path: str, Docker容器中的路径
        """
        success_count = 0
        fail_count = 0
        
        for item in selected_items:
            file_name = self.local_files_tree.item(item, "values")[0]
            local_file_path = os.path.join(local_folder, file_name)
            
            # 构造WSL中的目标路径
            # 将Windows路径转换为WSL路径格式
            wsl_local_path = local_file_path.replace("\\", "/")
            drive_letter = wsl_local_path[0].lower()
            wsl_local_path = f"/mnt/{drive_letter}{wsl_local_path[2:]}"
            
            # 目标路径
            wsl_target_path = f"{volume_path}{docker_path}"
            
            # 确保目标目录存在
            run_wsl_command(f"mkdir -p {wsl_target_path}")
            
            # 复制文件
            if os.path.isdir(local_file_path):
                # 复制目录
                cmd = f"cp -r {wsl_local_path} {wsl_target_path}"
            else:
                # 复制文件
                cmd = f"cp {wsl_local_path} {wsl_target_path}"
            
            code, output, error = run_wsl_command(cmd)
            if code == 0:
                success_count += 1
            else:
                fail_count += 1
                print(f"上传失败: {file_name}, {error}")
        
        # 刷新Docker文件列表
        self.root.after(100, self.refresh_docker_files)
        
        # 显示结果
        if fail_count == 0:
            messagebox.showinfo("成功", f"所有 {success_count} 个文件上传成功")
        else:
            messagebox.showwarning("部分成功", f"{success_count} 个文件上传成功，{fail_count} 个文件上传失败")
    
    def download_files(self):
        """
        从Docker卷下载文件
        """
        # 检查Docker是否运行
        if not is_docker_running():
            messagebox.showinfo("提示", "Docker未运行，请先启动Docker服务")
            return
        
        # 检查卷是否存在
        if not ensure_docker_volume():
            messagebox.showinfo("提示", "Docker卷不存在，请先创建卷")
            return
        
        # 获取选中的文件
        selected_items = self.docker_files_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请选择要下载的文件")
            return
        
        # 获取本地路径和Docker路径
        local_folder = self.entry_local_path.get()
        docker_path = self.entry_docker_path.get()
        
        # 获取卷挂载点
        volume_path = get_volume_mount_point()
        if not volume_path:
            messagebox.showinfo("提示", "无法获取Docker卷挂载点")
            return
        
        # 在单独的线程中执行下载，避免界面卡顿
        thread = threading.Thread(target=self._download_files_thread, 
                                args=(selected_items, local_folder, volume_path, docker_path))
        thread.daemon = True
        thread.start()
    
    def _download_files_thread(self, selected_items, local_folder, volume_path, docker_path):
        """
        下载文件线程函数
        
        参数:
            selected_items: list, 选中的文件项
            local_folder: str, 本地文件夹路径
            volume_path: str, Docker卷挂载点
            docker_path: str, Docker容器中的路径
        """
        success_count = 0
        fail_count = 0
        
        for item in selected_items:
            file_name = self.docker_files_tree.item(item, "values")[0]
            
            # 构造WSL中的源路径
            wsl_source_path = f"{volume_path}{docker_path}/{file_name}"
            
            # 将Windows路径转换为WSL路径格式
            wsl_local_folder = local_folder.replace("\\", "/")
            drive_letter = wsl_local_folder[0].lower()
            wsl_local_folder = f"/mnt/{drive_letter}{wsl_local_folder[2:]}"
            
            # 复制文件
            cmd = f"cp -r {wsl_source_path} {wsl_local_folder}"
            code, output, error = run_wsl_command(cmd)
            
            if code == 0:
                success_count += 1
            else:
                fail_count += 1
                print(f"下载失败: {file_name}, {error}")
        
        # 刷新本地文件列表
        self.root.after(100, self.refresh_local_files)
        
        # 显示结果
        if fail_count == 0:
            messagebox.showinfo("成功", f"所有 {success_count} 个文件下载成功")
        else:
            messagebox.showwarning("部分成功", f"{success_count} 个文件下载成功，{fail_count} 个文件下载失败")
    
    def run_binwalk_command(self):
        """
        执行Binwalk命令
        """
        # 检查Docker是否运行
        if not is_docker_running():
            messagebox.showinfo("提示", "Docker未运行，请先启动Docker服务")
            return
        
        # 获取命令
        command = self.entry_command.get().strip()
        if not command:
            messagebox.showinfo("提示", "请输入要执行的命令")
            return
        
        # 确保容器正在运行
        if not self.current_container_id:
            # 启动容器
            if not self._start_binwalk_container():
                messagebox.showerror("失败", "无法启动Binwalk容器")
                return
        
        # 清空输出
        self.text_output.config(state=tk.NORMAL)
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, f"执行命令: {command}\n\n")
        self.text_output.config(state=tk.DISABLED)
        
        # 在单独的线程中执行命令，避免界面卡顿
        thread = threading.Thread(target=self._run_command_thread, args=(command,))
        thread.daemon = True
        thread.start()
    
    def _start_binwalk_container(self):
        """
        启动Binwalk容器
        
        返回:
            bool: True表示启动成功，False表示失败
        """
        # 确保卷存在
        if not ensure_docker_volume():
            return False
        
        # 检查是否已有容器在运行
        code, output, _ = run_wsl_command("docker ps | grep binwalk")
        if code == 0 and output.strip():
            # 提取容器ID
            match = re.search(r'^([0-9a-f]+)', output.strip())
            if match:
                self.current_container_id = match.group(1)
                return True
        
        # 检查是否有停止的容器
        code, output, _ = run_wsl_command("docker ps -a | grep binwalk")
        if code == 0 and output.strip():
            # 提取容器ID
            match = re.search(r'^([0-9a-f]+)', output.strip())
            if match:
                container_id = match.group(1)
                # 启动容器
                code, output, error = run_wsl_command(f"docker start {container_id}")
                if code == 0:
                    self.current_container_id = container_id
                    return True
        
        # 创建新容器
        # 基于docker-Compose配置创建容器
        cmd = "docker run -d --name binwalkv3 -v binwalkv3:/analysis refirmlabs/binwalk:latest sleep infinity"
        code, output, error = run_wsl_command(cmd)
        if code == 0:
            self.current_container_id = output.strip()
            return True
        
        return False
    
    def _run_command_thread(self, command):
        """
        执行命令线程函数
        
        参数:
            command: str, 要执行的命令
        """
        # 在容器中执行命令
        full_command = f"docker exec -it {self.current_container_id} bash -c '{command}'"
        
        process = subprocess.Popen(
            f'wsl -d kali-linux -e bash -c "{full_command}"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # 实时显示输出
        for line in process.stdout:
            line = line.rstrip()
            self.root.after(0, self._append_output, line)
        
        process.wait()
        
        # 显示命令完成
        status = "成功" if process.returncode == 0 else f"失败 (返回码: {process.returncode})"
        self.root.after(0, self._append_output, f"\n命令执行{status}")
    
    def _append_output(self, text):
        """
        追加输出到文本区域
        
        参数:
            text: str, 要追加的文本
        """
        self.text_output.config(state=tk.NORMAL)
        self.text_output.insert(tk.END, text + "\n")
        self.text_output.see(tk.END)
        self.text_output.config(state=tk.DISABLED)
    
    def start_container(self):
        """
        启动容器
        """
        if self._start_binwalk_container():
            self.refresh_container_status()
            self.refresh_containers_list()
            messagebox.showinfo("成功", "容器启动成功")
        else:
            messagebox.showerror("失败", "容器启动失败")
    
    def stop_container(self):
        """
        停止容器
        """
        if not self.current_container_id:
            messagebox.showinfo("提示", "没有正在运行的容器")
            return
        
        code, output, error = run_wsl_command(f"docker stop {self.current_container_id}")
        if code == 0:
            self.current_container_id = ""
            self.refresh_container_status()
            self.refresh_containers_list()
            messagebox.showinfo("成功", "容器停止成功")
        else:
            messagebox.showerror("失败", f"容器停止失败: {error}")
    
    def restart_container(self):
        """
        重启容器
        """
        if not self.current_container_id:
            messagebox.showinfo("提示", "没有正在运行的容器")
            return
        
        code, output, error = run_wsl_command(f"docker restart {self.current_container_id}")
        if code == 0:
            self.refresh_container_status()
            self.refresh_containers_list()
            messagebox.showinfo("成功", "容器重启成功")
        else:
            messagebox.showerror("失败", f"容器重启失败: {error}")
    
    def remove_container(self):
        """
        移除容器
        """
        # 先停止容器
        if self.current_container_id:
            self.stop_container()
        
        # 查找所有binwalk相关容器
        code, output, _ = run_wsl_command("docker ps -a | grep binwalk")
        if code != 0 or not output.strip():
            messagebox.showinfo("提示", "没有找到binwalk相关容器")
            return
        
        # 获取容器ID
        match = re.search(r'^([0-9a-f]+)', output.strip())
        if not match:
            messagebox.showinfo("提示", "无法解析容器信息")
            return
        
        container_id = match.group(1)
        
        # 移除容器
        code, output, error = run_wsl_command(f"docker rm {container_id}")
        if code == 0:
            self.current_container_id = ""
            self.refresh_container_status()
            self.refresh_containers_list()
            messagebox.showinfo("成功", "容器移除成功")
        else:
            messagebox.showerror("失败", f"容器移除失败: {error}")
    
    def refresh_containers_list(self):
        """
        刷新容器列表
        """
        # 清空现有列表
        for item in self.containers_tree.get_children():
            self.containers_tree.delete(item)
        
        # 检查Docker是否运行
        if not is_docker_running():
            return
        
        # 获取容器列表
        code, output, error = run_wsl_command("docker ps -a")
        if code != 0:
            print(f"获取容器列表失败: {error}")
            return
        
        # 解析输出并添加到列表
        lines = output.strip().split("\n")
        for line in lines[1:]:  # 跳过标题行
            parts = line.split(" ")
            parts = [p for p in parts if p]
            if len(parts) >= 7:
                # 解析容器信息
                container_id = parts[0]
                image = parts[1]
                status = parts[5] if len(parts) >= 6 else ""
                ports = parts[6] if len(parts) >= 7 else ""
                names = " ".join(parts[7:]) if len(parts) >= 8 else ""
                
                # 检查是否为binwalk容器
                if "binwalk" in image.lower() or "binwalk" in names.lower():
                    self.containers_tree.insert("", "end", values=(container_id[:12], image, status, ports, names))
    
    def update_container_info(self):
        """
        更新容器信息
        """
        if not self.current_container_id:
            return
        
        # 获取容器详细信息
        code, output, error = run_wsl_command(f"docker inspect {self.current_container_id}")
        if code != 0:
            print(f"获取容器信息失败: {error}")
            return
        
        # 显示容器信息
        self.text_container_info.config(state=tk.NORMAL)
        self.text_container_info.delete(1.0, tk.END)
        self.text_container_info.insert(tk.END, output)
        self.text_container_info.config(state=tk.DISABLED)

if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("请使用Python 3.6或更高版本")
        sys.exit(1)
    
    # 创建并运行GUI
    root = tk.Tk()
    app = BinwalkGUI(root)
    root.mainloop()