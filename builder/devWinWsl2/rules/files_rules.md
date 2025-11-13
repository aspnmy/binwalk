# 文件路径记录

## 版本控制规则
- 使用**-${filename}-d${num+1}格式进行文本版本控制
- 首次编辑：**-${filename}-d1（基础版本）
- 不同业务方向：**-${filename}-d2、**-${filename}-d3等
- 关联功能扩展：使用temp-${filename}临时文件

## [生产代码]
true-install_wsl2.py
true-install-wsl2.py
true-install-wsl2-debug.py
true-binwalk_GUi.py
true-check_ip_location.py
true-checkTrueLocalHost

## [临时生成]
# 临时生成的文件，使用temp-前缀

## [测试代码]
# 测试文件，使用test-前缀或autotest--前缀
test_component_installation.py
test_component_menu.py
test_component_flow.py
test_import.py
test_ip_detection.py
test_logging.py
test_run_powershell.py