"""
测试反馈分析器模块

这个模块包含了对 FeedbackAnalyzer 类的测试，包括：
1. 基本的反馈分析功能测试
2. 边界情况测试
3. 错误处理测试
"""

import os
import sys
import unittest
from datetime import datetime
import logging

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from modules.feedback_analyzer import FeedbackAnalyzer, FeedbackType
from modules.exceptions import FeedbackAnalysisError

class TestFeedbackAnalyzer(unittest.TestCase):
    """测试反馈分析器"""

    # 测试数据集
    TEST_CASES = [
        {
            'name': '明确积极反馈',
            'feedback': '这个建议很有帮助，我会试试看',
            'solution': '建议您每天安排固定时间和孩子交流，了解他的想法和需求',
            'expected_type': FeedbackType.POSITIVE,
            'description': '用户明确表示建议有帮助'
        },
        {
            'name': '明确消极反馈',
            'feedback': '这个方法对我来说不太合适，我觉得不太有用',
            'solution': '您可以尝试每天做15分钟的冥想来缓解压力',
            'expected_type': FeedbackType.NEGATIVE,
            'description': '用户明确表示建议不合适'
        },
        {
            'name': '明确消极反馈',
            'feedback': '他在出现这些情绪的时候，整个人是听不进任何话的，试过的办法都是暂时缓解一下，其实我也不想让他看手机，但是没有别的方法。你有没有更好的方案？',
            'solution': '''五岁的孩子看到心仪的玩具哭闹想得到，这确实很常见的情况。很多家长都会遇到这样的难题。 孩子在这个年龄阶段好奇心强，想要的东西通常会强烈地渴望拥有，这时候如果不能及时引导和安慰，很容易情绪失控。 
您可以试试以下方法：先温柔地安抚孩子的情绪，告诉他理解他的感受，但是现在买玩具并不是一个好时机。可以尝试用其他方式转移他的注意力，比如带他去玩游乐场或者看一些有趣的小表演。  如果孩子仍然哭闹不止，可以和他商量一个达成共识的方式，例如下次逛街的时候再给他买个玩具，或者让他先选择一些书本或别的礼物。 
这样既能够满足孩子的愿望，又能够教会他理解"不能马上得到想要的东西"的道理，并学会控制自己的情绪。 您觉得这些建议是否符合您的情况？如果在实际操作中遇到什么困难，或者有什么不太适合的地方，请告诉我，我们可以一起调整方案。
''',
            'expected_type': FeedbackType.NEGATIVE,
            'description': '用户明确表示建议不合适'
        },
        {
            'name': '失去信心反馈',
            'feedback': '说了这么多都没用，你根本不懂我的情况',
            'solution': '建议您每天安排固定时间和孩子交流，了解他的想法和需求',
            'expected_type': FeedbackType.LOST_CONFIDENCE,
            'description': '用户表示系统不理解情况，失去信心'
        },
        {
            'name': '失去信心反馈2',
            'feedback': '我觉得你给不了什么有用的建议，还是算了吧',
            'solution': '建议您尝试和孩子一起制定一个每日活动计划',
            'expected_type': FeedbackType.LOST_CONFIDENCE,
            'description': '用户明确表示不相信系统能提供帮助'
        },
        {
            'name': '失去信心反馈3',
            'feedback': '看来你解决不了我的问题',
            'solution': '''五岁孩子在商场看到玩具哭闹，这很常见哦。很多小朋友都喜欢玩具，当他们想买但又不能立刻拥有的时候，可能会感到沮丧和失望，所以才会哭闹出来表达自己的情绪。
你可以试试这样：先耐心地安慰一下孩子，告诉他你喜欢他的想法，然后可以尝试和他商量一个解决方法，比如说下次再来的时候再买这个玩具，或者先看看其他的东西，如果今天真的不行，就给他一个拥抱，让他知道你理解他的感受。
您觉得这些建议是否符合您的情况？ 如果在实际操作中遇到什么困难，或者有什么不太适合的地方，请告诉我，我们可以一起调整方案。 ''',
            'expected_type': FeedbackType.LOST_CONFIDENCE,
            'description': '用户明确表示不相信系统能提供帮助'
        },
        {
            'name': '需要时间验证',
            'feedback': '我需要一段时间来尝试这个方法，看看效果如何',
            'solution': '建议您记录每天的情绪变化，观察规律',
            'expected_type': FeedbackType.NEED_TIME,
            'description': '用户表示需要时间验证'
        },
        {
            'name': '不确定反馈',
            'feedback': '嗯...这个建议听起来可以，但是我还有一些疑问',
            'solution': '您可以通过运动来释放压力，比如慢跑或瑜伽',
            'expected_type': FeedbackType.UNCERTAIN,
            'description': '用户表达了不确定性'
        },
        {
            'name': '间接积极反馈',
            'feedback': '我觉得这些建议说到点子上了，确实是我需要改变的地方',
            'solution': '建议您调整作息时间，保证充足的休息',
            'expected_type': FeedbackType.POSITIVE,
            'description': '用户通过间接方式表达认可'
        },
        {
            'name': '间接消极反馈',
            'feedback': '我之前试过类似的方法，但是没什么效果',
            'solution': '您可以尝试和朋友多交流，分享自己的感受',
            'expected_type': FeedbackType.NEGATIVE,
            'description': '用户通过过往经验表达否定'
        },
        {
            'name': '复杂反馈_偏积极',
            'feedback': '建议是不错的，不过我可能需要一点时间来调整，毕竟这是个习惯的改变',
            'solution': '建议您制定一个循序渐进的计划，慢慢改变',
            'expected_type': FeedbackType.NEED_TIME,
            'description': '用户既表达认可又表示需要时间'
        },
        {
            'name': '复杂反馈_偏消极',
            'feedback': '这个方法听起来是可行的，但是我担心在实际操作中会遇到困难',
            'solution': '您可以尝试把大目标分解成小目标，一步步完成',
            'expected_type': FeedbackType.UNCERTAIN,
            'description': '用户表达了认可但更多是担忧'
        }
    ]
    
    @classmethod
    def setUpClass(cls):
        """测试类的初始化工作"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        cls.logger = logging.getLogger(__name__)
        
    def setUp(self):
        """每个测试用例的初始化工作"""
        self.analyzer = FeedbackAnalyzer()
        
    def test_feedback_analysis(self):
        """测试反馈分析的基本功能"""
        for case in self.TEST_CASES:
            with self.subTest(name=case['name']):
                result = self.analyzer.analyze(
                    case['feedback'],
                    case['solution']
                )
                self.assertEqual(
                    result['type'],
                    case['expected_type'].value,
                    f"测试用例 '{case['name']}' 失败\n"
                    f"输入反馈: {case['feedback']}\n"
                    f"预期类型: {case['expected_type']}\n"
                    f"实际类型: {result}\n"
                    f"描述: {case['description']}"
                )
    '''
    def test_empty_feedback(self):
        """测试空反馈的处理"""
        empty_cases = [
            {'feedback': '', 'solution': '这是一个解决方案'},
            {'feedback': None, 'solution': '这是一个解决方案'},
            {'feedback': '   ', 'solution': '这是一个解决方案'}
        ]
        
        for case in empty_cases:
            with self.subTest(feedback=case['feedback']):
                with self.assertRaises(FeedbackAnalysisError):
                    self.analyzer.analyze(case['feedback'], case['solution'])
                    
    def test_invalid_solution(self):
        """测试无效解决方案的处理"""
        invalid_cases = [
            {'feedback': '这个建议不错', 'solution': ''},
            {'feedback': '这个建议不错', 'solution': None},
            {'feedback': '这个建议不错', 'solution': '   '}
        ]
        
        for case in invalid_cases:
            with self.subTest(solution=case['solution']):
                with self.assertRaises(FeedbackAnalysisError):
                    self.analyzer.analyze(case['feedback'], case['solution'])
                    
    def test_error_handling(self):
        """测试错误处理"""
        error_cases = [
            {
                'name': '超长反馈',
                'feedback': 'a' * 10000,  # 超长字符串
                'solution': '这是一个解决方案',
                'expected_error': FeedbackAnalysisError
            },
            {
                'name': '特殊字符反馈',
                'feedback': '\x00\x01',  # 非法字符
                'solution': '这是一个解决方案',
                'expected_error': FeedbackAnalysisError
            }
        ]
        
        for case in error_cases:
            with self.subTest(name=case['name']):
                with self.assertRaises(case['expected_error']):
                    self.analyzer.analyze(case['feedback'], case['solution'])

    '''
if __name__ == '__main__':
    unittest.main()
