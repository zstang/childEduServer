"""
隐私检查器测试模块

这个模块包含了对隐私检查器的测试用例，包括：
1. 安全问题检查
2. 隐私信息检查
3. 政治敏感内容检查
4. 公众人物相关内容检查
5. 错误处理测试
"""

import unittest
from unittest.mock import Mock, patch
from modules.privacy_checker import PrivacyChecker, PrivacyCheckResult
from modules.exceptions import ValidationError


class TestPrivacyChecker(unittest.TestCase):
    """测试隐私检查器"""
    
    def setUp(self):
        """测试准备"""
        self.checker = PrivacyChecker()
        
    def test_safe_question(self):
        """测试安全问题检查"""
        test_cases = [
            {
                "question": "我最近工作压力很大，经常失眠，该怎么办？",
                "description": "普通心理咨询问题"
            },
            {
                "question": "我的孩子最近学习成绩下降，很焦虑",
                "description": "使用关系称谓的问题"
            },
            {
                "question": "我和同事之间的沟通出现了问题",
                "description": "使用角色称谓的问题"
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                result = self.checker.check_privacy(case["question"])
                self.assertTrue(result.is_safe)
                self.assertEqual(result.risk_level, "low")

    def test_privacy_violation(self):
        """测试隐私信息检查"""
        test_cases = [
            {
                "question": "张三和李四经常在办公室吵架",
                "description": "包含真实姓名"
            },
            {
                "question": "王老师对我的成绩很不满意",
                "description": "包含教师真实姓名"
            },
            {
                "question": "我的同学小明最近很不开心",
                "description": "包含同学真实姓名"
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                result = self.checker.check_privacy(case["question"])
                self.assertFalse(result.is_safe)
                self.assertTrue(result.has_real_names)
                self.assertEqual(result.risk_level, "high")

    def test_political_content(self):
        """测试政治敏感内容检查"""
        test_cases = [
            {
                "question": "我对最近的政府政策很不满",
                "description": "涉及政府政策"
            },
            {
                "question": "我想谈谈对某个政党的看法",
                "description": "涉及政党"
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                result = self.checker.check_privacy(case["question"])
                self.assertFalse(result.is_safe)
                self.assertTrue(result.has_modern_political)
                self.assertEqual(result.risk_level, "high")
                self.assertTrue(result.rejection_required)

    def test_public_figure_content(self):
        """测试公众人物相关内容检查"""
        test_cases = [
            {
                "question": "我觉得周杰伦的音乐很有启发性",
                "description": "涉及艺人"
            },
            {
                "question": "我很崇拜马云，想成为像他一样的人",
                "description": "涉及企业家"
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                result = self.checker.check_privacy(case["question"])
                self.assertTrue(result.is_safe)
                self.assertTrue(result.has_public_figure)
                self.assertEqual(result.figure_category, "public")

    def test_error_handling(self):
        """测试错误处理"""
        with patch('modules.privacy_checker.PrivacyChecker._extract_json_from_markdown') as mock_extract:
            mock_extract.side_effect = Exception("Invalid JSON")
            with self.assertRaises(ValidationError):
                self.checker.check_privacy("测试问题")


class TestPrivacyCheckerNew(unittest.TestCase):
    def setUp(self):
        self.privacy_checker = PrivacyChecker()

    def test_safe_question(self):
        """测试安全的问题"""
        question = "如何做一道番茄炒蛋？"
        result = self.privacy_checker.check_privacy(question)
        self.assertTrue(result.is_safe)
        self.assertEqual(result.risk_level, "low")
        self.assertFalse(result.rejection_required)

    def test_modern_political_figure(self):
        """测试涉及近现代政治人物的问题"""
        question = "请问你觉得某某领导人怎么样？"
        result = self.privacy_checker.check_privacy(question)
        self.assertFalse(result.is_safe)
        self.assertTrue(result.has_modern_political)
        self.assertEqual(result.figure_category, "modern_political")
        self.assertEqual(result.risk_level, "high")
        self.assertTrue(result.rejection_required)

    def test_historical_figure(self):
        """测试涉及历史人物的问题"""
        question = "你觉得诸葛亮是一个什么样的人？"
        result = self.privacy_checker.check_privacy(question)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.has_historical_figure)
        self.assertEqual(result.figure_category, "historical")
        self.assertEqual(result.risk_level, "medium")
        self.assertFalse(result.rejection_required)

    def test_public_figure_negative(self):
        """测试涉及公众人物的负面评价"""
        question = "我觉得某某明星最近的行为很让人失望"
        result = self.privacy_checker.check_privacy(question)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.has_public_figure)
        self.assertEqual(result.figure_category, "public")
        self.assertEqual(result.user_emotion, "negative")
        self.assertEqual(result.risk_level, "medium")
        self.assertFalse(result.rejection_required)

    def test_public_figure_positive(self):
        """测试涉及公众人物的正面评价"""
        question = "我很喜欢某某歌手的新歌"
        result = self.privacy_checker.check_privacy(question)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.has_public_figure)
        self.assertEqual(result.figure_category, "public")
        self.assertEqual(result.user_emotion, "positive")
        self.assertEqual(result.risk_level, "low")
        self.assertFalse(result.rejection_required)

    def test_real_names(self):
        """测试包含真实姓名的问题"""
        question = "我的同事张三最近表现很好"
        result = self.privacy_checker.check_privacy(question)
        self.assertFalse(result.is_safe)
        self.assertTrue(result.has_real_names)
        self.assertEqual(result.risk_level, "high")
        self.assertTrue(result.rejection_required)

    def test_invalid_response(self):
        """测试LLM返回无效响应的情况"""
        with patch('modules.privacy_checker.PrivacyChecker._extract_json_from_markdown') as mock_extract:
            mock_extract.side_effect = Exception("Invalid JSON")
            with self.assertRaises(ValidationError):
                self.privacy_checker.check_privacy("测试问题")


if __name__ == '__main__':
    unittest.main()
