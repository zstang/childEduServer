"""
隐私检查器模块

这个模块负责检查用户问题中的隐私和安全问题，包括：
1. 检查是否包含个人隐私信息
2. 检查是否包含政治敏感内容
3. 检查是否包含不当内容
"""

import json
import logging
import requests
import re
from typing import Dict, Any, Tuple
from ollama import Client
import os

from config.settings import LLM_SERVER, MODEL_CONFIG, PROMPT_PATHS
from modules.exceptions import ValidationError


class PrivacyCheckResult:
    def __init__(self, is_safe: bool, details: dict):
        self.is_safe = is_safe
        self.has_real_names = details.get('has_real_names', False)
        self.has_modern_political = details.get('has_modern_political', False)
        self.has_historical_figure = details.get('has_historical_figure', False)
        self.has_public_figure = details.get('has_public_figure', False)
        self.figure_category = details.get('figure_category', 'none')
        self.user_emotion = details.get('user_emotion', 'neutral')
        self.risk_level = details.get('risk_level', 'low')
        self.suggestion = details.get('suggestion', '')
        self.rejection_required = details.get('rejection_required', False)

    def to_dict(self):
        return {
            'is_safe': self.is_safe,
            'has_real_names': self.has_real_names,
            'has_modern_political': self.has_modern_political,
            'has_historical_figure': self.has_historical_figure,
            'has_public_figure': self.has_public_figure,
            'figure_category': self.figure_category,
            'user_emotion': self.user_emotion,
            'risk_level': self.risk_level,
            'suggestion': self.suggestion,
            'rejection_required': self.rejection_required
        }


class PrivacyChecker:
    def __init__(self):
        """初始化隐私检查器"""
        self.client = Client(
            host=f"http://{LLM_SERVER['host']}:{LLM_SERVER['port']}"
        )
        self.prompt_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            PROMPT_PATHS['privacy_checker_prompt']
        )
        self.logger = logging.getLogger(__name__)

        # 常见中文姓氏
        self.common_surnames = {
            '李', '王', '张', '刘', '陈', '杨', '黄', '赵', '周', '吴',
            '徐', '孙', '朱', '马', '胡', '郭', '林', '何', '高', '梁',
            '郑', '罗', '宋', '谢', '唐', '韩', '曹', '许', '邓', '萧',
            '冯', '曾', '程', '蔡', '彭', '潘', '袁', '于', '董', '余',
            '苏', '叶', '吕', '魏', '蒋', '田', '杜', '丁', '沈', '姜',
            '范', '江', '傅', '钟', '卢', '汪', '戴', '崔', '任', '陆',
            '廖', '姚', '方', '金', '邱', '夏', '谭', '韦', '贾', '邹',
            '石', '熊', '孟', '秦', '阎', '薛', '侯', '雷', '白', '龙',
            '段', '郝', '孔', '邵', '史', '毛', '常', '万', '顾', '赖',
            '武', '康', '贺', '严', '尹', '钱', '施', '牛', '洪', '龚'
        }

    def _extract_json_from_markdown(self, text: str) -> str:
        """
        从markdown格式的文本中提取JSON内容

        参数:
            text (str): 包含JSON的markdown文本

        返回:
            str: 提取出的JSON字符串
        """
        try:
            # 方法1：使用正则表达式匹配
            json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', text)
            if json_match:
                return json_match.group(1).strip()
            
            # 方法2：如果没有markdown标记，尝试提取JSON内容
            json_match = re.search(r'({[\s\S]*?})', text)
            if json_match:
                return json_match.group(1).strip()
                
            # 如果上述方法都失败，返回原始文本
            return text.strip()
        except Exception as e:
            raise ValidationError(f"JSON提取失败: {str(e)}")

    def _contains_real_name(self, text: str) -> bool:
        """
        检查文本是否包含真实姓名
        
        检查规则：
        1. 姓氏+名字（如：张三、李四）
        2. 姓氏+职位（如：王老师、张经理）
        3. "小"+名字（如：小明、小红）
        4. 姓氏+称谓（如：老王、小张）
        """
        # 分词处理
        words = list(text)
        
        for i in range(len(words)-1):
            # 检查当前字符
            current_char = words[i]
            next_char = words[i+1]
            
            # 1. 检查姓氏+名字/职位/称谓
            if current_char in self.common_surnames:
                # 姓氏后面是否跟着常见名字组合（如：三、四、明、华等）
                if next_char in {'三', '四', '五', '六', '七', '八', '九', '明', '华', '军', '伟', '强', '平'}:
                    return True
                # 姓氏后面是否跟着职位（如：老师、经理、主任等）
                if i < len(words)-2 and ''.join(words[i+1:i+3]) in {'老师', '经理', '主任', '医生', '教授'}:
                    return True
            
            # 2. 检查"小"+名字
            if current_char == '小':
                if next_char in {'明', '红', '华', '强', '军', '伟', '玲', '芳', '英', '梅'}:
                    return True
            
            # 3. 检查称谓+姓氏
            if current_char in {'老', '小'} and next_char in self.common_surnames:
                return True
        
        return False

    def check_privacy(self, question: str) -> PrivacyCheckResult:
        """
        检查用户问题是否包含隐私信息或敏感内容。
        
        Args:
            question: 用户的问题
            
        Returns:
            PrivacyCheckResult: 包含检查结果的对象
            
        Raises:
            ValidationError: 当LLM调用失败或返回格式错误时抛出
        """
        try:
            # 首先进行基于规则的真实姓名检查
            contains_name = self._contains_real_name(question)
            if contains_name:
                return PrivacyCheckResult(
                    is_safe=False,
                    details={
                        'is_safe': False,
                        'has_real_names': True,
                        'has_modern_political': False,
                        'has_historical_figure': False,
                        'has_public_figure': False,
                        'figure_category': 'none',
                        'user_emotion': 'neutral',
                        'risk_level': 'high',
                        'suggestion': '检测到真实姓名，请使用关系称谓代替',
                        'rejection_required': True
                    }
                )
            
            # 读取隐私检查提示词
            with open(self.prompt_file, "r", encoding="utf-8") as f:
                prompt = f.read()
            
            # 构建隐私检查提示词
            prompt = prompt.format(question=question)
            
            # 调用LLM进行检查
            response = self.client.chat(
                model=MODEL_CONFIG['model'],
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=False
            )

            # 提取JSON结果
            result = json.loads(self._extract_json_from_markdown(response['message']['content']))
            
            # 验证必要字段
            required_fields = ['is_safe', 'risk_level', 'rejection_required']
            for field in required_fields:
                if field not in result:
                    raise ValidationError(f"LLM响应缺少必要字段: {field}")
                    
            return PrivacyCheckResult(
                is_safe=result['is_safe'],
                details=result
            )
            
        except Exception as e:
            raise ValidationError(f"隐私检查失败: {str(e)}")
