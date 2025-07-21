import re
import sys
import os
from pathlib import Path
from datetime import datetime

def reorder_file(file_path: Path, verbose=True):
    """
    重新排序小说章节

    Args:
        file_path: 文件路径
        verbose: 是否输出详细信息

    Returns:
        bool: 是否成功处理
    """
    try:
        if verbose:
            print(f'📖 正在处理: {file_path.name}')

        text = file_path.read_text(encoding='utf-8')
        lines = text.splitlines()
        header = []
        chapters = []
        current = None

        # 解析文件内容
        for line_num, line in enumerate(lines, 1):
            # 匹配章节标题：## 第X章 标题
            m = re.match(r'##\s*第(\d+)章\s*(.*)', line.strip())
            if m:
                # 保存上一章节
                if current:
                    chapters.append(current)

                num = int(m.group(1))
                title = m.group(2).strip()
                current = {
                    'num': num,
                    'title': title,
                    'content': [],
                    'original_line': line_num
                }
                if verbose and len(chapters) < 5:  # 只显示前5章的信息
                    print(f'  📄 发现章节: 第{num}章 {title}')
            else:
                # 章节内容或文件头部
                if current:
                    current['content'].append(line)
                else:
                    header.append(line)

        # 添加最后一章
        if current:
            chapters.append(current)

        if not chapters:
            if verbose:
                print(f'  ⚠️  未找到任何章节，跳过处理')
            return False

        # 检查是否需要重排序
        original_order = [ch['num'] for ch in chapters]
        sorted_order = sorted(original_order)

        if original_order == sorted_order:
            if verbose:
                print(f'  ✅ 章节顺序正确，无需调整 (共{len(chapters)}章)')
            return True

        if verbose:
            print(f'  🔄 检测到章节顺序错乱，正在重新排序...')
            print(f'  📊 原顺序: {original_order[:10]}{"..." if len(original_order) > 10 else ""}')
            print(f'  📊 新顺序: {sorted_order[:10]}{"..." if len(sorted_order) > 10 else ""}')

        # 按章节号排序
        chapters.sort(key=lambda x: x['num'])

        # 创建备份
        backup_path = file_path.with_suffix('.bak')
        if not backup_path.exists():
            file_path.rename(backup_path)
            if verbose:
                print(f'  💾 已创建备份: {backup_path.name}')

        # 写回文件
        with file_path.open('w', encoding='utf-8') as f:
            # 写入文件头部
            for hl in header:
                f.write(hl + '\n')

            # 写入排序后的章节
            for i, chap in enumerate(chapters):
                # 章节之间添加适当的空行
                if i > 0 or header:
                    f.write('\n')

                # 写入章节标题（修复格式问题）
                f.write(f"## 第{chap['num']}章 {chap['title']}\n")

                # 写入章节内容
                for cl in chap['content']:
                    f.write(cl + '\n')

        if verbose:
            print(f'  ✅ 章节排序完成！共处理 {len(chapters)} 章')

        return True

    except Exception as e:
        if verbose:
            print(f'  ❌ 处理失败: {str(e)}')
        return False

def auto_fix_current_directory(verbose=True):
    """
    自动修复当前目录下所有小说文件的章节顺序
    """
    current_dir = Path('.')
    txt_files = list(current_dir.glob('*.txt'))

    if not txt_files:
        if verbose:
            print('📁 当前目录下没有找到 .txt 文件')
        return

    if verbose:
        print(f'🔍 在当前目录找到 {len(txt_files)} 个文本文件')
        print(f'⏰ 开始时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('-' * 50)

    success_count = 0
    for txt_file in sorted(txt_files):
        if reorder_file(txt_file, verbose):
            success_count += 1
        if verbose:
            print()  # 添加空行分隔

    if verbose:
        print('-' * 50)
        print(f'🎉 处理完成！成功处理 {success_count}/{len(txt_files)} 个文件')
        print(f'⏰ 结束时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

def main():
    if len(sys.argv) < 2:
        print('📚 小说章节自动排序工具')
        print()
        print('用法:')
        print('  python fix_chapter_order.py <文件或目录路径> [更多路径...]')
        print('  python fix_chapter_order.py --auto    # 自动处理当前目录')
        print()
        print('示例:')
        print('  python fix_chapter_order.py novel.txt')
        print('  python fix_chapter_order.py ./novels/')
        print('  python fix_chapter_order.py --auto')
        sys.exit(1)

    # 自动模式
    if sys.argv[1] == '--auto':
        auto_fix_current_directory()
        return

    # 手动指定路径模式
    for p in sys.argv[1:]:
        path = Path(p)
        if path.is_dir():
            print(f'📁 处理目录: {path}')
            txt_files = list(path.glob('*.txt'))
            if not txt_files:
                print(f'  ⚠️  目录中没有找到 .txt 文件')
                continue

            for txt in sorted(txt_files):
                reorder_file(txt)
                print()  # 添加空行分隔
        elif path.is_file():
            reorder_file(path)
        else:
            print(f'❌ 路径不存在: {path}')

if __name__ == '__main__':
    main()
