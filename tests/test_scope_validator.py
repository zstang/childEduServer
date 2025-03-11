"""
范围验证器测试模块

这个模块包含了对范围验证器的测试用例，包括：
1. 问题范围验证
2. 用户角色验证
3. 错误处理测试
"""

import unittest
import json
import logging
from modules.scope_validator import ScopeValidator
from config.settings import UserRole
from modules.exceptions import ValidationError

# 配置日志输出
logging.basicConfig(level=logging.DEBUG)

class TestScopeValidator(unittest.TestCase):
    """测试范围验证器"""
    
    def setUp(self):
        """测试前的设置"""
        self.validator = ScopeValidator()
        
    def test_invalid_questions(self):
        """测试各类无效问题的验证"""
        test_cases = [
            # 作业代写类
            ("帮我写一篇作文", UserRole.STUDENT),
            ("帮我解这道数学题", UserRole.STUDENT),
            # 医疗类
            ("最近头疼要吃什么药", UserRole.PARENT),
            ("感冒了要去看哪个医生", UserRole.TEACHER),
            # 投资理财类
            ("推荐一下理财产品", UserRole.PARENT),
            ("股市最近怎么样", UserRole.TEACHER),
            # 敏感话题
            ("对某个政治事件的看法", UserRole.STUDENT),
            # 日常生活类
            ("今天天气怎么样", UserRole.PARENT),
            ("推荐个好看的电影", UserRole.TEACHER)
        ]
        
        for question, role in test_cases:
            is_valid, result = self.validator.validate_question(question, role)
            self.assertFalse(is_valid)
            self.assertEqual(result['problem_type'], "非心理咨询范畴")
            self.assertTrue(isinstance(result['reason'], str))
            self.assertTrue(len(result['reason']) > 0)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试空问题
        with self.assertRaises(ValidationError):
            self.validator.validate_question(None, UserRole.STUDENT)
            
        with self.assertRaises(ValidationError):
            self.validator.validate_question("", UserRole.STUDENT)
            
        # 测试问题长度超限
        long_question = "测试" * 500
        with self.assertRaises(ValidationError):
            self.validator.validate_question(long_question, UserRole.STUDENT)
            
        # 测试无效角色
        with self.assertRaises(ValidationError):
            self.validator.validate_question("测试问题", None)

    def test_extract_json(self):
        """测试JSON提取功能"""
        # 测试直接JSON
        json_str = '{"is_valid":true,"topic":"学习压力","confidence":0.95,"problem_type":"学生问题","safety_flag":"安全","reason":""}'
        result = self.validator._extract_json_from_markdown(json_str)
        self.assertEqual(
            json.loads(result), 
            {
                "is_valid": True,
                "topic": "学习压力",
                "confidence": 0.95,
                "problem_type": "学生问题",
                "safety_flag": "安全",
                "reason": ""
            }
        )
        
        # 测试带空白字符的JSON
        json_str = """
        {
            "is_valid": true,
            "topic": "学习压力",
            "confidence": 0.95,
            "problem_type": "学生问题",
            "safety_flag": "安全",
            "reason": ""
        }
        """
        result = self.validator._extract_json_from_markdown(json_str)
        self.assertEqual(
            json.loads(result), 
            {
                "is_valid": True,
                "topic": "学习压力",
                "confidence": 0.95,
                "problem_type": "学生问题",
                "safety_flag": "安全",
                "reason": ""
            }
        )
        
        # 测试无效输入
        with self.assertRaises(ValidationError):
            self.validator._extract_json_from_markdown("")
            
        with self.assertRaises(ValidationError):
            self.validator._extract_json_from_markdown("invalid json")

    def test_valid_student_questions(self):
        """测试学生用户的有效问题验证"""
        test_cases = [
            "我最近学习压力很大，总是睡不好觉，影响了考试成绩",
            "感觉和同学相处很困难，不知道该如何改善关系",
            "对未来的专业选择很困惑，不知道该怎么规划",
            "最近情绪很低落，总是控制不住自己",
            "和父母沟通总是不顺畅，经常发生争吵"
        ]
        
        for question in test_cases:
            is_valid, result = self.validator.validate_question(
                question,
                UserRole.STUDENT
            )
            self.assertTrue(is_valid)
            self.assertEqual(result['problem_type'], "学生问题")
            self.assertTrue(result['confidence'] > 0.8)
            self.assertIn(result['safety_flag'], ["安全", "需要关注"])
            self.assertIn(result['topic'], [
                "学业压力", "人际关系", "生涯规划", 
                "情绪管理", "家庭关系", "自我认知"
            ])

    def test_valid_parent_questions(self):
        """测试家长用户的有效问题验证"""
        test_cases = [
            "孩子最近学习成绩下降，我很担心",
            "和孩子沟通总是不顺畅，不知道该怎么办",
            "孩子总是沉迷游戏，影响学习",
            "对孩子的教育方式感到困惑",
            "孩子性格内向，不愿意与人交往"
        ]
        
        for question in test_cases:
            is_valid, result = self.validator.validate_question(
                question,
                UserRole.PARENT
            )
            self.assertTrue(is_valid)
            self.assertEqual(result['problem_type'], "家长问题")
            self.assertTrue(result['confidence'] > 0.8)
            self.assertIn(result['safety_flag'], ["安全", "需要关注"])
            self.assertIn(result['topic'], [
                "子女教育", "亲子关系", "情绪管理", 
                "家庭教育"
            ])

    def test_valid_teacher_questions(self):
        """测试教师用户的有效问题验证"""
        test_cases = [
            "工作压力很大，影响了教学状态和身心健康",
            "课堂管理总是出现问题，学生纪律难以控制",
            "和学生沟通不太顺畅，不知道如何建立良好关系",
            "对教学方法感到困惑，希望能提高教学效果",
            "感觉职业倦怠，不知道该如何调整"
        ]
        
        for question in test_cases:
            is_valid, result = self.validator.validate_question(
                question,
                UserRole.TEACHER
            )
            self.assertTrue(is_valid)
            self.assertEqual(result['problem_type'], "教师问题")
            self.assertTrue(result['confidence'] > 0.8)
            self.assertIn(result['safety_flag'], ["安全", "需要关注"])
            self.assertIn(result['topic'], [
                "职业压力", "班级管理", "师生关系", 
                "教学困扰", "情绪管理", "专业成长"
            ])

if __name__ == '__main__':
    unittest.main()
