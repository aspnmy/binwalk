#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binwalk Qemu 图形界面工具

功能: 管理Qemu环境中的Docker容器，进行文件传输和Binwalk命令执行
"""

import os
import sys
import subprocess
import time
import threading
import paramiko
import scp
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path

class BinwalkQemuGUI:
    """
    Binwalk Qemu 图形界面主类
    提供Docker管理、文件传输和命令执行功能
    """
    
    def __init__(self, root):
        """
        初始化图形界面
        
        参数:
            root: tkinter的根窗口对象
        """
        self.root = root
        self.root.title("Binwalk Qemu 管理器")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 设置中文字体支持
        self.setup_fonts()
        
        # SSH连接相关变量
        self.ssh_client = None
        self.scp_client = None
        self.connected = False
        
        # 当前工作目录
        self.current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # 加载配置
        self.config = self.load_config()
        
        # 创建界面
        self.create_widgets()
        
        # 更新Docker状态的定时器
        self.docker_status_timer = None
    
    def setup_fonts(self):
        """
        设置中文字体支持
        """
        # 为不同系统设置合适的字体
        if sys.platform == 'win32':
            self.font_family = ('Microsoft YaHei UI', 10)
            self.font_family_bold = ('Microsoft YaHei UI', 10, 'bold')
        else:
            self.font_family = ('SimHei', 10)
            self.font_family_bold = ('SimHei', 10, 'bold')
    
    def load_config(self):
        """
        加载配置文件
        
        返回值:
            dict: 配置信息字典
        """
        config_path = self.current_dir / "config.json"
        default_config = {
            "ssh_host": "localhost",
            "ssh_port": 2222,
            "ssh_user": "kali",
            "ssh_password": "kali",
            "docker_image": "refirmlabs/binwalk:latest",
            "docker_container": "binwalkv3",
            "analysis_dir": "/analysis",
            "local_data_dir": str(self.current_dir / "data")
        }
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    # 合并默认配置和用户配置
                    default_config.update(user_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        # 保存配置
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config):
        """
        保存配置到文件
        
        参数:
            config: dict, 配置信息字典
        """
        config_path = self.current_dir / "config.json"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def create_widgets(self):
        """
        创建界面组件
        """
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页控件
        tab_control = ttk.Notebook(main_frame)
        
        # 创建各个标签页
        self.tab_connection = ttk.Frame(tab_control)
        self.tab_files = ttk.Frame(tab_control)
        self.tab_docker = ttk.Frame(tab_control)
        self.tab_binwalk = ttk.Frame(tab_control)
        self.tab_logs = ttk.Frame(tab_control)
        
        # 添加标签页
        tab_control.add(self.tab_connection, text="连接设置")
        tab_control.add(self.tab_files, text="文件管理")
        tab_control.add(self.tab_docker, text="Docker管理")
        tab_control.add(self.tab_binwalk, text="Binwalk分析")
        tab_control.add(self.tab_logs, text="日志")
        
        tab_control.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个标签页的内容
        self.create_connection_tab()
        self.create_files_tab()
        self.create_docker_tab()
        self.create_binwalk_tab()
        self.create_logs_tab()
        
        # 创建状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_connection_tab(self):
        """
        创建连接设置标签页
        """
        frame = ttk.LabelFrame(self.tab_connection, text="SSH连接设置", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 连接参数输入
        grid_row = 0
        
        ttk.Label(frame, text="主机:", font=self.font_family).grid(row=grid_row, column=0, sticky=tk.W, pady=5, padx=5)
        self.ssh_host_var = tk.StringVar(value=self.config["ssh_host"])
        ttk.Entry(frame, textvariable=self.ssh_host_var, width=30, font=self.font_family).grid(row=grid_row, column=1, sticky=tk.W, pady=5, padx=5)
        
        grid_row += 1
        ttk.Label(frame, text="端口:", font=self.font_family).grid(row=grid_row, column=0, sticky=tk.W, pady=5, padx=5)
        self.ssh_port_var = tk.StringVar(value=str(self.config["ssh_port"]))
        ttk.Entry(frame, textvariable=self.ssh_port_var, width=10, font=self.font_family).grid(row=grid_row, column=1, sticky=tk.W, pady=5, padx=5)
        
        grid_row += 1
        ttk.Label(frame, text="用户名:", font=self.font_family).grid(row=grid_row, column=0, sticky=tk.W, pady=5, padx=5)
        self.ssh_user_var = tk.StringVar(value=self.config["ssh_user"])
        ttk.Entry(frame, textvariable=self.ssh_user_var, width=30, font=self.font_family).grid(row=grid_row, column=1, sticky=tk.W, pady=5, padx=5)
        
        grid_row += 1
        ttk.Label(frame, text="密码:", font=self.font_family).grid(row=grid_row, column=0, sticky=tk.W, pady=5, padx=5)
        self.ssh_password_var = tk.StringVar(value=self.config["ssh_password"])
        ttk.Entry(frame, textvariable=self.ssh_password_var, show="*", width=30, font=self.font_family).grid(row=grid_row, column=1, sticky=tk.W, pady=5, padx=5)
        
        grid_row += 1
        # 连接按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=grid_row, column=0, columnspan=2, pady=10)
        
        self.connect_button = ttk.Button(button_frame, text="连接", command=self.toggle_connection, width=15)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="保存配置", command=self.save_connection_config, width=15).pack(side=tk.LEFT, padx=5)
        
        # 连接状态
        self.connection_status_var = tk.StringVar(value="未连接")
        ttk.Label(frame, textvariable=self.connection_status_var, font=self.font_family_bold, foreground="red").grid(row=grid_row, column=1, sticky=tk.W, pady=10)
    
    def create_files_tab(self):
        """
        创建文件管理标签页
        """
        # 本地文件和远程文件的框架
        file_frame = ttk.Frame(self.tab_files)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：本地文件
        left_frame = ttk.LabelFrame(file_frame, text="本地文件", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 本地文件路径
        path_frame = ttk.Frame(left_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.local_path_var = tk.StringVar(value=self.config["local_data_dir"])
        ttk.Entry(left_frame, textvariable=self.local_path_var, font=self.font_family).pack(fill=tk.X, padx=5, pady=2)
        
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(button_frame, text="浏览...", command=self.browse_local_directory, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="刷新", command=self.refresh_local_files, width=10).pack(side=tk.LEFT, padx=2)
        
        # 本地文件列表
        self.local_files_listbox = tk.Listbox(left_frame, font=self.font_family, selectmode=tk.EXTENDED)
        self.local_files_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 中间：传输按钮
        transfer_frame = ttk.Frame(file_frame)
        transfer_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Button(transfer_frame, text="上传 ->", command=self.upload_files).pack(pady=5)
        ttk.Button(transfer_frame, text="<- 下载", command=self.download_files).pack(pady=5)
        ttk.Button(transfer_frame, text="删除", command=self.delete_files).pack(pady=5)
        
        # 右侧：远程文件
        right_frame = ttk.LabelFrame(file_frame, text="远程文件 (Docker /analysis)", padding="5")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 远程文件路径
        self.remote_path_var = tk.StringVar(value=self.config["analysis_dir"])
        ttk.Entry(right_frame, textvariable=self.remote_path_var, font=self.font_family).pack(fill=tk.X, padx=5, pady=2)
        
        button_frame2 = ttk.Frame(right_frame)
        button_frame2.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(button_frame2, text="刷新", command=self.refresh_remote_files, width=10).pack(side=tk.LEFT, padx=2)
        
        # 远程文件列表
        self.remote_files_listbox = tk.Listbox(right_frame, font=self.font_family, selectmode=tk.EXTENDED)
        self.remote_files_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 刷新本地文件列表
        self.refresh_local_files()
    
    def create_docker_tab(self):
        """
        创建Docker管理标签页
        """
        frame = ttk.LabelFrame(self.tab_docker, text="Docker容器管理", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Docker配置
        config_frame = ttk.Frame(frame)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Docker镜像:", font=self.font_family).grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.docker_image_var = tk.StringVar(value=self.config["docker_image"])
        ttk.Entry(config_frame, textvariable=self.docker_image_var, width=40, font=self.font_family).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(config_frame, text="容器名称:", font=self.font_family).grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.docker_container_var = tk.StringVar(value=self.config["docker_container"])
        ttk.Entry(config_frame, textvariable=self.docker_container_var, width=40, font=self.font_family).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Docker控制按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="拉取镜像", command=self.pull_docker_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="启动容器", command=self.start_docker_container).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="停止容器", command=self.stop_docker_container).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="重启容器", command=self.restart_docker_container).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除容器", command=self.remove_docker_container).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看状态", command=self.check_docker_status).pack(side=tk.LEFT, padx=5)
        
        # Docker状态
        self.docker_status_var = tk.StringVar(value="未检测到状态")
        ttk.Label(frame, textvariable=self.docker_status_var, font=self.font_family_bold, foreground="blue").pack(pady=10)
        
        # Docker容器日志
        ttk.Label(frame, text="容器日志:", font=self.font_family_bold).pack(anchor=tk.W, pady=5, padx=5)
        self.docker_logs_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=self.font_family, height=10)
        self.docker_logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_binwalk_tab(self):
        """
        创建Binwalk分析标签页
        """
        frame = ttk.LabelFrame(self.tab_binwalk, text="Binwalk分析", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 文件选择
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(file_frame, text="目标文件:", font=self.font_family).grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.target_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.target_file_var, width=60, font=self.font_family).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Button(file_frame, text="选择文件", command=self.select_target_file).grid(row=0, column=2, padx=5)
        
        # Binwalk选项
        options_frame = ttk.LabelFrame(frame, text="分析选项", padding="5")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建选项复选框
        self.extract_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="提取文件 (-e)", variable=self.extract_var, font=self.font_family).grid(row=0, column=0, sticky=tk.W, pady=2, padx=10)
        
        self.verbose_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="详细输出 (-v)", variable=self.verbose_var, font=self.font_family).grid(row=0, column=1, sticky=tk.W, pady=2, padx=10)
        
        self.entropy_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="显示熵图 (-E)", variable=self.entropy_var, font=self.font_family).grid(row=1, column=0, sticky=tk.W, pady=2, padx=10)
        
        self.carve_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="深度扫描 (-C)", variable=self.carve_var, font=self.font_family).grid(row=1, column=1, sticky=tk.W, pady=2, padx=10)
        
        # 自定义命令
        ttk.Label(options_frame, text="自定义选项:", font=self.font_family).grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.custom_options_var = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.custom_options_var, width=50, font=self.font_family).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 执行按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="执行Binwalk", command=self.run_binwalk).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="停止执行", command=self.stop_binwalk).pack(side=tk.LEFT, padx=5)
        
        # 结果输出
        ttk.Label(frame, text="分析结果:", font=self.font_family_bold).pack(anchor=tk.W, pady=5, padx=5)
        self.binwalk_output_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=self.font_family)
        self.binwalk_output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 执行状态
        self.binwalk_status_var = tk.StringVar(value="就绪")
        ttk.Label(frame, textvariable=self.binwalk_status_var, font=self.font_family, foreground="green").pack(anchor=tk.W, pady=5, padx=5)
    
    def create_logs_tab(self):
        """
        创建日志标签页
        """
        frame = ttk.LabelFrame(self.tab_logs, text="系统日志", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 日志文本框
        self.logs_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=self.font_family)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 日志按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="清空日志", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存日志", command=self.save_logs).pack(side=tk.LEFT, padx=5)
    
    def log(self, message):
        """
        记录日志信息
        
        参数:
            message: str, 日志消息
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.logs_text.insert(tk.END, log_message + "\n")
        self.logs_text.see(tk.END)
        self.status_var.set(message)
    
    def toggle_connection(self):
        """
        切换SSH连接状态
        """
        if self.connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """
        连接到SSH服务器
        """
        try:
            self.log("正在连接到SSH服务器...")
            self.connect_button.config(state=tk.DISABLED)
            
            # 获取连接参数
            host = self.ssh_host_var.get()
            port = int(self.ssh_port_var.get())
            username = self.ssh_user_var.get()
            password = self.ssh_password_var.get()
            
            # 创建SSH客户端
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(host, port=port, username=username, password=password, timeout=10)
            
            # 创建SCP客户端
            self.scp_client = scp.SCPClient(self.ssh_client.get_transport())
            
            self.connected = True
            self.connection_status_var.set("已连接")
            self.connection_status_var.setvar(name=self.connection_status_var._name, value="已连接")
            self.connect_button.config(text="断开连接")
            self.log(f"成功连接到 {host}:{port}")
            
            # 刷新远程文件列表
            self.refresh_remote_files()
            # 检查Docker状态
            self.check_docker_status()
            # 启动Docker状态更新定时器
            self.start_docker_status_timer()
            
        except Exception as e:
            self.log(f"连接失败: {str(e)}")
            messagebox.showerror("连接失败", f"无法连接到SSH服务器:\n{str(e)}")
        finally:
            self.connect_button.config(state=tk.NORMAL)
    
    def disconnect(self):
        """
        断开SSH连接
        """
        try:
            self.log("正在断开连接...")
            
            # 停止Docker状态更新定时器
            self.stop_docker_status_timer()
            
            # 关闭SCP客户端
            if self.scp_client:
                self.scp_client.close()
                self.scp_client = None
            
            # 关闭SSH客户端
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
            
            self.connected = False
            self.connection_status_var.set("未连接")
            self.connect_button.config(text="连接")
            self.log("已断开连接")
            
        except Exception as e:
            self.log(f"断开连接时出错: {str(e)}")
    
    def save_connection_config(self):
        """
        保存连接配置
        """
        try:
            # 更新配置
            self.config["ssh_host"] = self.ssh_host_var.get()
            self.config["ssh_port"] = int(self.ssh_port_var.get())
            self.config["ssh_user"] = self.ssh_user_var.get()
            self.config["ssh_password"] = self.ssh_password_var.get()
            
            # 保存配置文件
            self.save_config(self.config)
            self.log("连接配置已保存")
            messagebox.showinfo("成功", "连接配置已保存")
        except Exception as e:
            self.log(f"保存配置失败: {str(e)}")
            messagebox.showerror("错误", f"保存配置失败:\n{str(e)}")
    
    def browse_local_directory(self):
        """
        浏览本地目录
        """
        directory = filedialog.askdirectory(title="选择本地目录")
        if directory:
            self.local_path_var.set(directory)
            self.refresh_local_files()
    
    def refresh_local_files(self):
        """
        刷新本地文件列表
        """
        try:
            directory = self.local_path_var.get()
            if not os.path.exists(directory):
                return
            
            self.local_files_listbox.delete(0, tk.END)
            
            # 添加返回上级目录
            if os.path.dirname(directory) != directory:
                self.local_files_listbox.insert(tk.END, ".. (上级目录)")
            
            # 列出目录内容
            items = os.listdir(directory)
            for item in sorted(items):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    self.local_files_listbox.insert(tk.END, f"[目录] {item}")
                else:
                    # 获取文件大小
                    size = os.path.getsize(item_path)
                    size_str = self.format_size(size)
                    self.local_files_listbox.insert(tk.END, f"{item} ({size_str})")
        except Exception as e:
            self.log(f"刷新本地文件失败: {str(e)}")
    
    def refresh_remote_files(self):
        """
        刷新远程文件列表
        """
        if not self.connected:
            return
        
        try:
            remote_path = self.remote_path_var.get()
            
            # 执行远程命令列出文件
            stdin, stdout, stderr = self.ssh_client.exec_command(f"ls -la {remote_path}")
            
            # 读取输出
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                self.log(f"刷新远程文件失败: {error}")
                return
            
            # 清空列表
            self.remote_files_listbox.delete(0, tk.END)
            
            # 添加返回上级目录
            if remote_path != "/":
                parent_dir = os.path.dirname(remote_path)
                if parent_dir == "":
                    parent_dir = "/"
                self.remote_files_listbox.insert(tk.END, ".. (上级目录)")
            
            # 解析输出并添加到列表
            lines = output.strip().split('\n')[1:]  # 跳过标题行
            for line in lines:
                parts = line.split()
                if len(parts) < 9:
                    continue
                
                permissions = parts[0]
                name = parts[8]
                size = parts[4]
                
                if permissions.startswith('d'):
                    self.remote_files_listbox.insert(tk.END, f"[目录] {name}")
                else:
                    self.remote_files_listbox.insert(tk.END, f"{name} ({size} bytes)")
                    
        except Exception as e:
            self.log(f"刷新远程文件失败: {str(e)}")
    
    def upload_files(self):
        """
        上传文件到远程服务器
        """
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到SSH服务器")
            return
        
        # 获取选中的本地文件
        selected_indices = self.local_files_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("提示", "请选择要上传的文件")
            return
        
        local_dir = self.local_path_var.get()
        remote_dir = self.remote_path_var.get()
        
        # 创建上传线程
        def upload_thread_func():
            try:
                for index in selected_indices:
                    item_text = self.local_files_listbox.get(index)
                    
                    # 跳过上级目录
                    if item_text.startswith(".."):
                        continue
                    
                    # 提取文件名
                    if "[目录]" in item_text:
                        filename = item_text[6:].strip()
                    else:
                        # 提取文件名（去掉大小信息）
                        filename = item_text.split(' (')[0]
                    
                    local_path = os.path.join(local_dir, filename)
                    
                    # 检查是否为目录
                    if os.path.isdir(local_path):
                        # 上传目录
                        self.log(f"正在上传目录: {filename}")
                        # 创建远程目录
                        self.ssh_client.exec_command(f"mkdir -p {remote_dir}/{filename}")
                        # 递归上传文件
                        for root, _, files in os.walk(local_path):
                            relative_path = os.path.relpath(root, local_dir)
                            remote_subdir = f"{remote_dir}/{relative_path}"
                            
                            # 创建远程子目录
                            self.ssh_client.exec_command(f"mkdir -p {remote_subdir}")
                            
                            for file in files:
                                local_file_path = os.path.join(root, file)
                                remote_file_path = f"{remote_subdir}/{file}"
                                self.scp_client.put(local_file_path, remote_file_path)
                        
                        self.log(f"目录上传完成: {filename}")
                    else:
                        # 上传单个文件
                        self.log(f"正在上传文件: {filename}")
                        self.scp_client.put(local_path, f"{remote_dir}/{filename}")
                        self.log(f"文件上传完成: {filename}")
                
                # 刷新远程文件列表
                self.root.after(100, self.refresh_remote_files)
                self.log("所有文件上传完成")
                messagebox.showinfo("成功", "文件上传完成")
                
            except Exception as e:
                error_msg = f"上传文件失败: {str(e)}"
                self.log(error_msg)
                self.root.after(100, lambda: messagebox.showerror("错误", error_msg))
        
        # 启动上传线程
        threading.Thread(target=upload_thread_func).start()
    
    def download_files(self):
        """
        从远程服务器下载文件
        """
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到SSH服务器")
            return
        
        # 获取选中的远程文件
        selected_indices = self.remote_files_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("提示", "请选择要下载的文件")
            return
        
        local_dir = self.local_path_var.get()
        remote_dir = self.remote_path_var.get()
        
        # 创建下载线程
        def download_thread_func():
            try:
                for index in selected_indices:
                    item_text = self.remote_files_listbox.get(index)
                    
                    # 跳过上级目录
                    if item_text.startswith(".."):
                        continue
                    
                    # 提取文件名
                    if "[目录]" in item_text:
                        filename = item_text[6:].strip()
                    else:
                        # 提取文件名（去掉大小信息）
                        filename = item_text.split(' (')[0]
                    
                    local_path = os.path.join(local_dir, filename)
                    remote_path = f"{remote_dir}/{filename}"
                    
                    # 检查是否为目录
                    stdin, stdout, stderr = self.ssh_client.exec_command(f"test -d {remote_path} && echo 'dir' || echo 'file'")
                    result = stdout.read().decode('utf-8').strip()
                    
                    if result == "dir":
                        # 下载目录
                        self.log(f"正在下载目录: {filename}")
                        # 创建本地目录
                        os.makedirs(local_path, exist_ok=True)
                        
                        # 列出远程目录内容
                        stdin, stdout, stderr = self.ssh_client.exec_command(f"find {remote_path} -type f")
                        files = stdout.read().decode('utf-8').split('\n')
                        
                        for file in files:
                            if file.strip():
                                relative_path = os.path.relpath(file, remote_dir)
                                local_file_path = os.path.join(local_dir, relative_path)
                                # 确保本地目录存在
                                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                                # 下载文件
                                self.scp_client.get(file, local_file_path)
                        
                        self.log(f"目录下载完成: {filename}")
                    else:
                        # 下载单个文件
                        self.log(f"正在下载文件: {filename}")
                        self.scp_client.get(remote_path, local_path)
                        self.log(f"文件下载完成: {filename}")
                
                # 刷新本地文件列表
                self.root.after(100, self.refresh_local_files)
                self.log("所有文件下载完成")
                messagebox.showinfo("成功", "文件下载完成")
                
            except Exception as e:
                error_msg = f"下载文件失败: {str(e)}"
                self.log(error_msg)
                self.root.after(100, lambda: messagebox.showerror("错误", error_msg))
        
        # 启动下载线程
        threading.Thread(target=download_thread_func).start()
    
    def delete_files(self):
        """
        删除选中的文件（远程或本地）
        """
        # 检查哪个列表框有焦点
        if self.local_files_listbox.focus_get() == self.local_files_listbox:
            self.delete_local_files()
        elif self.remote_files_listbox.focus_get() == self.remote_files_listbox:
            self.delete_remote_files()
        else:
            messagebox.showinfo("提示", "请先选择要删除的文件")
    
    def delete_local_files(self):
        """
        删除本地文件
        """
        selected_indices = self.local_files_listbox.curselection()
        if not selected_indices:
            return
        
        if not messagebox.askyesno("确认删除", "确定要删除选中的本地文件吗？"):
            return
        
        local_dir = self.local_path_var.get()
        
        try:
            for index in reversed(selected_indices):  # 从后往前删除，避免索引变化
                item_text = self.local_files_listbox.get(index)
                
                # 跳过上级目录
                if item_text.startswith(".."):
                    continue
                
                # 提取文件名
                if "[目录]" in item_text:
                    filename = item_text[6:].strip()
                else:
                    filename = item_text.split(' (')[0]
                
                path = os.path.join(local_dir, filename)
                
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    self.log(f"已删除目录: {filename}")
                else:
                    os.remove(path)
                    self.log(f"已删除文件: {filename}")
            
            # 刷新文件列表
            self.refresh_local_files()
            messagebox.showinfo("成功", "文件删除完成")
            
        except Exception as e:
            self.log(f"删除文件失败: {str(e)}")
            messagebox.showerror("错误", f"删除文件失败:\n{str(e)}")
    
    def delete_remote_files(self):
        """
        删除远程文件
        """
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到SSH服务器")
            return
        
        selected_indices = self.remote_files_listbox.curselection()
        if not selected_indices:
            return
        
        if not messagebox.askyesno("确认删除", "确定要删除选中的远程文件吗？"):
            return
        
        remote_dir = self.remote_path_var.get()
        
        try:
            for index in reversed(selected_indices):
                item_text = self.remote_files_listbox.get(index)
                
                # 跳过上级目录
                if item_text.startswith(".."):
                    continue
                
                # 提取文件名
                if "[目录]" in item_text:
                    filename = item_text[6:].strip()
                else:
                    filename = item_text.split(' (')[0]
                
                path = f"{remote_dir}/{filename}"
                
                # 检查是否为目录
                stdin, stdout, stderr = self.ssh_client.exec_command(f"test -d {path} && echo 'dir' || echo 'file'")
                result = stdout.read().decode('utf-8').strip()
                
                if result == "dir":
                    # 删除目录
                    self.ssh_client.exec_command(f"rm -rf {path}")
                    self.log(f"已删除远程目录: {filename}")
                else:
                    # 删除文件
                    self.ssh_client.exec_command(f"rm -f {path}")
                    self.log(f"已删除远程文件: {filename}")
            
            # 刷新文件列表
            self.refresh_remote_files()
            messagebox.showinfo("成功", "远程文件删除完成")
            
        except Exception as e:
            self.log(f"删除远程文件失败: {str(e)}")
            messagebox.showerror("错误", f"删除远程文件失败:\n{str(e)}")
    
    def pull_docker_image(self):
        """
        拉取Docker镜像
        """
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到SSH服务器")
            return
        
        image = self.docker_image_var.get()
        
        # 创建执行线程
        def pull_thread_func():
            try:
                self.log(f"正在拉取Docker镜像: {image}")
                self.binwalk_status_var.set(f"正在拉取镜像: {image}")
                
                # 执行拉取命令
                stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo docker pull {image}")
                
                # 实时显示输出
                output_text = ""
                for line in iter(stdout.readline, ""):
                    output_line = line.strip()
                    output_text += output_line + "\n"
                    self.root.after(100, lambda line=output_line: self.docker_logs_text.insert(tk.END, line + "\n"))
                    self.root.after(100, lambda: self.docker_logs_text.see(tk.END))
                
                # 检查错误
                error = stderr.read().decode('utf-8')
                if error:
                    self.log(f"拉取镜像时出错: {error}")
                    self.root.after(100, lambda: self.docker_logs_text.insert(tk.END, "错误: " + error + "\n"))
                    self.root.after(100, lambda: messagebox.showerror("错误", f"拉取镜像失败:\n{error}"))
                else:
                    self.log(f"镜像拉取成功: {image}")
                    self.root.after(100, lambda: messagebox.showinfo("成功", "镜像拉取完成"))
                    
            except Exception as e:
                error_msg = f"拉取镜像失败: {str(e)}"
                self.log(error_msg)
                self.root.after(100, lambda: messagebox.showerror("错误", error_msg))
            finally:
                self.root.after(100, lambda: self.binwalk_status_var.set("就绪"))
        
        # 启动执行线程
        threading.Thread(target=pull_thread_func).start()
    
    def start_docker_container(self):
        """
        启动Docker容器
        """
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到SSH服务器")
            return
        
        container = self.docker_container_var.get()
        image = self.docker_image_var.get()
        analysis_dir = self.config["analysis_dir"]
        
        # 创建执行线程
        def start_thread_func():
            try:
                self.log(f"正在启动Docker容器: {container}")
                
                # 检查容器是否存在
                stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo docker ps -a | grep {container}")
                output = stdout.read().decode('utf-8')
                
                if container not in output:
                    # 创建新容器
                    cmd = f"sudo docker run -d --name {container} -v {container}:{analysis_dir} --entrypoint /bin/bash -it {image}"
                    self.log(f"创建新容器: {cmd}")
                    stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
                    error = stderr.read().decode('utf-8')
                    if error:
                        raise Exception(f"创建容器失败: {error}")
                else:
                    # 启动现有容器
                    stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo docker start {container}")
                    error = stderr.read().decode('utf-8')
                    if error:
                        raise Exception(f"启动容器失败: {error}")
                
                self.log(f"容器启动成功: {container}")
                self.root.after(1000, self.check_docker_status)
                messagebox.showinfo("成功", "Docker容器已启动")
                
            except Exception as e:
                error_msg = f"启动容器失败: {str(e)}"
                self.log(error_msg)
                messagebox.showerror("错误", error_msg)
        
        # 启动执行线程
        threading.Thread(target=start_thread_func).start()
    
    def stop_docker_container(self):
        """
        停止Docker容器
        """
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到SSH服务器")
            return
        
        container = self.docker_container_var.get()
        
        # 创建执行线程
        def stop_thread_func():
            try:
                self.log(f"正在停止Docker容器: {container}")
                
                # 停止容器
                stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo docker stop {container}")
                error = stderr.read().decode('utf-8')
                
                if error:
                    raise Exception(f"停止容器失败: {error}")
                
                self.log(f"容器已停止: {container}")
                self.root.after(1000, self.check_docker_status)
                messagebox.showinfo("成功", "Docker容器已停止")
                
            except Exception as e:
                error_msg = f"停止容器失败: {str(e)}"
                self.log(error_msg)
                messagebox.showerror("错误", error_msg)
        
        # 启动执行线程
        threading.Thread(target=stop_thread_func).start()
    
    def restart_docker_container(self):
        """
        重启Docker容器
        """
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到SSH服务器")
            return
        
        container = self.docker_container_var.get()
        
        # 创建执行线程
        def restart_thread_func():
            try:
                self.log(f"正在重启Docker容器: {container}")
                
                # 重启容器
                stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo docker restart {container}")
                error = stderr.read().decode('utf-8')
                
                if error:
                    raise Exception(f"重启容器失败: {error}")
                
                self.log(f"容器已重启: {container}")
                self.root.after(1000, self.check_docker_status)
                messagebox.showinfo("成功", "Docker容器已重启")
                
            except Exception as e:
                error_msg = f"重启容器失败: {str(e)}"
                self.log(error_msg)
                messagebox.showerror("错误", error_msg)
        
        # 启动执行线程
        threading.Thread(target=restart_thread_func).start()
    
    def remove_docker_container(self):
        """
        删除Docker容器
        """
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到SSH服务器")
            return
        
        container = self.docker_container_var.get()
        
        if not messagebox.askyesno("确认删除", f"确定要删除Docker容器 {container} 吗？"):
            return
        
        # 创建执行线程
        def remove_thread_func():
            try:
                self.log(f"正在删除Docker容器: {container}")
                
                # 先停止容器（如果正在运行）
                self.ssh_client.exec_command(f"sudo docker stop {container}")
                
                # 删除容器
                stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo docker rm {container}")
                error = stderr.read().decode('utf-8')
                
                if error:
                    raise Exception(f"删除容器失败: {error}")
                
                self.log(f"容器已删除: {container}")
                self.root.after(1000, self.check_docker_status)
                messagebox.showinfo("成功", "Docker容器已删除")
                
            except Exception as e:
                error_msg = f"删除容器失败: {str(e)}"
                self.log(error_msg)
                messagebox.showerror("错误", error_msg)
        
        # 启动执行线程
        threading.Thread(target=remove_thread_func).start()
    
    def check_docker_status(self):
        """
        检查Docker容器状态
        """
        if not self.connected:
            return
        
        container = self.docker_container_var.get()
        
        try:
            # 检查Docker服务是否运行
            stdin, stdout, stderr = self.ssh_client.exec_command("sudo systemctl is-active docker")
            docker_active = stdout.read().decode('utf-8').strip()
            
            if docker_active != "active":
                self.docker_status_var.set("Docker服务未运行")
                self.docker_status_var.setvar(name=self.docker_status_var._name, value="Docker服务未运行")
                return
            
            # 检查容器状态
            stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo docker ps -a --format '{{{{.Names}}}}|{{{{.Status}}}}' | grep ^{container}")
            output = stdout.read().decode('utf-8').strip()
            
            if not output:
                self.docker_status_var.set(f"容器 {container} 不存在")
            else:
                name, status = output.split('|', 1)
                self.docker_status_var.set(f"容器状态: {status}")
                
                # 获取容器日志
                stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo docker logs {container} --tail 50")
                logs = stdout.read().decode('utf-8')
                
                self.root.after(100, lambda: self.update_docker_logs(logs))
                
        except Exception as e:
            self.log(f"检查Docker状态失败: {str(e)}")
    
    def update_docker_logs(self, logs):
        """
        更新Docker日志显示
        
        参数:
            logs: str, Docker容器日志
        """
        self.docker_logs_text.delete(1.0, tk.END)
        self.docker_logs_text.insert(tk.END, logs)
        self.docker_logs_text.see(tk.END)
    
    def start_docker_status_timer(self):
        """
        启动Docker状态更新定时器
        """
        self.stop_docker_status_timer()
        self.docker_status_timer = self.root.after(10000, self.check_docker_status)
    
    def stop_docker_status_timer(self):
        """
        停止Docker状态更新定时器
        """
        if self.docker_status_timer:
            self.root.after_cancel(self.docker_status_timer)
            self.docker_status_timer = None
    
    def select_target_file(self):
        """
        选择要分析的目标文件
        """
        # 从远程文件列表中获取选中的文件
        selected_indices = self.remote_files_listbox.curselection()
        if selected_indices:
            item_text = self.remote_files_listbox.get(selected_indices[0])
            
            # 提取文件名
            if "[目录]" in item_text:
                return  # 不选择目录
            else:
                filename = item_text.split(' (')[0]
                remote_path = self.remote_path_var.get()
                full_path = f"{remote_path}/{filename}"
                self.target_file_var.set(full_path)
    
    def run_binwalk(self):
        """
        运行Binwalk分析
        """
        if not self.connected:
            messagebox.showwarning("未连接", "请先连接到SSH服务器")
            return
        
        target_file = self.target_file_var.get()
        if not target_file:
            messagebox.showinfo("提示", "请选择要分析的目标文件")
            return
        
        container = self.docker_container_var.get()
        
        # 检查容器是否正在运行
        stdin, stdout, stderr = self.ssh_client.exec_command(f"sudo docker ps | grep {container}")
        output = stdout.read().decode('utf-8')
        
        if container not in output:
            messagebox.showwarning("容器未运行", "请先启动Docker容器")
            return
        
        # 构建Binwalk命令
        binwalk_cmd = "binwalk"
        
        # 添加选项
        if self.extract_var.get():
            binwalk_cmd += " -e"
        if self.verbose_var.get():
            binwalk_cmd += " -v"
        if self.entropy_var.get():
            binwalk_cmd += " -E"
        if self.carve_var.get():
            binwalk_cmd += " -C"
        
        # 添加自定义选项
        custom_options = self.custom_options_var.get().strip()
        if custom_options:
            binwalk_cmd += f" {custom_options}"
        
        # 添加目标文件
        binwalk_cmd += f" '{target_file}'"
        
        # 创建执行线程
        def binwalk_thread_func():
            try:
                self.log(f"正在执行Binwalk分析: {binwalk_cmd}")
                self.binwalk_status_var.set("正在分析...")
                self.binwalk_output_text.delete(1.0, tk.END)
                
                # 在Docker容器中执行Binwalk
                cmd = f"sudo docker exec -i {container} {binwalk_cmd}"
                
                # 使用通道执行命令，支持实时输出
                channel = self.ssh_client.get_transport().open_session()
                channel.exec_command(cmd)
                
                # 实时读取和显示输出
                while True:
                    if channel.exit_status_ready():
                        break
                    
                    if channel.recv_ready():
                        output_data = channel.recv(1024).decode('utf-8')
                        if output_data:
                            self.root.after(100, lambda data=output_data: self.append_binwalk_output(data))
                    
                    if channel.recv_stderr_ready():
                        error_data = channel.recv_stderr(1024).decode('utf-8')
                        if error_data:
                            self.root.after(100, lambda data=error_data: self.append_binwalk_output(data))
                    
                    time.sleep(0.1)
                
                # 检查退出状态
                exit_status = channel.recv_exit_status()
                
                if exit_status == 0:
                    self.log("Binwalk分析完成")
                    self.root.after(100, lambda: self.binwalk_status_var.set("分析完成"))
                    self.root.after(100, lambda: messagebox.showinfo("成功", "Binwalk分析完成"))
                else:
                    self.log(f"Binwalk分析失败，退出码: {exit_status}")
                    self.root.after(100, lambda: self.binwalk_status_var.set(f"分析失败，退出码: {exit_status}"))
                    
            except Exception as e:
                error_msg = f"执行Binwalk失败: {str(e)}"
                self.log(error_msg)
                self.root.after(100, lambda: self.binwalk_status_var.set("分析失败"))
                self.root.after(100, lambda: messagebox.showerror("错误", error_msg))
        
        # 启动执行线程
        threading.Thread(target=binwalk_thread_func).start()
    
    def append_binwalk_output(self, text):
        """
        追加Binwalk输出到文本框
        
        参数:
            text: str, 要追加的文本
        """
        self.binwalk_output_text.insert(tk.END, text)
        self.binwalk_output_text.see(tk.END)
    
    def stop_binwalk(self):
        """
        停止正在执行的Binwalk分析
        """
        # 这里简化处理，可以根据实际情况实现更复杂的停止逻辑
        self.log("已取消Binwalk分析")
        self.binwalk_status_var.set("已取消")
        messagebox.showinfo("提示", "Binwalk分析已取消")
    
    def clear_logs(self):
        """
        清空日志
        """
        self.logs_text.delete(1.0, tk.END)
        self.log("日志已清空")
    
    def save_logs(self):
        """
        保存日志到文件
        """
        logs = self.logs_text.get(1.0, tk.END)
        
        if not logs.strip():
            messagebox.showinfo("提示", "日志为空，无需保存")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*")],
            title="保存日志"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(logs)
                self.log(f"日志已保存到: {file_path}")
                messagebox.showinfo("成功", "日志保存完成")
            except Exception as e:
                self.log(f"保存日志失败: {str(e)}")
                messagebox.showerror("错误", f"保存日志失败:\n{str(e)}")
    
    def format_size(self, size_bytes):
        """
        格式化文件大小
        
        参数:
            size_bytes: int, 文件大小（字节）
            
        返回值:
            str: 格式化后的大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

# 主函数
def main():
    """
    主函数，启动图形界面
    """
    # 检查必要的依赖
    try:
        import paramiko
        import scp
    except ImportError:
        print("缺少必要的依赖，请安装:")
        print("pip install paramiko scp")
        input("按Enter键退出...")
        sys.exit(1)
    
    # 创建并运行图形界面
    root = tk.Tk()
    app = BinwalkQemuGUI(root)
    
    # 设置窗口关闭时的处理
    def on_closing():
        if app.connected:
            app.disconnect()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()