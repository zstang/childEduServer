"""
全局配置模块

这个模块集中了所有系统配置，包括：
1. 服务器配置
2. LLM模型配置
3. 用户角色配置
4. 系统常量
5. 错误消息
"""

import os
from enum import Enum
from typing import Dict, List
from pydantic import BaseModel

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# LLM服务器配置
LLM_SERVER = {
    'host': '192.168.1.13',
    'port': 11434,
    'timeout': 30,  # 请求超时时间（秒）
}

# LLM模型配置
MODEL_CONFIG = {
    'model': 'gemma2:latest',
    #'model': 'qwen2.5',
    'temperature': 0.7,
    'top_p': 0.9,
    'max_tokens': 32000
}

# 提示词文件路径
PROMPT_PATHS = {
    'privacy_checker_prompt': os.path.join(PROJECT_ROOT, 'config', 'prompts', 'privacy_checker_prompt.txt'),
    'SCOPE_CHECK_PROMPT': os.path.join(PROJECT_ROOT, 'config', 'prompts', 'scope_check.txt'),
    'solution': os.path.join(PROJECT_ROOT, 'config', 'prompts', 'solution_prompt.txt')
}
# 提示词文件路径
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
VALIDATION_PROMPT = os.path.join(PROMPTS_DIR, "validation_prompt.txt")
PRIVACY_CHECK_PROMPT = os.path.join(PROMPTS_DIR, "privacy_check_prompt.txt")

# 用户角色定义
class UserRole(str, Enum):
    """用户角色枚举"""
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"

    @property
    def display_name(self) -> str:
        """返回角色的显示名称"""
        return {
            self.STUDENT: "学生",
            self.PARENT: "家长",
            self.TEACHER: "教师"
        }[self]

# 各角色允许的问题范围
ROLE_TOPICS = {
    UserRole.STUDENT: [
        "学习压力",
        "心理健康",
        "性格特点",
        "行为习惯",
        "学习方法",
        "人际交往"
    ],
    UserRole.PARENT: [
        "家庭关系",
        "子女教育",
        "工作压力",
        "情绪管理",
        "性格习惯",
        "社会交往"
    ],
    UserRole.TEACHER: [
        "家庭关系",
        "社会交往",
        "工作压力",
        "情绪管理",
        "性格发展",
        "教育教学"
    ]
}

# 问题类型的严重程度
TOPIC_SEVERITY = {
    "学习压力": "medium",
    "心理健康": "high",
    "性格特点": "low",
    "行为习惯": "medium",
    "学习方法": "low",
    "人际交往": "medium",
    "家庭关系": "high",
    "子女教育": "medium",
    "工作压力": "high",
    "情绪管理": "high",
    "性格习惯": "low",
    "社会交往": "medium",
    "性格发展": "medium",
    "教育教学": "medium"
}

# 错误消息
ERROR_MESSAGES = {
    'invalid_topic': '抱歉，您的问题不在我们的咨询范围内',
    'privacy_violation': '抱歉，您的问题包含了不应该透露的隐私信息',
    'political_content': '抱歉，我们不讨论政治相关话题',
    'public_figure': '抱歉，我们不讨论具体的公众人物',
    'validation_error': '问题验证失败，请稍后再试',
    'system_error': '系统出现错误，请稍后再试'
}
