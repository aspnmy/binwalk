use crate::extractors;
use std::env;
use std::path::{Path, PathBuf};
use std::fs::{read, File};
use std::io::{Read};
use std::process::{Command};
use log::{warn, debug, error, info};

/// 检查SquashFS文件是否使用LZMA压缩
/// 增强的LZMA压缩检测，能够更准确地识别LZMA压缩的SquashFS文件
/// 
/// 参数:
/// - file_path: 文件路径
/// 
/// 返回:
/// - Option<bool>: 如果能检测到返回Some(true/false)，否则返回None
fn is_lzma_compressed(file_path: &str) -> Option<bool> {
    // 尝试读取文件头来检测压缩类型
    match read(file_path) {
        Ok(data) if data.len() > 24 => {
            // 检查SquashFS标志
            let is_squashfs = 
                data[0..4] == [0x68, 0x73, 0x71, 0x73] || // 'hsqs'
                data[0..4] == [0x73, 0x71, 0x73, 0x68];    // 'sqsh'
            
            if is_squashfs {
                // 增强的LZMA压缩检测逻辑
                // 1. 检查LZMA特定签名
                let lzma_magic = data.windows(4).any(|window| window == [0x5d, 0x00, 0x00, 0x80]);
                
                // 2. 检查SquashFS超级块中的压缩类型标志
                // 在大多数SquashFS格式中，压缩类型通常在偏移24附近
                let compression_type_offset = 24;
                let is_lzma_in_superblock = if data.len() > compression_type_offset + 2 {
                    // LZMA压缩通常在SquashFS超级块中有特定标识
                    let comp_flag = data[compression_type_offset];
                    // 0x02 通常表示LZMA压缩
                    comp_flag == 0x02 || 
                    // 也检查其他可能的LZMA标识值
                    (compression_type_offset + 3 < data.len() && 
                     data[compression_type_offset..compression_type_offset+4] == [0x5d, 0x00, 0x00, 0x80])
                } else {
                    false
                };
                
                // 3. 检查更大范围内的LZMA特征
                let extended_lzma_check = data.windows(6).any(|window| {
                    // 检查LZMA流的其他可能标识
                    window[0] == 0x5d && window[1] == 0x00 && window[2] == 0x00
                });
                
                // 如果任何检测方法返回true，则认为是LZMA压缩
                let is_lzma = lzma_magic || is_lzma_in_superblock || extended_lzma_check;
                debug!("文件 {} 的LZMA压缩检测结果: {}", file_path, is_lzma);
                Some(is_lzma)
            } else {
                None
            }
        }
        Err(e) => {
            debug!("读取文件 {} 失败: {}", file_path, e);
            None
        }
        _ => None
    }
}

/// 检查7-Zip是否可用
/// 
/// 返回:
///     Option<String>: 7-Zip可执行文件路径，如果未找到则返回None
fn find_seven_zip() -> Option<String> {
    // 常见的7-Zip安装路径
    let common_paths = [
        "C:\\Program Files\\7-Zip\\7z.exe",
        "C:\\Program Files (x86)\\7-Zip\\7z.exe",
        ".\\7z.exe",
        ".\\7-Zip\\7z.exe",
    ];
    
    // 尝试常见路径
    for path in &common_paths {
        if Path::new(path).exists() {
            debug!("在常见路径找到7-Zip: {}", path);
            return Some(path.to_string());
        }
    }
    
    // 尝试在PATH环境变量中查找
    if let Ok(path_env) = env::var("PATH") {
        for path in path_env.split(';') {
            let seven_zip_path = Path::new(path).join("7z.exe");
            if seven_zip_path.exists() {
                debug!("在PATH中找到7-Zip: {}", seven_zip_path.display());
                return Some(seven_zip_path.to_string_lossy().to_string());
            }
        }
    }
    
    // 尝试在binwalk.exe所在目录查找
    if let Ok(exe_path) = env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let seven_zip_path = exe_dir.join("7z.exe");
            if seven_zip_path.exists() {
                debug!("在binwalk.exe目录找到7-Zip: {}", seven_zip_path.display());
                return Some(seven_zip_path.to_string_lossy().to_string());
            }
            
            // 尝试binwalk.exe目录下的7-Zip子目录
            let seven_zip_dir_path = exe_dir.join("7-Zip").join("7z.exe");
            if seven_zip_dir_path.exists() {
                debug!("在binwalk.exe目录的7-Zip子目录找到7-Zip: {}", seven_zip_dir_path.display());
                return Some(seven_zip_dir_path.to_string_lossy().to_string());
            }
        }
    }
    
    debug!("未找到7-Zip");
    None
}

