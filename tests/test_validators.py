"""
问题验证器集成测试模块

这个模块包含了对问题验证器的集成测试，测试整个验证流程，包括：
1. 隐私检查
2. 范围验证
3. 新问题判断
"""

import unittest
import logging
from typing import Dict, Any

from hub.question_validator import QuestionValidator
from config.settings import UserRole


class TestQuestionValidator(unittest.TestCase):
    """测试问题验证器"""
    
    @classmethod
    def setUpClass(cls):
        """测试类的初始化工作"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        cls.logger = logging.getLogger(__name__)
        
    def setUp(self):
        """测试准备"""
        self.validator = QuestionValidator()
        
    def test_valid_question_flow(self):
        """测试有效问题的完整验证流程"""
        test_cases = [
            {
                "question": "我最近学习压力很大，该怎么调节？",
                "role": UserRole.STUDENT,
                "description": "学生学习压力问题"
            },
            {
                "question": "孩子的学习成绩下降，我很担心",
                "role": UserRole.PARENT,
                "description": "家长教育问题"
            },
            {
                "question": "班级管理让我很困扰",
                "role": UserRole.TEACHER,
                "description": "教师管理问题"
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                result = self.validator.validate_question(
                    case["question"],
                    case["role"]
                )
                self.assertTrue(result['is_valid'], 
                              f"问题应该是有效的，但返回无效。错误信息：{result.get('error_message')}")
                self.assertIsNone(result['error_message'])
                self.assertIsNotNone(result['topic'])
                    
    def test_privacy_violation_flow(self):
        """测试隐私违规问题的验证流程"""
        test_cases = [
            {
                "question": "张三最近学习成绩下降",
                "role": UserRole.TEACHER,
                "description": "包含真实姓名"
            },
            {
                "question": "某政府官员的政策让我困扰",
                "role": UserRole.PARENT,
                "description": "包含政治内容"
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                result = self.validator.validate_question(
                    case["question"],
                    case["role"]
                )
                self.assertFalse(result['is_valid'], 
                               f"问题应该因隐私问题被拒绝，但被标记为有效")
                self.assertIsNotNone(result['error_message'])
                self.assertIsNone(result['topic'])
                    
    def test_invalid_scope_flow(self):
        """测试范围无效问题的验证流程"""
        test_cases = [
            {
                "question": "推荐一些好看的电影",
                "role": UserRole.STUDENT,
                "description": "非咨询问题"
            },
            {
                "question": "帮我写一篇作文",
                "role": UserRole.STUDENT,
                "description": "学习辅导问题"
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                result = self.validator.validate_question(
                    case["question"],
                    case["role"]
                )
                self.assertFalse(result['is_valid'], 
                               f"问题应该因超出范围被拒绝，但被标记为有效")
                self.assertIsNotNone(result['error_message'])
                self.assertIsNone(result['topic'])
                    

if __name__ == '__main__':
    unittest.main()
