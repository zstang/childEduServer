import unittest
from modules.question_generator import QuestionGenerator

class TestQuestionGenerator(unittest.TestCase):
    """测试问题生成模块"""

    def setUp(self):
        """测试前的准备工作"""
        self.generator = QuestionGenerator()
        
        # 测试用例1：多个问题的情况
        self.test_case_1 = {
            "problem": "用户因工作压力导致失眠，影响日常生活和工作专注力",
            "missing_info": {
                "critical": [
                    "失眠具体表现细节（例如：入睡困难、易醒、睡眠质量差）",
                    "工作压力来源和具体情况",
                    "其他可能影响睡眠的因素（例如：饮食习惯、运动情况）",
                    "失眠对日常生活的具体影响"
                ],
                "optional": [
                    "过往的睡眠情况",
                    "工作时间安排"
                ]
            }
        }
        
        # 测试用例2：较少问题的情况
        self.test_case_2 = {
            "problem": "用户感到焦虑和压力",
            "missing_info": {
                "critical": [
                    "焦虑的具体表现",
                    "压力来源"
                ],
                "optional": []
            }
        }

    def test_generate_list_format(self):
        """测试生成列表格式的提问（多个问题）"""
        print("\n测试用例1：多个问题")
        result = self.generator.generate(self.test_case_1)
        print("\n生成的提问内容:")
        print(result)
        
        # 验证输出格式
        self.assertIsInstance(result, str)
        self.assertIn("为了", result)  # 检查是否有开场白
        self.assertIn("1.", result)  # 应该包含编号列表
        self.assertIn("了解", result)  # 检查是否有结束语
        
        # 验证问题数量（通过计算数字编号的出现次数）
        question_count = sum(1 for line in result.split('\n') if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')))
        self.assertGreaterEqual(question_count, 3)  # 应该有3个或更多问题

    def test_generate_direct_format(self):
        """测试生成直接格式的提问（较少问题）"""
        print("\n测试用例2：较少问题")
        result = self.generator.generate(self.test_case_2)
        print("\n生成的提问内容:")
        print(result)
        
        # 验证输出格式
        self.assertIsInstance(result, str)
        self.assertIn("为了", result)  # 检查是否有开场白
        self.assertNotIn("1.", result)  # 不应该包含编号列表
        self.assertIn("回答", result)  # 检查是否有结束语
        
        # 验证包含问题关键词
        self.assertIn("焦虑", result)
        self.assertIn("压力", result)

    def test_validate_input(self):
        """测试输入验证"""
        # 测试缺少必要字段
        with self.assertRaises(ValueError):
            self.generator._validate_input({"problem": "测试问题"})
            
        # 测试missing_info格式错误
        with self.assertRaises(ValueError):
            self.generator._validate_input({
                "problem": "测试问题",
                "missing_info": "错误格式"
            })
            
        # 测试missing_info缺少必要字段
        with self.assertRaises(ValueError):
            self.generator._validate_input({
                "problem": "测试问题",
                "missing_info": {
                    "critical": ["测试"]
                }
            })

if __name__ == '__main__':
    unittest.main()
