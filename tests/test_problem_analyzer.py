import unittest
from modules.problem_analyzer import ProblemAnalyzer

class TestProblemAnalyzer(unittest.TestCase):
    """测试问题分析模块"""

    def setUp(self):
        """测试前的准备工作"""
        self.analyzer = ProblemAnalyzer()
        
        # 测试用例1：提供了较多信息的咨询对话
        self.test_case_1 = [
            {"role": "user", "content": "我今年28岁，是一名程序员。最近工作压力很大，经常失眠，差不多有两个月了。每周至少会失眠3-4次，躺在床上2-3个小时都睡不着，一直在想工作的事情。"},
            {"role": "assistant", "content": "听起来失眠困扰着你的生活。你之前有尝试过什么方法来改善睡眠吗？"},
            {"role": "user", "content": "我试过喝热牛奶和泡热水澡，效果不太明显。也下载了一个冥想APP，用了几次但感觉静不下心来。希望能尽快改善睡眠质量，最好一个月内就能看到效果，不然工作都没法专心。"}
        ]
        
        # 测试用例2：信息较少的咨询对话
        self.test_case_2 = [
            {"role": "user", "content": "我最近总是很焦虑，感觉压力很大。"},
            {"role": "assistant", "content": "能具体说说是什么让你感到焦虑吗？"},
            {"role": "user", "content": "工作上的事情，总是担心做不好。"}
        ]

    def test_analyze_complete_info(self):
        """测试分析包含较完整信息的对话"""
        print("\n测试用例1：完整信息分析")
        result = self.analyzer.analyze(self.test_case_1)
        print(result)
        
        # 验证基本结构
        self.assertIn("problem", result)
        self.assertIn("provided_info", result)
        self.assertIn("coping_history", result)
        self.assertIn("user_expectation", result)
        self.assertIn("missing_info", result)
        
        # 验证已提供信息
        provided_info = result["provided_info"]
        self.assertEqual(provided_info["age"], "28")  
        self.assertEqual(provided_info["occupation"], "程序员")
        self.assertIsNotNone(provided_info["frequency"])
        self.assertIsNotNone(provided_info["duration"])
        self.assertTrue(len(provided_info["symptoms"]) > 0)
        
        # 验证应对情况
        coping_history = result["coping_history"]
        self.assertTrue(len(coping_history["attempts"]) > 0)
        self.assertTrue(len(coping_history["effectiveness"]) > 0)
        
        # 验证期望
        expectation = result["user_expectation"]
        self.assertIsNotNone(expectation["timeline"])
        self.assertIn(expectation["solution_type"], ["long_term", "immediate", None])
        
        print("\n分析结果:")
        print(f"主要问题: {result['problem']}")
        print(f"已提供信息: {result['provided_info']}")
        print(f"应对情况: {result['coping_history']}")
        print(f"用户期望: {result['user_expectation']}")
        print(f"缺失信息: {result['missing_info']}")

    def test_analyze_incomplete_info(self):
        """测试分析信息不完整的对话"""
        print("\n测试用例2：不完整信息分析")
        result = self.analyzer.analyze(self.test_case_2)
        print(result)
        
        # 验证基本结构
        self.assertIn("problem", result)
        self.assertIn("provided_info", result)
        self.assertIn("coping_history", result)
        self.assertIn("user_expectation", result)
        self.assertIn("missing_info", result)
        
        # 验证缺失信息
        self.assertTrue(len(result["missing_info"]["critical"]) > 0)
        
        # 验证空值处理
        provided_info = result["provided_info"]
        self.assertIsNone(provided_info["age"])
        self.assertIsNone(provided_info["occupation"])
        self.assertEqual(len(result["coping_history"]["attempts"]), 0)
        self.assertIsNone(result["user_expectation"]["solution_type"])
        
        print("\n分析结果:")
        print(f"主要问题: {result['problem']}")
        print(f"已提供信息: {result['provided_info']}")
        print(f"应对情况: {result['coping_history']}")
        print(f"用户期望: {result['user_expectation']}")
        print(f"缺失信息: {result['missing_info']}")

    def test_format_conversation(self):
        """测试对话格式化功能"""
        formatted = self.analyzer._format_conversation(self.test_case_1)
        self.assertIsInstance(formatted, str)
        self.assertIn("用户:", formatted)
        self.assertIn("咨询师:", formatted)

if __name__ == '__main__':
    unittest.main()
