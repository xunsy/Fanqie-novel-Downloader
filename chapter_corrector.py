"""
章节矫正模块

提供智能章节排序和矫正功能，能够：
1. 从各种格式的章节标题中提取章节号
2. 根据章节号对章节进行智能排序
3. 处理特殊章节类型（序章、番外、后记等）
4. 检测和修复章节顺序问题

支持的章节标题格式：
- 第1章、第一章、第001章
- Chapter 1、Ch.1、chapter 1
- 序章、楔子、番外、后记、终章等特殊章节
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ChapterType(Enum):
    """章节类型枚举"""
    PROLOGUE = "prologue"      # 序章、楔子、前言
    NORMAL = "normal"          # 正常章节
    EXTRA = "extra"           # 番外、特别篇
    EPILOGUE = "epilogue"     # 后记、终章、尾声
    UNKNOWN = "unknown"       # 未知类型


@dataclass
class ChapterInfo:
    """章节信息数据类"""
    original_index: int        # 原始索引
    chapter_id: str           # 章节ID
    original_title: str       # 原始标题
    extracted_number: Optional[int]  # 提取的章节号
    chapter_type: ChapterType # 章节类型
    special_weight: int       # 特殊章节权重
    sort_key: Tuple[int, int, int, int]  # 排序键 (类型优先级, 章节号/特殊权重, 原始索引, 特殊权重)
    

class ChapterNumberExtractor:
    """章节号提取器"""
    
    def __init__(self):
        # 中文数字映射
        self.chinese_numbers = {
            '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
            '十': 10, '百': 100, '千': 1000, '万': 10000,
            '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '拾': 10,
            '佰': 100, '仟': 1000, '萬': 10000
        }
        
        # 章节号提取正则表达式（按优先级排序）
        self.number_patterns = [
            # 阿拉伯数字：第123章、第001章
            (r'第\s*(\d+)\s*章', 1),
            # 中文数字：第一章、第二十三章
            (r'第\s*([一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+)\s*章', 1),
            # 英文：Chapter 123、Ch.123、chapter 123
            (r'(?:Chapter|Ch\.?|chapter)\s*(\d+)', 1),
            # 简单数字：123章、123话
            (r'(\d+)\s*[章话集]', 1),
            # 括号中的数字：(123)、【123】
            (r'[（(【]\s*(\d+)\s*[）)】]', 1),
        ]
        
        # 特殊章节类型识别（按优先级排序，更精确的模式在前）
        self.special_patterns = {
            ChapterType.PROLOGUE: [
                r'序章', r'楔子', r'前言', r'开篇', r'引子', r'序言', r'开场', r'起始',
                r'prologue', r'preface', r'introduction', r'opening'
            ],
            ChapterType.EXTRA: [
                r'番外', r'特别篇', r'外传', r'if线', r'特典', r'支线', r'分支', r'特别章',
                r'extra', r'special', r'side story', r'bonus', r'omake', r'gaiden'
            ],
            ChapterType.EPILOGUE: [
                r'后记', r'终章', r'尾声', r'结语', r'完结', r'结尾', r'终结', r'大结局',
                r'epilogue', r'finale', r'ending', r'conclusion', r'final'
            ]
        }

        # 特殊章节的排序权重（用于同类型章节内部排序）
        self.special_chapter_weights = {
            # 序章类型的权重
            '序章': 0, '楔子': 1, '前言': 2, '开篇': 3, '引子': 4,
            'prologue': 0, 'preface': 2, 'introduction': 3,

            # 番外类型的权重（通常按出现顺序）
            '番外': 100, '特别篇': 101, '外传': 102, 'if线': 103,
            'extra': 100, 'special': 101, 'side story': 102,

            # 后记类型的权重
            '后记': 200, '终章': 201, '尾声': 202, '结语': 203, '完结': 204,
            'epilogue': 200, 'finale': 201, 'ending': 202
        }
    
    def chinese_to_arabic(self, chinese_num: str) -> int:
        """将中文数字转换为阿拉伯数字"""
        try:
            # 处理简单的中文数字
            if chinese_num in self.chinese_numbers:
                return self.chinese_numbers[chinese_num]
            
            # 处理复合中文数字
            result = 0
            temp = 0
            
            for char in chinese_num:
                if char in self.chinese_numbers:
                    num = self.chinese_numbers[char]
                    if num >= 10:
                        if num >= 10000:
                            result += temp * num
                            temp = 0
                        elif num >= 100:
                            temp = temp * num if temp else num
                        else:  # num == 10
                            temp = temp * num if temp else num
                    else:
                        temp += num
            
            result += temp
            return result if result > 0 else temp
            
        except Exception:
            return None
    
    def extract_chapter_number(self, title: str) -> Optional[int]:
        """从章节标题中提取章节号"""
        if not title:
            return None
        
        title_clean = title.strip()
        
        # 尝试各种数字提取模式
        for pattern, group_idx in self.number_patterns:
            match = re.search(pattern, title_clean, re.IGNORECASE)
            if match:
                number_str = match.group(group_idx)
                
                # 尝试直接转换为整数（阿拉伯数字）
                try:
                    return int(number_str)
                except ValueError:
                    # 尝试中文数字转换
                    arabic_num = self.chinese_to_arabic(number_str)
                    if arabic_num is not None:
                        return arabic_num
        
        return None
    
    def detect_chapter_type(self, title: str) -> Tuple[ChapterType, int]:
        """
        检测章节类型和特殊章节权重

        Returns:
            (章节类型, 特殊章节权重)
        """
        if not title:
            return ChapterType.UNKNOWN, 0

        title_lower = title.lower().strip()

        # 检查特殊章节类型
        for chapter_type, patterns in self.special_patterns.items():
            for pattern in patterns:
                if re.search(pattern, title_lower, re.IGNORECASE):
                    # 计算特殊章节权重
                    weight = self.special_chapter_weights.get(pattern, 999)
                    return chapter_type, weight

        # 如果能提取到章节号，认为是正常章节
        if self.extract_chapter_number(title) is not None:
            return ChapterType.NORMAL, 0

        return ChapterType.UNKNOWN, 0


class ChapterCorrector:
    """章节矫正器"""
    
    def __init__(self):
        self.extractor = ChapterNumberExtractor()
        
        # 章节类型排序优先级
        self.type_priority = {
            ChapterType.PROLOGUE: 0,   # 序章最前
            ChapterType.NORMAL: 1,     # 正常章节
            ChapterType.EXTRA: 2,      # 番外
            ChapterType.EPILOGUE: 3,   # 后记最后
            ChapterType.UNKNOWN: 4     # 未知类型最后
        }
    
    def analyze_chapters(self, chapters: List[Dict[str, Any]]) -> List[ChapterInfo]:
        """分析章节列表，提取章节信息"""
        chapter_infos = []

        for i, chapter in enumerate(chapters):
            title = chapter.get('title', '')
            chapter_id = chapter.get('id', '')

            # 提取章节号和类型
            chapter_number = self.extractor.extract_chapter_number(title)
            chapter_type, special_weight = self.extractor.detect_chapter_type(title)

            # 生成排序键
            type_priority = self.type_priority.get(chapter_type, 999)

            # 对于不同类型的章节使用不同的排序逻辑
            if chapter_type == ChapterType.NORMAL:
                # 正常章节按章节号排序
                number_for_sort = chapter_number if chapter_number is not None else 999999
                sort_key = (type_priority, number_for_sort, i, 0)
            else:
                # 特殊章节按特殊权重排序
                sort_key = (type_priority, special_weight, i, special_weight)

            chapter_info = ChapterInfo(
                original_index=i,
                chapter_id=chapter_id,
                original_title=title,
                extracted_number=chapter_number,
                chapter_type=chapter_type,
                special_weight=special_weight,
                sort_key=sort_key
            )

            chapter_infos.append(chapter_info)

        return chapter_infos
    
    def detect_order_issues(self, chapter_infos: List[ChapterInfo]) -> List[str]:
        """检测章节顺序问题"""
        issues = []
        
        # 分离正常章节
        normal_chapters = [info for info in chapter_infos if info.chapter_type == ChapterType.NORMAL]
        
        if not normal_chapters:
            return issues
        
        # 检查章节号连续性
        chapter_numbers = [info.extracted_number for info in normal_chapters if info.extracted_number is not None]
        
        if chapter_numbers:
            chapter_numbers.sort()
            
            # 检查是否有重复章节号
            duplicates = []
            seen = set()
            for num in chapter_numbers:
                if num in seen:
                    duplicates.append(num)
                seen.add(num)
            
            if duplicates:
                issues.append(f"发现重复章节号: {duplicates}")
            
            # 检查章节号连续性
            if len(chapter_numbers) > 1:
                gaps = []
                for i in range(len(chapter_numbers) - 1):
                    if chapter_numbers[i + 1] - chapter_numbers[i] > 1:
                        gaps.append((chapter_numbers[i], chapter_numbers[i + 1]))
                
                if gaps:
                    gap_strs = [f"{start}-{end}" for start, end in gaps]
                    issues.append(f"发现章节号跳跃: {gap_strs}")
        
        # 检查是否需要重新排序
        original_order = [info.original_index for info in chapter_infos]
        sorted_infos = sorted(chapter_infos, key=lambda x: x.sort_key)
        sorted_order = [info.original_index for info in sorted_infos]
        
        if original_order != sorted_order:
            issues.append("章节顺序需要调整")
        
        return issues
    
    def correct_chapter_order(self, chapters: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """矫正章节顺序"""
        if not chapters:
            return chapters, []
        
        # 分析章节
        chapter_infos = self.analyze_chapters(chapters)
        
        # 检测问题
        issues = self.detect_order_issues(chapter_infos)
        
        # 按排序键排序
        sorted_infos = sorted(chapter_infos, key=lambda x: x.sort_key)
        
        # 重新构建章节列表
        corrected_chapters = []
        for info in sorted_infos:
            original_chapter = chapters[info.original_index]
            corrected_chapters.append(original_chapter)
        
        return corrected_chapters, issues


# 全局章节矫正器实例
chapter_corrector = ChapterCorrector()


def correct_chapters(chapters: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    矫正章节顺序的便捷函数
    
    Args:
        chapters: 章节列表
        
    Returns:
        (矫正后的章节列表, 发现的问题列表)
    """
    return chapter_corrector.correct_chapter_order(chapters)


def analyze_chapter_title(title: str) -> Dict[str, Any]:
    """
    分析单个章节标题的便捷函数

    Args:
        title: 章节标题

    Returns:
        包含分析结果的字典
    """
    extractor = ChapterNumberExtractor()
    chapter_type, special_weight = extractor.detect_chapter_type(title)

    return {
        'title': title,
        'chapter_number': extractor.extract_chapter_number(title),
        'chapter_type': chapter_type.value,
        'special_weight': special_weight,
        'is_special': chapter_type != ChapterType.NORMAL
    }


if __name__ == "__main__":
    # 测试代码
    test_titles = [
        "第1章 开始的地方",
        "第二章 新的冒险", 
        "序章",
        "Chapter 5 The Journey",
        "番外：如果线",
        "第001章 特殊格式",
        "后记",
        "第十五章 中文数字"
    ]
    
    print("=== 章节标题分析测试 ===")
    for title in test_titles:
        result = analyze_chapter_title(title)
        print(f"{title} -> 章节号: {result['chapter_number']}, 类型: {result['chapter_type']}")
