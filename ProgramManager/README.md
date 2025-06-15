# AutoTradingBinance 项目管理器 Shell 界面

## 🎯 概述

AutoTradingBinance 项目管理器是一个专业的交互式命令行工具，提供了完整的项目管理、安全配置、系统监控等功能。

## 🚀 快速启动

### 方法 1: 使用启动脚本
```bash
./start_shell.sh
```

### 方法 2: 直接运行 Python 脚本
```bash
python3 ProgramManager/shell.py
```

### 方法 3: 使用根目录管理脚本
```bash
python3 manage.py
```

## 🔧 主要功能

### 1. 项目设置 (`setup`)
- 完整的环境设置
- 依赖安装
- 权限配置
- 安全检查

### 2. 依赖管理 (`deps`)
- 安装Python依赖
- 更新过期包
- 检查依赖状态

### 3. 安全管理 (`security`)
- 系统安全检查
- 文件权限设置
- 环境变量验证

### 4. 密钥管理 (`keys`)
- 密钥状态检查
- 自动密钥轮换
- 密钥生成

### 5. 服务器管理 (`server`)
- 启动/停止 FastAPI 服务器
- 服务器状态监控
- 服务器重启

### 6. 系统监控 (`monitor`)
- CPU/内存/磁盘使用率
- 进程监控
- 实时系统状态

### 7. 项目状态 (`status`)
- 完整项目状态概览
- 组件健康检查

### 8. 日志查看 (`logs`)
- 系统日志查看
- 错误日志分析

## 🎨 界面特性

### 彩色输出
- 🟢 绿色：成功操作
- 🟡 黄色：警告信息
- 🔴 红色：错误信息
- 🔵 蓝色：信息提示
- 🟣 紫色：特殊功能

### 交互式菜单
- 数字选择 (1-8)
- 命令别名 (setup, deps, security, etc.)
- 快捷命令 (help, clear, history, exit)

### 命令历史
- 自动记录执行的命令
- 时间戳标记
- 历史命令查看

## 📋 使用示例

### 基本使用流程

1. **首次设置**
   ```
   [AutoTrading]➤ setup
   ```

2. **检查项目状态**
   ```
   [AutoTrading]➤ status
   ```

3. **启动服务器**
   ```
   [AutoTrading]➤ server
   ```

4. **监控系统**
   ```
   [AutoTrading]➤ monitor
   ```

### 高级功能

1. **密钥轮换**
   ```
   [AutoTrading]➤ keys
   选择: 2 (轮换密钥)
   ```

2. **安全检查**
   ```
   [AutoTrading]➤ security
   选择: 1 (安全检查)
   ```

3. **依赖更新**
   ```
   [AutoTrading]➤ deps
   选择: 2 (更新依赖)
   ```

## 🔧 快捷命令

| 命令 | 功能 |
|------|------|
| `help` / `h` / `?` | 显示帮助菜单 |
| `clear` / `cls` | 清屏 |
| `history` | 显示命令历史 |
| `exit` / `quit` / `q` | 退出程序 |

## 🛡️ 安全特性

- 密钥操作需要确认
- 文件权限自动设置
- 安全检查自动化
- 进程监控和管理

## 📁 文件结构

```
AutoTradingBinance/
├── ProgramManager/          # 🔧 项目管理工具
│   ├── shell.py            # 交互式 Shell 界面
│   ├── manage.py           # 命令行管理工具  
│   ├── setup.py            # 项目设置
│   └── *.sh                # Shell 脚本
├── start_shell.sh          # 快速启动脚本
├── manage.py               # 根目录启动入口
└── ...
```

## 🐛 故障排除

### 常见问题

1. **Python 环境问题**
   - 确保安装了 Python 3.8+
   - 检查虚拟环境是否激活

2. **权限问题**
   - 运行权限设置：`chmod +x start_shell.sh`
   - 密钥文件权限自动管理

3. **依赖问题**
   - 运行依赖安装：在 shell 中选择 `deps` → `1`
   - 更新过期依赖：在 shell 中选择 `deps` → `2`

### 日志调试

使用 shell 界面的日志查看功能：
```
[AutoTrading]➤ logs
```

## 🔄 更新和维护

Shell 界面会自动检查项目状态并提供维护建议。定期运行：

1. `status` - 检查项目健康状态
2. `security` - 运行安全检查
3. `deps` - 更新依赖包
4. `keys` - 检查密钥状态

---

## 💡 提示

- 使用 Tab 键可以在某些系统上自动补全
- 输入错误命令时会显示建议
- 支持 Ctrl+C 安全退出
- 所有操作都有详细的状态反馈

享受使用 AutoTradingBinance 项目管理器！🚀
