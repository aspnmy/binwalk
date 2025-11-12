fn main() {
    // 测试不同宽度场景下的行为
    let widths = [0, 5, 10, 20, 100];
    let prefix_sizes = [0, 5, 15, 25, 100];
    
    for &width in &widths {
        println!("模拟终端宽度: {}", width);
        for &prefix in &prefix_sizes {
            // 模拟terminal_width返回值
            let result = if width >= prefix {
                width - prefix
            } else {
                0
            };
            println!("  前缀大小 {} -> 计算结果: {}", prefix, result);
            // 测试saturating_sub
            let safe_result = width.saturating_sub(prefix).max(10);
            println!("  安全计算结果: {}", safe_result);
        }
    }
}