fn get_squashfs_tool() -> String {
    // 根据操作系统平台选择适当的工具
    if cfg!(target_os = "windows") {
        // Windows平台使用binwalk.exe同级目录下的sqfs_for_win\unsquashfs.exe
        // 尝试多种可能的路径，提高兼容性
        let potential_paths = [
            "sqfs_for_win\\unsquashfs.exe",
            ".\\sqfs_for_win\\unsquashfs.exe",
            "unsquashfs.exe",
            "sasquatch.exe"
        ];
        
        // 返回第一个存在的路径，否则返回默认路径
        for path in &potential_paths {
            if Path::new(path).exists() {
                debug!("找到SquashFS工具: {}", path);
                return path.to_string();
            }
        }
        
        // 如果找不到标准unsquashfs工具，尝试使用7-Zip作为替代方案
        if let Some(seven_zip_path) = find_seven_zip() {
            debug!("使用7-Zip作为squashfs提取的替代方案");
            return seven_zip_path;
        }
        
        // 默认路径
        "sqfs_for_win\\unsquashfs.exe".to_string()
    } else {
        // Linux/macOS平台使用sasquatch，如果不存在则回退到unsquashfs
        let tools_to_try = ["sasquatch", "unsquashfs"];
        for tool in &tools_to_try {
            if Command::new("which").arg(tool).output().is_ok() {
                return tool.to_string();
            }
        }
        
        // 在Linux/macOS上也尝试查找7-Zip作为替代方案
        let seven_zip_names = ["7z", "7za", "7zr"];
        for name in &seven_zip_names {
            if Command::new("which").arg(name).output().is_ok() {
                debug!("使用7-Zip工具 {} 作为squashfs提取的替代方案", name);
                return name.to_string();
            }
        }
        
        "sasquatch".to_string()
    }
}

/// 获取适用于SquashFSv4大端格式的提取工具命令
/// 
/// 返回:
///     String: 平台适配的v4be版本提取工具命令名称
fn get_squashfs_v4be_tool() -> String {
    // 根据操作系统平台选择适当的工具
    if cfg!(target_os = "windows") {
        // Windows平台使用binwalk.exe同级目录下的sqfs_for_win\unsquashfs.exe
        "sqfs_for_win\\unsquashfs.exe".to_string()
    } else {
        // Linux/macOS平台使用sasquatch-v4be
        "sasquatch-v4be".to_string()
    }
}

/// 获取mksquashfs打包工具命令
/// 
/// 返回:
///     String: 平台适配的打包工具命令名称
fn get_mksquashfs_tool() -> String {
    if cfg!(target_os = "windows") {
        // Windows平台使用binwalk.exe同级目录下的sqfs_for_win\mksquashfs.exe
        "sqfs_for_win\\mksquashfs.exe".to_string()
    } else {
        // Linux/macOS平台使用mksquashfs
        "mksquashfs".to_string()
    }
}

