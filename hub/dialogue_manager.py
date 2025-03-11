"""
对话管理器模块

这个模块负责管理与用户的对话流程，实现：
1. 对话状态的流转
2. 用户输入的处理
3. 响应的生成和管理
4. 多轮对话的上下文维护
"""

import os
import sys
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from config.settings import UserRole, ERROR_MESSAGES
from hub.question_validator import QuestionValidator
from modules.solution_generator import SolutionGenerator
from modules.problem_analyzer import ProblemAnalyzer
from modules.question_generator import QuestionGenerator
from modules.feedback_analyzer import FeedbackAnalyzer
from modules.exceptions import ValidationError, ResponseGenerationError

class DialogueState(Enum):
    """对话状态枚举"""
    INITIAL = "initial"                 # 初始状态
    PROBLEM_ANALYSIS = "analysis"       # 问题分析
    QUESTIONNAIRE = "questionnaire"     # 问卷调查
    SOLUTION_GENERATION = "solution"    # 解决方案生成
    FEEDBACK = "feedback"               # 用户反馈
    REPORT_GENERATION = "report"        # 报告生成
    COMPLETED = "completed"             # 会话完成
    ERROR = "error"                     # 错误状态
    ENDED = "ended"                     # 会话结束

class FeedbackType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNCERTAIN = "uncertain"
    NEED_TIME = "need_time"
    LOST_CONFIDENCE = "lost_confidence"

