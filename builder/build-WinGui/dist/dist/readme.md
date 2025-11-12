# binwalk_for_Win_v3
适配在Win10/Win11中的Binwalk v3.x以上版本

## 版本说明
binwalk v3 rust重构版完美运行于linux环境，也可以docker部署，但是仍然有部分客户只会使用exe文件双击运行，故此重新适配编译了这个版本

## 文件说明
- readme.md 帮助文件
- binwalk.exe binwalk编译在win11的命令行工具  建议在pwsh下 输入 .\binwalk --help 获得使用方法
- binwalk_gui.exe  binwalk.exe程序WinGUI文件，双击执行即可，需要和binwalk.exe在同个目录下
- unsquashfs.exe 位于.\sqfs_for_win\sqfs_for_win.7z 压缩包中，是squashfs压缩独立解包组件，命令行执行，作为备用方案
- Tests 中是测试解包的Dlink的固件例子

## binwalk_for_Win_v3 可能遇到的几个问题

-  Extraction of squashfs data at offset 0x1174A4 failed! 报错
-  这个是由于squashfs-tools工具链在win系统下不理想造成的解压失败
-  所以我这个适配版本中使用的是外部工具包“sqfs_for_win”
-  使用的时候把sqfs_for_win.zip 解压缩到binwalk.exe同级目录下的sqfs_for_win路径下即可
  <img width="1092" height="507" alt="image" src="https://github.com/user-attachments/assets/210d13f3-9ce1-44fc-851f-8d2126fe646d" />
<img width="664" height="311" alt="image" src="https://github.com/user-attachments/assets/e8e62233-442c-44a8-b3e9-b28970aee28f" />


## binwalk_for_WinGUI的问题

- 考虑到部分用户只会双击exe 不会使用python脚本运行GUI交互界面，所以binwalk_gui.exe,使用pyinstaller进行编译后的独立exe GUI文件，使用binwalk_gui.exe的时候，需要和binwalk.exe在同级目录下，才能正确调用
  <img width="894" height="689" alt="image" src="https://github.com/user-attachments/assets/d71eae04-fe19-4e67-b076-9d3a52726f4a" />

- -c参数可以解非标准bin文件
  <img width="1026" height="689" alt="企业微信截图_17629278156167" src="https://github.com/user-attachments/assets/7da5c05a-42bd-4f22-a79c-17c4443574c3" />


## 路由器固件解包以后重新打包的问题

### 重新LZMA压缩编辑过的固件
- 这个比较简单所以没写GUI程序，mksquashfs也在sqfs_for_win\目录下
- 在cmd 下运行
 ``` bat
mksquashfs squashfs-root/ new_rootfs.bin -comp xz
# mksquashfs 输出的目录/  编辑过的bin文件路径 -comp xz
  ```
- 把自己修改过的bin文件重新进行LZMA压缩

### 使用DD工具重新和头文件固件合并 或者和原始固件合并
```
dd if=<原始固件> of=head.bin bs=1 count=<头部大小>
cat head.bin new_rootfs.bin > new_firmware.bin
```
- DD 也有Win对应工具 就简单跳过了

### 完成打包就可以去虚拟机运行固件 通过就可以烧录了  
  