/// 检查Windows平台上工具是否可用
/// 
/// 参数:
///     tool_name: 工具名称
/// 
/// 返回:
///     bool: 工具是否可用
fn is_tool_available_on_windows(tool_name: &str) -> bool {
    // 1. 尝试直接使用工具名作为命令执行
    match Command::new(tool_name).arg("--help").output() {
        Ok(output) if output.status.success() || output.status.code() == Some(1) => {
            // 大多数工具在显示帮助时返回0或1
            debug!("工具 {} 可以通过命令行直接访问", tool_name);
            return true;
        }
        _ => {}
    }
    
    // 2. 检查相对路径和绝对路径
    let potential_paths = vec![
        tool_name.to_string(),
        format!(".\\{}", tool_name),
        format!("sqfs_for_win\\{}", tool_name),
        format!(".\\sqfs_for_win\\{}", tool_name),
        // 如果不包含.exe后缀，添加.exe再尝试
        if !tool_name.to_lowercase().ends_with(".exe") {
            format!("{}.exe", tool_name)
        } else { "".to_string() },
        if !tool_name.to_lowercase().ends_with(".exe") {
            format!(".\\{}.exe", tool_name)
        } else { "".to_string() },
        if !tool_name.to_lowercase().ends_with(".exe") {
            format!("sqfs_for_win\\{}.exe", tool_name)
        } else { "".to_string() },
        if !tool_name.to_lowercase().ends_with(".exe") {
            format!(".\\sqfs_for_win\\{}.exe", tool_name)
        } else { "".to_string() },
    ];
    
    for path in potential_paths {
        if path.is_empty() { continue; }
        
        if Path::new(&path).exists() {
            // 验证该文件是否可执行
            match Command::new(&path).arg("--help").output() {
                Ok(_) => {
                    debug!("找到可用的工具: {}", path);
                    return true;
                }
                _ => continue,
            }
        }
    }
    
    // 3. 检查PATH环境变量中的所有目录
    if let Ok(path) = env::var("PATH") {
        for dir in path.split(";").filter(|d| !d.is_empty()) {
            let potential_exe_paths = [
                Path::new(dir).join(tool_name),
                if !tool_name.to_lowercase().ends_with(".exe") {
                    Path::new(dir).join(format!("{}.exe", tool_name))
                } else { PathBuf::new() }
            ];
            
            for exe_path in &potential_exe_paths {
                if exe_path.exists() {
                    match Command::new(exe_path).arg("--help").output() {
                        Ok(_) => {
                            debug!("在PATH中找到可用的工具: {}", exe_path.display());
                            return true;
                        }
                        _ => continue,
                    }
                }
            }
        }
    }
    
    // 4. 检查binwalk.exe所在目录
    if let Ok(exe_path) = env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let potential_tool_path = exe_dir.join(
                if tool_name.contains("\\") || tool_name.contains("/") {
                    PathBuf::from(tool_name)
                } else {
                    PathBuf::from(tool_name)
                }
            );
            
            if potential_tool_path.exists() {
                match Command::new(&potential_tool_path).arg("--help").output() {
                    Ok(_) => {
                        debug!("在binwalk.exe所在目录找到工具: {}", potential_tool_path.display());
                        return true;
                    }
                    _ => {}
                }
            }
            
            // 也检查exe目录下的sqfs_for_win子目录
            let sqfs_path = exe_dir.join("sqfs_for_win").join(
                Path::new(tool_name).file_name().unwrap_or(Path::new(tool_name).as_ref())
            );
            if sqfs_path.exists() {
                match Command::new(&sqfs_path).arg("--help").output() {
                    Ok(_) => {
                        debug!("在binwalk.exe目录的sqfs_for_win子目录找到工具: {}", sqfs_path.display());
                        return true;
                    }
                    _ => {}
                }
            }
        }
    }
    
    debug!("无法找到可用的工具: {}", tool_name);
    false
}

