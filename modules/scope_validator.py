"""
问题范围验证器模块

这个模块负责验证用户问题的范围合法性，包括：
1. 判断问题是否属于心理咨询范畴
2. 判断问题是否符合用户角色定位
"""
import re
import json
import logging
from typing import Dict, Any, Tuple

from ollama import Client

from config.settings import (
    LLM_SERVER, MODEL_CONFIG, PROJECT_ROOT,
    UserRole
)
from modules.exceptions import ValidationError


class ScopeValidator:
    def __init__(self):
        """初始化范围验证器"""
        self.client = Client(
            host=f"http://{LLM_SERVER['host']}:{LLM_SERVER['port']}"
        )
        self.logger = logging.getLogger(__name__)
        
        # 加载角色特定的提示词
        self.role_prompts = {}
        self._load_role_prompts()
        
    def _load_role_prompts(self):
        """加载各个角色的提示词"""
        role_files = {
            UserRole.STUDENT: "scope_validator_student.txt",
            UserRole.PARENT: "scope_validator_parent.txt",
            UserRole.TEACHER: "scope_validator_teacher.txt"
        }
        
        for role, filename in role_files.items():
            try:
                with open(f"{PROJECT_ROOT}/config/prompts/{filename}", "r", encoding="utf-8") as f:
                    self.role_prompts[role] = f.read()
            except Exception as e:
                self.logger.error(f"Failed to load prompt for role {role}: {str(e)}")
                raise ValidationError(f"Failed to load prompt for role {role}")

    def validate_question(self, question: str, role: UserRole) -> Tuple[bool, Dict[str, Any]]:
        """验证问题的合法性"""
        # 基本验证
        if question is None:
            raise ValidationError("问题不能为空")
            
        try:
            question = str(question)
        except:
            raise ValidationError("问题必须是字符串类型")
            
        question = question.strip()
        if not question:
            raise ValidationError("问题不能为空")
            
        if len(question) >= 1000:
            raise ValidationError("问题长度不能超过1000字符")
            
        if role is None or not isinstance(role, UserRole):
            raise ValidationError("用户角色无效")

        try:
            # 预处理验证：检查是否包含明显的不合适内容
            invalid_patterns = {
                r'写.*作[业文]|解.*题': "作业代写类问题不在咨询范围内",
                r'吃.*药|看.*医生|头疼|感冒': "医疗相关问题不在咨询范围内",
                r'股市|基金|理财|投资': "投资理财问题不在咨询范围内",
                r'政治|宗教|暴力|色情': "敏感话题不在咨询范围内",
                r'天气|电影|购物': "日常生活问题不在咨询范围内"
            }
            
            for pattern, reason in invalid_patterns.items():
                if re.search(pattern, question):
                    return False, {
                        "is_valid": False,
                        "topic": "",
                        "confidence": 1.0,
                        "problem_type": "非心理咨询范畴",
                        "safety_flag": "危险" if "敏感话题" in reason else "安全",
                        "reason": reason
                    }

            # 获取角色对应的提示词
            if role not in self.role_prompts:
                raise ValidationError(f"未找到角色 {role.value} 的提示词")
                
            prompt = self.role_prompts[role]
            
            # 构建验证提示词
            prompt = prompt.format(
                question=question,
                role=role.value
            )

            # 调用LLM进行验证
            try:
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
                self.logger.debug(f"LLM Response: {response}")
                self.logger.debug(f"LLM Response Content: {response['message']['content']}")
            except Exception as e:
                self.logger.error(f"LLM调用失败: {str(e)}")
                raise ValidationError(f"LLM调用失败: {str(e)}")

            # 提取JSON结果
            try:
                json_str = self._extract_json_from_markdown(response['message']['content'])
                self.logger.debug(f"Extracted JSON: {json_str}")
                result = json.loads(json_str)
                self.logger.debug(f"Parsed Result: {result}")
            except Exception as e:
                self.logger.error(f"解析LLM响应失败: {str(e)}")
                raise ValidationError(f"解析LLM响应失败: {str(e)}")
            
            # 验证结果格式
            required_fields = {
                'is_valid': bool,
                'topic': str,
                'confidence': float,
                'problem_type': str,
                'safety_flag': str,
                'reason': str
            }
            
            # 检查必要字段
            for field, field_type in required_fields.items():
                if field not in result:
                    raise ValidationError(f"缺少必要字段: {field}")
                if not isinstance(result[field], field_type):
                    raise ValidationError(f"字段类型错误: {field} 应为 {field_type.__name__}")
            
            # 检查安全标记和问题类型
            if result['safety_flag'] == "危险" or result['problem_type'] == "非心理咨询范畴":
                result['is_valid'] = False
            
            # 检查置信度
            if result['confidence'] < 0.8:
                result['is_valid'] = False
                
            return result['is_valid'], result

        except ValidationError as e:
            raise e
        except Exception as e:
            self.logger.error(f"验证问题时发生错误: {str(e)}")
            error_info = {
                "is_valid": False,
                "topic": "",
                "confidence": 0.0,
                "problem_type": "非心理咨询范畴",
                "safety_flag": "危险",
                "reason": str(e)
            }
            return False, error_info

    @staticmethod
    def _extract_json_from_markdown(text: str) -> str:
        """从markdown格式的文本中提取JSON内容"""
        if not text:
            raise ValidationError("输入文本不能为空")

        try:
            # 首先尝试直接解析文本作为JSON
            text = text.strip()
            if text.startswith('{') and text.endswith('}'):
                try:
                    json.loads(text)
                    return text
                except:
                    pass

            # 移除所有注释和多余的空白字符
            text = re.sub(r'//.*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s+', ' ', text)
            
            # 尝试匹配JSON对象
            pattern = r'\{[^{}]*\}'
            matches = re.findall(pattern, text)
            
            if matches:
                # 使用最后一个匹配结果（通常是最完整的）
                json_str = matches[-1].strip()
                # 验证JSON是否有效
                json.loads(json_str)
                return json_str
                
            raise ValidationError("无法从文本中提取JSON")
        except json.JSONDecodeError as e:
            raise ValidationError(f"无效的JSON格式: {str(e)}")
        except Exception as e:
            raise ValidationError(f"JSON提取失败: {str(e)}")
