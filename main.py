"""
番茄小说下载器启动脚本 - 模块化重构版本
"""

import os
import sys
import traceback

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

def check_dependencies():
    """检查依赖"""
    missing_deps = []
    
    try:
        import customtkinter
        print("✅ customtkinter 已安装")
    except ImportError:
        missing_deps.append("customtkinter")
    
    try:
        import requests
        print("✅ requests 已安装")
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import packaging
        print("✅ packaging 已安装")
    except ImportError:
        missing_deps.append("packaging")
    
    if missing_deps:
        print("\n❌ 缺少以下依赖包:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print(f"\n请运行: pip install {' '.join(missing_deps)}")
        return False
    
    return True

def test_module_imports():
    """测试模块导入"""
    print("\n🧪 测试模块导入...")
    
    modules = [
        ("配置管理", "config.settings"),
        ("常量定义", "config.constants"),
        ("小说模型", "core.models.novel"),
        ("章节模型", "core.models.chapter"),
        ("下载器基类", "core.downloaders.base"),
        ("小说下载器", "core.downloaders.novel_downloader"),
        ("文件管理器", "core.storage.file_manager"),
        ("更新服务", "services.update_service"),
        ("日志服务", "services.logging_service"),
        ("文件工具", "utils.file_utils"),
        ("UI工具", "utils.ui_utils"),
        ("网络工具", "utils.network_utils"),
        ("格式转换", "utils.format_converter")
    ]
    
    success_count = 0
    for name, module in modules:
        try:
            __import__(module)
            print(f"  ✅ {name}")
            success_count += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
    
    print(f"\n📊 模块导入结果: {success_count}/{len(modules)} 成功")
    return success_count == len(modules)

def create_simple_gui():
    """创建简单的GUI界面"""
    try:
        import customtkinter as ctk
        
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 创建主窗口
        app = ctk.CTk()
        app.title("番茄小说下载器 v2.0 - 模块化重构版本")
        app.geometry("900x700")
        
        # 主框架
        main_frame = ctk.CTkFrame(app)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎉 番茄小说下载器 - 模块化重构版本",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # 重构信息
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        info_text = """
🏗️ 模块化重构完成！

✅ 新的架构特点：
• 分层架构设计 (核心层、服务层、UI层、工具层)
• 单一职责原则
• 松耦合设计
• 依赖注入
• 配置管理统一化
• 日志系统完善
• 错误处理优化

📁 新的目录结构：
src/
├── core/           # 核心业务逻辑
│   ├── models/     # 数据模型
│   ├── downloaders/# 下载器
│   └── storage/    # 存储管理
├── ui/             # 用户界面
│   └── components/ # UI组件
├── utils/          # 工具函数
├── config/         # 配置管理
└── services/       # 服务层

🔧 主要改进：
• 代码可维护性大幅提升
• 模块间依赖关系清晰
• 易于单元测试
• 支持功能扩展
• 配置管理更灵活
        """
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        info_label.pack(padx=20, pady=20)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        def test_functionality():
            """测试功能"""
            try:
                # 测试配置系统
                from config.settings import get_config, set_config
                config = get_config()
                
                # 测试数据模型
                from core.models.novel import Novel
                from core.models.chapter import Chapter
                
                novel = Novel(
                    book_id="test001",
                    title="测试小说",
                    author="测试作者"
                )
                
                chapter = Chapter(
                    chapter_id="ch001",
                    title="第一章",
                    content="测试内容"
                )
                
                novel.add_chapter(chapter)
                
                # 测试文件工具
                from utils.file_utils import sanitize_filename
                clean_name = sanitize_filename("测试<>文件名")
                
                result_text.configure(
                    text="✅ 功能测试通过！\n\n" +
                         f"• 配置系统正常\n" +
                         f"• 数据模型正常\n" +
                         f"• 小说: {novel.title} (作者: {novel.author})\n" +
                         f"• 章节数: {novel.total_chapters}\n" +
                         f"• 文件名清理: {clean_name}",
                    text_color="green"
                )
                
            except Exception as e:
                result_text.configure(
                    text=f"❌ 功能测试失败:\n{str(e)}",
                    text_color="red"
                )
        
        test_btn = ctk.CTkButton(
            button_frame,
            text="测试核心功能",
            command=test_functionality,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        test_btn.pack(side="left", padx=10, pady=10)
        
        def close_app():
            app.destroy()
        
        close_btn = ctk.CTkButton(
            button_frame,
            text="关闭",
            command=close_app,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        close_btn.pack(side="right", padx=10, pady=10)
        
        # 结果显示
        result_text = ctk.CTkLabel(
            main_frame,
            text="点击上方按钮测试核心功能",
            font=ctk.CTkFont(size=12),
            wraplength=800
        )
        result_text.pack(pady=10)
        
        # 居中显示
        app.update_idletasks()
        width = app.winfo_width()
        height = app.winfo_height()
        x = (app.winfo_screenwidth() // 2) - (width // 2)
        y = (app.winfo_screenheight() // 2) - (height // 2)
        app.geometry(f"{width}x{height}+{x}+{y}")
        
        print("🚀 GUI界面已启动！")
        app.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ GUI创建失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🍅 番茄小说下载器 v2.0 - 模块化重构版本")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        input("\n按Enter键退出...")
        return
    
    # 测试模块导入
    if not test_module_imports():
        print("\n⚠️ 部分模块导入失败，但仍可继续测试GUI")
    
    print("\n🚀 启动GUI界面...")
    
    # 创建GUI
    success = create_simple_gui()
    
    if success:
        print("✅ 程序正常退出")
    else:
        print("❌ 程序异常退出")
        input("按Enter键退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"\n💥 未捕获的异常: {e}")
        traceback.print_exc()
        input("按Enter键退出...")