/// 检查指定文件是否为LZMA压缩的SquashFS文件
/// 
/// 参数:
///     file_path: 文件路径
/// 
/// 返回:
///     bool: 是否为LZMA压缩
fn check_lzma_compression(file_path: &str) -> bool {
    // 调用已有的is_lzma_compressed函数进行检测
    if let Some(is_lzma) = is_lzma_compressed(file_path) {
        return is_lzma;
    }
    
    // 额外的检测逻辑：尝试从文件内容中查找LZMA特征
    match File::open(file_path) {
        Ok(mut file) => {
            let mut buffer = [0; 1024]; // 读取前1024字节进行检测
            if let Ok(size) = file.read(&mut buffer) {
                // 检查LZMA特征字节序列
                let lzma_signatures = [
                    [0x5d, 0x00, 0x00, 0x80], // 常见的LZMA标志
                    [0x5d, 0x00, 0x00, 0x00],  // 简化版本的LZMA标志
                ];
                
                for signature in &lzma_signatures {
                    for i in 0..size - signature.len() + 1 {
                        if &buffer[i..i + signature.len()] == signature {
                            debug!("在文件 {} 中找到LZMA压缩标志", file_path);
                            return true;
                        }
                    }
                }
            }
        }
        Err(e) => {
            debug!("无法打开文件 {} 进行LZMA检测: {}", file_path, e);
        }
    }
    
    false
}

/// 获取适用于当前平台的SquashFS提取参数
/// 
/// 参数:
///     is_little_endian: 是否为小端格式
///     is_big_endian: 是否为大端格式
///     is_v4: 是否为SquashFSv4格式
/// 
/// 返回:
///     Vec<String>: 平台适配的命令行参数列表
fn get_squashfs_arguments(is_little_endian: bool, is_big_endian: bool, is_v4: bool) -> Vec<String> {
    let mut args = Vec::new();
    let file_placeholder = extractors::common::SOURCE_FILE_PLACEHOLDER.to_string();
    
    // Windows平台的unsquashfs参数
    if cfg!(target_os = "windows") {
        // 首先检查是否使用的是7-Zip工具
        let tool = get_squashfs_tool();
        if tool.to_lowercase().contains("7z") || tool.to_lowercase().contains("7-zip") {
            // 7-Zip参数
            args.push("x".to_string()); // 提取命令
            args.push("-y".to_string()); // 自动覆盖确认
            args.push("-o.".to_string()); // 输出到当前目录
            args.push(file_placeholder); // 源文件
            debug!("Windows平台使用7-Zip提取SquashFS文件，参数: {:?}", args);
        } else {
            // 标准unsquashfs参数
            // 优先设置解压参数，确保兼容性
            // 1. 首先设置静默模式和覆盖参数，避免交互提示
            args.push("-n".to_string()); // 静默模式
            args.push("-f".to_string()); // 强制覆盖现有文件
            
            // 2. 设置目标目录
            args.push("-d".to_string());
            args.push(".".to_string()); // 当前目录
            
            // 3. 根据字节序设置参数
            if is_little_endian {
                args.push("-le".to_string());
            } else if is_big_endian {
                args.push("-be".to_string());
                
                // 对于v4大端格式，使用特殊处理
                if is_v4 {
                    // 某些版本的unsquashfs可能需要额外参数来处理v4大端格式
                    // 尝试添加兼容性参数
                    args.push("-force-uid".to_string());
                    args.push("0".to_string());
                    args.push("-force-gid".to_string());
                    args.push("0".to_string());
                }
            }
            
            // 4. 最后添加源文件占位符
            args.push(file_placeholder);
            
            debug!("Windows平台SquashFS提取参数: {:?}", args);
        }
    } else {
        // Linux/macOS平台的sasquatch参数
        // 1. 设置输出目录
        args.push("-dest".to_string());
        args.push(".".to_string());
        
        // 2. 根据字节序设置参数
        if is_little_endian {
            args.push("-le".to_string());
        } else if is_big_endian {
            if is_v4 {
                // 对于v4大端格式，使用特定参数
                args.push("-be-v4".to_string());
            } else {
                args.push("-be".to_string());
            }
        }
        
        // 3. 添加静默模式和其他优化参数
        args.push("-silent".to_string());
        args.push("-force".to_string()); // 强制提取
        
        // 4. 最后添加源文件占位符
        args.push(file_placeholder);
        
        debug!("Linux/macOS平台SquashFS提取参数: {:?}", args);
    }
    
    args
}