class DialogueManager:
    def __init__(self):
        """初始化对话管理器"""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.question_validator = QuestionValidator()
        self.solution_generator = SolutionGenerator()
        self.problem_analyzer = ProblemAnalyzer()
        self.question_generator = QuestionGenerator()
        self.feedback_analyzer = FeedbackAnalyzer()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def process_input(self, user_input: str, session_id: str,
                     role: UserRole = UserRole.STUDENT) -> Dict[str, Any]:
        """
        处理用户输入，返回响应。

        Args:
            user_input: 用户输入的文本
            session_id: 会话ID
            role: 用户角色

        Returns:
            Dict[str, Any]: 包含响应内容和元数据的字典
        """
        # 获取或创建会话状态
        session = self._get_or_create_session(session_id)
        current_state = session.get('state', DialogueState.INITIAL)
        
        # 根据当前状态处理输入
        response = self._process_state(current_state, user_input, session)
        
        # 更新会话状态和历史
        self._update_session_state(session, response)
        
        return response

    def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """获取或创建新的会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'state': DialogueState.INITIAL,
                'context': {},
                'history': [],
                'current_topic': None,
                'analysis_result': {
                    'problem': None,
                    'provided_info': {},
                    'missing_info': {'critical': [], 'optional': []},
                    'last_updated': None
                },
                'created_at': datetime.now(),
                'last_active': datetime.now()
            }
        return self.sessions[session_id]

    def _handle_invalid_question(self, session: Dict[str, Any], 
                               error_message: str) -> Dict[str, Any]:
        """处理非法问题"""
        return {
            'response': error_message,
            'state': DialogueState.ERROR.value
        }
    
    # 用户咨询，建立 session
    def _handle_new_question(self, session: Dict[str, Any],
                           validation_result: Dict[str, Any],
                           user_input: str) -> Dict[str, Any]:
        """处理新问题"""
        # 更新会话主题
        session['current_topic'] = validation_result['topic']
        session['context'] = {
            'topic': validation_result['topic'],
            'initial_question': user_input
        }
        session['analysis_result'] = {
                'problem': None,
                'provided_info': {},
                'missing_info': {'critical': [], 'optional': []},
                'last_updated': None
            }
        # 重置会话状态
        session['state'] = DialogueState.PROBLEM_ANALYSIS
        
        # 生成响应
        return {
            'response': self._generate_new_question_response(validation_result),
            'state': DialogueState.QUESTIONNAIRE.value
        }
    
    def _generate_new_question_response(self, 
                                      validation_result: Dict[str, Any]) -> str:
        """生成新问题的响应"""
        try:
            # 使用 solution_generator 生成响应
            response = self.solution_generator.generate_response(
                question=validation_result.get('initial_question', ''),
                context={
                    'topic': validation_result.get('topic', '一般咨询'),
                    'state': DialogueState.INITIAL.value
                }
            )
            return response.get('response', '我理解您的问题，让我们开始咨询。')
        except Exception as e:
            return f"我理解您想咨询关于{validation_result.get('topic', '一般咨询')}的问题。让我们先了解一下具体情况。请您详细描述一下您遇到的问题。"
    
    def _process_state(self, state: DialogueState, user_input: str, 
                      session: Dict[str, Any]) -> Dict[str, Any]:
        """根据当前状态处理用户输入
        
        Args:
            state: 当前状态
            user_input: 用户输入
            session: 当前会话数据
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            if state == DialogueState.INITIAL:
                return self._handle_initial_state(user_input)
            elif state == DialogueState.PROBLEM_ANALYSIS:
                return self._handle_problem_analysis(user_input, session)
            elif state == DialogueState.QUESTIONNAIRE:
                # 如果在问卷状态收到用户输入，直接进入解决方案生成
                return self._handle_solution_generation(
                    user_input, 
                    session, 
                    session.get('analysis_result', {})
                )
            elif state == DialogueState.SOLUTION_GENERATION:
                return self._handle_solution_generation(
                    user_input, 
                    session,
                    session.get('analysis_result', {})
                )
            elif state == DialogueState.FEEDBACK:
                return self._handle_feedback(user_input, session)
            elif state == DialogueState.REPORT_GENERATION:
                return self._handle_report_generation(session)
            else:
                self.logger.error(f"Unknown state: {state}")
                return {
                    'response': ERROR_MESSAGES['unknown_state'],
                    'state': DialogueState.INITIAL.value
                }
        except Exception as e:
            self.logger.error(f"Error processing state {state}: {str(e)}")
            return {
                'response': ERROR_MESSAGES['processing_error'],
                'state': DialogueState.INITIAL.value
            }
    
    def _update_session_state(self, session: Dict[str, Any], response: Dict[str, Any]) -> None:
        """更新会话状态和历史记录
        
        Args:
            session: 当前会话数据
            response: 处理结果
        """
        # 更新会话状态
        if 'state' in response:
            session['state'] = DialogueState(response['state'])
        
        # 更新历史记录
        history_entry = {
            'timestamp': datetime.now(),
            'user_input': response.get('user_input'),
            'response': response.get('response'),
            'state': response.get('state')
        }
        session['history'].append(history_entry)
        
        # 更新最后活动时间
        session['last_active'] = datetime.now()
        
        # 保存分析结果（如果有）
        if 'analysis_result' in response:
            session['analysis_result'] = response['analysis_result']
            
        # 记录日志
        self.logger.info(
            f"Session updated - Current State: {session['state']}, "
            f"History Length: {len(session['history'])}"
        )
    
    def _handle_initial_state(self, user_input: str) -> Dict[str, Any]:
        """处理初始状态"""
        # 安全检查、话题范围检查、隐私保护策略检查

        return self._handle_problem_analysis(user_input, {})
    
    def _handle_problem_analysis(self, user_input: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """处理问题分析状态"""
        try:
            # 获取历史对话
            history = session.get('history', [])
            messages = [{'role': 'user', 'content': user_input}]
            if history:
                messages.extend([{
                    'role': 'user' if h.get('user_input') else 'assistant',
                    'content': h.get('user_input') or h.get('response')
                } for h in history])
    
            # 分析问题并更新会话
            analysis_result = self.problem_analyzer.analyze(messages)
            
            # 检查是否需要更多信息
            missing_info = analysis_result.get('missing_info', {})
            critical_missing = missing_info.get('critical', [])
            optional_missing = missing_info.get('optional', [])
            
            if critical_missing or optional_missing:
                # 如果有缺失信息，进入问卷调查状态
                questionnaire_response = self._handle_questionnaire(user_input, analysis_result)
                questionnaire_response['analysis_result'] = analysis_result
                return questionnaire_response
            else:
                # 如果信息完整，直接进入解决方案生成状态
                solution_response = self._handle_solution_generation(user_input, session, analysis_result)
                solution_response['analysis_result'] = analysis_result
                return solution_response
                
        except Exception as e:
            self.logger.error(f"Problem analysis failed: {str(e)}")
            return {
                'response': '抱歉，我在理解您的问题时遇到了一些困难。请您能再详细描述一下吗？',
                'state': DialogueState.PROBLEM_ANALYSIS.value
            }

    def _handle_questionnaire(self, user_input: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理问卷调查状态"""
        try:
            # 生成问题
            questions = self.question_generator.generate(analysis_result)
            
            # 记录日志
            self.logger.info(
                f"Generated questions for missing info: "
                f"{analysis_result.get('missing_info', {})}"
            )
            
            return {
                'response': questions,
                'state': DialogueState.SOLUTION_GENERATION.value,
                'user_input': user_input
            }
            
        except ValueError as e:
            self.logger.error(f"Question generation failed: {str(e)}")
            return {
                'response': '抱歉，我在生成问题时遇到了一些困难。让我们换个方式，您能告诉我更多关于您的情况吗？',
                'state': DialogueState.QUESTIONNAIRE.value,
                'user_input': user_input
            }
        except Exception as e:
            self.logger.error(f"Unexpected error in questionnaire handling: {str(e)}")
            return {
                'response': '抱歉，系统出现了一些问题。请稍后再试。',
                'state': DialogueState.QUESTIONNAIRE.value,
                'user_input': user_input
            }
    
    def _handle_solution_generation(self, user_input: str, 
                                  session: Dict[str, Any], 
                                  analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理解决方案生成状态
        
        Args:
            user_input: 用户输入
            session: 当前会话数据
            analysis_result: 问题分析结果
            
        Returns:
            Dict[str, Any]: 包含响应内容和状态转换信息的字典
        """
        try:
            # 准备生成解决方案的上下文
            context = {
                'topic': session.get('context', {}).get('topic', '一般咨询'),
                'state': session.get('state', DialogueState.SOLUTION_GENERATION).value,
                'history': session.get('messages', []),
                'analysis_result': analysis_result
            }
            
            # 构建问题描述
            problem_description = (
                f"根据分析，用户的问题是：{analysis_result.get('problem', '未指定')}\n"
                f"已收集的信息：{json.dumps(analysis_result.get('provided_info', {}), ensure_ascii=False)}"
            )
            print('----------')
            print(context)
            print('----------')
            # 生成解决方案
            solution = self.solution_generator.generate_response(
                question=problem_description,
                context=context
            )
            
            # 记录日志
            self.logger.info(
                f"Generated solution for problem: {analysis_result.get('problem')}"
            )
            
            # 更新会话状态
            session['solution'] = solution.get('message', {}).get('content', '')
            
            return {
                'response': session['solution'],
                'state': DialogueState.FEEDBACK.value,
                'solution': session['solution']
            }
            
        except Exception as e:
            self.logger.error(f"Solution generation failed: {str(e)}")
            return {
                'response': '抱歉，我在生成解决方案时遇到了一些困难。您能再详细描述一下您的情况吗？',
                'state': DialogueState.SOLUTION_GENERATION.value
            }
    
    def _handle_feedback(self, user_input: str, 
                        session: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户反馈状态
        
        根据用户的反馈决定是继续咨询还是结束会话：
        - 如果反馈是不确定或否定，继续咨询
        - 如果反馈是肯定或需要时间，进入报告生成阶段
        
        Args:
            user_input: 用户的反馈内容
            session: 当前会话数据
            
        Returns:
            Dict[str, Any]: 包含响应内容和状态转换信息的字典
        """
        try:
            # 获取之前生成的解决方案
            solution = session.get('solution', '')
            if not solution:
                self.logger.error("No solution found in session")
                return {
                    'response': '抱歉，我找不到之前的解决方案。让我们重新开始，您能再描述一下您的问题吗？',
                    'state': DialogueState.SOLUTION_GENERATION.value
                }
            
            # 分析用户反馈
            feedback_result = self.feedback_analyzer.analyze(user_input, solution)
            feedback_type = feedback_result.get('type', '').lower()
            response = feedback_result.get('response', '')
            print(feedback_result)
            # 记录反馈结果
            session['feedback'] = {
                'content': user_input,
                'type': feedback_type,
                'timestamp': datetime.now()
            }
            
            # 根据反馈类型决定下一步
            if feedback_type == FeedbackType.LOST_CONFIDENCE.value:
                # 用户失去信心，结束对话
                session['state'] = DialogueState.ENDED
                return {
                    'response': response,
                    'state': DialogueState.ENDED.value
                }
            elif feedback_type in [FeedbackType.NEGATIVE.value.lower(), FeedbackType.UNCERTAIN.value.lower()]:
                # 用户对解决方案不满意或不确定，继续咨询
                # 用户补充说明或者解释疑虑后，重新生成解决方案
                return {
                    'response': response + '\n\n您能具体说说哪些方面需要改进或者有什么疑虑吗？',
                    'state': DialogueState.SOLUTION_GENERATION.value,
                    'feedback_type': feedback_type
                }
            else:
                # 用户对解决方案满意或需要时间验证，准备结束咨询
                return self._handle_report_generation(session)
                
        except Exception as e:
            self.logger.error(f"Feedback handling failed: {str(e)}")
            return {
                'response': '抱歉，我在处理您的反馈时遇到了一些问题。您能再说一下您对解决方案的想法吗？',
                'state': DialogueState.FEEDBACK.value
            }
    
    def _handle_report_generation(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """处理报告生成状态"""
        return {
            'response': '您的咨询报告已经生成。感谢您的信任，如果还有其他问题，随时都可以来找我。',
            'state': DialogueState.COMPLETED.value
        }