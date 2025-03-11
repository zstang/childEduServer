"""
状态追踪器模块

这个模块负责追踪和管理咨询过程中的各种状态信息，包括：
1. 会话进度
2. 用户信息
3. 问题分析结果
4. 解决方案状态

主要功能：
- 状态信息的存储和检索
- 会话进度追踪
- 状态转换记录
- 数据持久化
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

class StateTracker:
    def __init__(self):
        """初始化状态追踪器"""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
    def create_session(self, session_id: str) -> None:
        """
        创建新的会话状态记录
        
        参数:
            session_id (str): 会话ID
        """
        self.sessions[session_id] = {
            'created_at': datetime.now(),
            'last_updated': datetime.now(),
            'progress': 0,
            'user_info': {},
            'problem_analysis': {},
            'questionnaire_responses': [],
            'solutions': [],
            'feedback': [],
            'completed': False
        }
    
    def update_progress(self, session_id: str, progress: int) -> None:
        """
        更新会话进度
        
        参数:
            session_id (str): 会话ID
            progress (int): 进度值（0-100）
        """
        if session_id in self.sessions:
            self.sessions[session_id]['progress'] = progress
            self.sessions[session_id]['last_updated'] = datetime.now()
    
    def add_user_info(self, session_id: str, info: Dict[str, Any]) -> None:
        """
        添加用户信息
        
        参数:
            session_id (str): 会话ID
            info (Dict[str, Any]): 用户信息
        """
        if session_id in self.sessions:
            self.sessions[session_id]['user_info'].update(info)
            self.sessions[session_id]['last_updated'] = datetime.now()
    
    def update_problem_analysis(self, session_id: str, 
                              analysis: Dict[str, Any]) -> None:
        """
        更新问题分析结果
        
        参数:
            session_id (str): 会话ID
            analysis (Dict[str, Any]): 分析结果
        """
        if session_id in self.sessions:
            self.sessions[session_id]['problem_analysis'].update(analysis)
            self.sessions[session_id]['last_updated'] = datetime.now()
    
    def add_questionnaire_response(self, session_id: str, 
                                 response: Dict[str, Any]) -> None:
        """
        添加问卷响应
        
        参数:
            session_id (str): 会话ID
            response (Dict[str, Any]): 问卷响应
        """
        if session_id in self.sessions:
            self.sessions[session_id]['questionnaire_responses'].append(response)
            self.sessions[session_id]['last_updated'] = datetime.now()
    
    def add_solution(self, session_id: str, solution: Dict[str, Any]) -> None:
        """
        添加解决方案
        
        参数:
            session_id (str): 会话ID
            solution (Dict[str, Any]): 解决方案
        """
        if session_id in self.sessions:
            self.sessions[session_id]['solutions'].append(solution)
            self.sessions[session_id]['last_updated'] = datetime.now()
    
    def add_feedback(self, session_id: str, feedback: Dict[str, Any]) -> None:
        """
        添加用户反馈
        
        参数:
            session_id (str): 会话ID
            feedback (Dict[str, Any]): 用户反馈
        """
        if session_id in self.sessions:
            self.sessions[session_id]['feedback'].append(feedback)
            self.sessions[session_id]['last_updated'] = datetime.now()
    
    def complete_session(self, session_id: str) -> None:
        """
        标记会话为已完成
        
        参数:
            session_id (str): 会话ID
        """
        if session_id in self.sessions:
            self.sessions[session_id]['completed'] = True
            self.sessions[session_id]['last_updated'] = datetime.now()
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话状态
        
        参数:
            session_id (str): 会话ID
            
        返回:
            Optional[Dict[str, Any]]: 会话状态信息
        """
        return self.sessions.get(session_id)
    
    def get_session_progress(self, session_id: str) -> Optional[int]:
        """
        获取会话进度
        
        参数:
            session_id (str): 会话ID
            
        返回:
            Optional[int]: 会话进度
        """
        session = self.sessions.get(session_id)
        return session['progress'] if session else None