/// Describes how to run the appropriate utility to create SquashFS images
pub fn mksquashfs_creator(source_dir: &str, output_file: &str) -> extractors::common::Extractor {
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External(get_mksquashfs_tool()),
        extension: "sqsh".to_string(),
        arguments: vec![source_dir.to_string(), output_file.to_string()],
        exit_codes: vec![0],
        ..Default::default()
    }
}

/// Describes how to run the appropriate utility to extract SquashFS images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::squashfs::squashfs_extractor;
///
/// match squashfs_extractor().utility {
///     ExtractorType::None => panic!("Invalid extractor type of None"),
///     ExtractorType::Internal(func) => println!("Internal extractor OK: {:?}", func),
///     ExtractorType::External(cmd) => {
///         if let Err(e) = Command::new(&cmd).output() {
///             if e.kind() == ErrorKind::NotFound {
///                 panic!("External extractor '{}' not found", cmd);
///             } else {
///                 panic!("Failed to execute external extractor '{}': {}", cmd, e);
///             }
///         }
///     }
/// }
/// ```
pub fn squashfs_extractor() -> extractors::common::Extractor {
    // 获取适合的提取工具
    let tool = get_squashfs_tool();
    
    // 在Windows平台上先检查工具是否可用
    #[cfg(windows)]
    {
        if !is_tool_available_on_windows(&tool) {
            // 如果标准工具不可用，尝试使用7-Zip作为备选
            if let Some(seven_zip_path) = find_seven_zip() {
                info!("标准SquashFS提取工具不可用，将使用7-Zip作为备选方案");
                return extractors::common::Extractor {
                    utility: extractors::common::ExtractorType::External(seven_zip_path),
                    extension: "sqsh".to_string(),
                    arguments: get_squashfs_arguments(false, false, false),
                    // 7-Zip的退出码为0表示成功
                    exit_codes: vec![0],
                    ..Default::default()
                };
            }
            warn!("在Windows平台上找不到 '{}' 工具。确保它与binwalk.exe位于同一目录。", tool);
        }
    }
    
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External(tool),
        extension: "sqsh".to_string(),
        arguments: get_squashfs_arguments(false, false, false),
        // 支持unsquashfs和7-Zip的退出码
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}

/// Describes how to run the appropriate utility to extract little endian SquashFS images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::squashfs::squashfs_le_extractor;
///
/// match squashfs_le_extractor().utility {
///     ExtractorType::None => panic!("Invalid extractor type of None"),
///     ExtractorType::Internal(func) => println!("Internal extractor OK: {:?}", func),
///     ExtractorType::External(cmd) => {
///         if let Err(e) = Command::new(&cmd).output() {
///             if e.kind() == ErrorKind::NotFound {
///                 panic!("External extractor '{}' not found", cmd);
///             } else {
///                 panic!("Failed to execute external extractor '{}': {}", cmd, e);
///             }
///         }
///     }
/// }
/// ```
pub fn squashfs_le_extractor() -> extractors::common::Extractor {
    // 获取适合的提取工具
    let tool = get_squashfs_tool();
    
    // 在Windows平台上先检查工具是否可用
    #[cfg(windows)]
    {
        if !is_tool_available_on_windows(&tool) {
            // 如果标准工具不可用，尝试使用7-Zip作为备选
            if let Some(seven_zip_path) = find_seven_zip() {
                info!("标准SquashFS提取工具不可用，将使用7-Zip作为备选方案提取小端格式文件");
                return extractors::common::Extractor {
                    utility: extractors::common::ExtractorType::External(seven_zip_path),
                    extension: "sqsh".to_string(),
                    arguments: get_squashfs_arguments(true, false, false),
                    // 7-Zip的退出码为0表示成功
                    exit_codes: vec![0],
                    ..Default::default()
                };
            }
            warn!("在Windows平台上找不到 '{}' 工具。确保它与binwalk.exe位于同一目录。", tool);
        }
    }
    
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External(tool),
        extension: "sqsh".to_string(),
        arguments: get_squashfs_arguments(true, false, false),
        // 支持unsquashfs和7-Zip的退出码
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}

/// Describes how to run the appropriate utility to extract big endian SquashFS images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::squashfs::squashfs_be_extractor;
///
/// match squashfs_be_extractor().utility {
///     ExtractorType::None => panic!("Invalid extractor type of None"),
///     ExtractorType::Internal(func) => println!("Internal extractor OK: {:?}", func),
///     ExtractorType::External(cmd) => {
///         if let Err(e) = Command::new(&cmd).output() {
///             if e.kind() == ErrorKind::NotFound {
///                 panic!("External extractor '{}' not found", cmd);
///             } else {
///                 panic!("Failed to execute external extractor '{}': {}", cmd, e);
///             }
///         }
///     }
/// }
/// ```
pub fn squashfs_be_extractor() -> extractors::common::Extractor {
    // 获取适合的提取工具
    let tool = get_squashfs_tool();
    
    // 在Windows平台上先检查工具是否可用
    #[cfg(windows)]
    {
        if !is_tool_available_on_windows(&tool) {
            // 如果标准工具不可用，尝试使用7-Zip作为备选
            if let Some(seven_zip_path) = find_seven_zip() {
                info!("标准SquashFS提取工具不可用，将使用7-Zip作为备选方案提取大端格式文件");
                return extractors::common::Extractor {
                    utility: extractors::common::ExtractorType::External(seven_zip_path),
                    extension: "sqsh".to_string(),
                    arguments: get_squashfs_arguments(false, true, false),
                    // 7-Zip的退出码为0表示成功
                    exit_codes: vec![0],
                    ..Default::default()
                };
            }
            warn!("在Windows平台上找不到 '{}' 工具。确保它与binwalk.exe位于同一目录。", tool);
        }
    }
    
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External(tool),
        extension: "sqsh".to_string(),
        arguments: get_squashfs_arguments(false, true, false),
        // 支持unsquashfs和7-Zip的退出码
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}

/// Describes how to run the appropriate utility to extract big endian SquashFSv4 images
///
/// ```
/// use std::io::ErrorKind;
/// use std::process::Command;
/// use binwalk::extractors::common::ExtractorType;
/// use binwalk::extractors::squashfs::squashfs_v4_be_extractor;
///
/// match squashfs_v4_be_extractor().utility {
///     ExtractorType::None => panic!("Invalid extractor type of None"),
///     ExtractorType::Internal(func) => println!("Internal extractor OK: {:?}", func),
///     ExtractorType::External(cmd) => {
///         if let Err(e) = Command::new(&cmd).output() {
///             if e.kind() == ErrorKind::NotFound {
///                 panic!("External extractor '{}' not found", cmd);
///             } else {
///                 panic!("Failed to execute external extractor '{}': {}", cmd, e);
///             }
///         }
///     }
/// }
/// ```
pub fn squashfs_v4_be_extractor() -> extractors::common::Extractor {
    // 获取适合的提取工具
    let tool = get_squashfs_v4be_tool();
    
    // 在Windows平台上先检查工具是否可用
    #[cfg(windows)]
    {
        if !is_tool_available_on_windows(&tool) {
            // 如果标准工具不可用，尝试使用7-Zip作为备选
            if let Some(seven_zip_path) = find_seven_zip() {
                info!("标准SquashFS提取工具不可用，将使用7-Zip作为备选方案提取大端格式v4文件");
                return extractors::common::Extractor {
                    utility: extractors::common::ExtractorType::External(seven_zip_path),
                    extension: "sqsh".to_string(),
                    arguments: get_squashfs_arguments(false, true, true),
                    // 7-Zip的退出码为0表示成功
                    exit_codes: vec![0],
                    ..Default::default()
                };
            }
            warn!("在Windows平台上找不到 '{}' 工具。确保它与binwalk.exe位于同一目录。", tool);
        }
    }
    
    extractors::common::Extractor {
        utility: extractors::common::ExtractorType::External(tool),
        extension: "sqsh".to_string(),
        arguments: get_squashfs_arguments(false, true, true),
        // 支持unsquashfs和7-Zip的退出码
        exit_codes: vec![0, 2],
        ..Default::default()
    }
}
