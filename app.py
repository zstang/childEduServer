"""
主应用程序入口

这个模块作为整个应用的入口点，负责：
1. 初始化应用程序
2. 管理用户会话
3. 处理HTTP请求
4. 维护会话状态
"""

from flask import Flask, request, jsonify, session
from datetime import datetime, timedelta
import uuid
import json
from typing import Dict, Any, Optional

from hub.dialogue_manager import DialogueManager
from modules.state_tracker import StateTracker
from modules.knowledge_base import KnowledgeBase
from modules.solution_generator import SolutionGenerator
from modules.report_generator import ReportGenerator

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 用于session加密
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # 会话超时时间

# 初始化核心组件
dialogue_manager = DialogueManager()
state_tracker = StateTracker()
knowledge_base = KnowledgeBase()
solution_generator = SolutionGenerator()
report_generator = ReportGenerator()

# 存储活跃会话
active_sessions: Dict[str, Dict[str, Any]] = {}

# 会话配置
SESSION_TIMEOUT = timedelta(hours=2)
MAX_INACTIVE_TIME = timedelta(minutes=30)

def create_session() -> str:
    """创建新会话"""
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        'created_at': datetime.now(),
        'last_active': datetime.now(),
        'user_nickname': '', # 用户昵称
        'user_type': '', # 用户类型, 如学生/教师/家长
        'messages': [],
        'state': 'initial'
    }
    return session_id

def update_session_activity(session_id: str) -> None:
    """更新会话活动时间"""
    if session_id in active_sessions:
        active_sessions[session_id]['last_active'] = datetime.now()

def cleanup_inactive_sessions() -> None:
    """清理不活跃的会话"""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in active_sessions.items():
        last_active = session_data['last_active']
        if current_time - last_active > MAX_INACTIVE_TIME:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del active_sessions[session_id]

@app.before_request
def before_request():
    """请求预处理：清理过期会话"""
    cleanup_inactive_sessions()

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    处理聊天请求
    
    请求体格式：
    {
        "session_id": "会话ID（可选，首次对话不需要）",
        "message": "用户消息",
        "timestamp": "时间戳（可选）"
    }
    """
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Invalid request format',
                'required_fields': ['message']
            }), 400

        # 获取或创建会话ID
        session_id = data.get('session_id')
        if not session_id or session_id not in active_sessions:
            session_id = create_session()

        # 更新会话活动时间
        update_session_activity(session_id)
        
        # 获取会话状态
        session_data = active_sessions[session_id]
        
        # 处理用户输入
        response = dialogue_manager.process_input(
            data['message'],
            session_id
        )
        
        # 更新会话历史
        session_data['messages'].append({
            'role': 'user',
            'content': data['message'],
            'timestamp': datetime.now().isoformat()
        })
        session_data['messages'].append({
            'role': 'assistant',
            'content': response.get('response', ''),
            'timestamp': datetime.now().isoformat()
        })

        session_data['state'] = response.get('state', session_data['state'])
        print('-> ', session_data['state'])
        return jsonify({
            'session_id': session_id,
            'response': response.get('response', ''),
            'state': response.get('state', session_data['state']),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        app.logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/session/status', methods=['GET'])
def get_session_status():
    """获取会话状态"""
    session_id = request.args.get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({
            'error': 'Invalid or expired session'
        }), 404
    
    session_data = active_sessions[session_id]
    return jsonify({
        'session_id': session_id,
        'created_at': session_data['created_at'].isoformat(),
        'last_active': session_data['last_active'].isoformat(),
        'state': session_data['state'],
        'message_count': len(session_data['messages'])
    })

@app.route('/api/session/history', methods=['GET'])
def get_session_history():
    """获取会话历史"""
    session_id = request.args.get('session_id')
    if not session_id or session_id not in active_sessions:
        return jsonify({
            'error': 'Invalid or expired session'
        }), 404
    
    session_data = active_sessions[session_id]
    return jsonify({
        'session_id': session_id,
        'messages': session_data['messages']
    })

@app.route('/api/session/generate_report', methods=['POST'])
def generate_report():
    """生成会话报告"""
    try:
        data = request.json
        session_id = data.get('session_id')
        print(session_id)
        if not session_id or session_id not in active_sessions:
            return jsonify({
                'error': 'Invalid or expired session'
            }), 404
        session_data = active_sessions[session_id]
        # 生成报告
        report = report_generator.generate(session_id, session_data['messages'])
        
        return jsonify({
            'session_id': session_id,
            'report': report
        })
        
    except Exception as e:
        app.logger.error(f"Error generating report: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/session/end', methods=['POST'])
def end_session():
    """结束会话"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({
                'error': 'Invalid or expired session'
            }), 404
        
        # 生成最终报告
        session_data = active_sessions[session_id]
        final_report = report_generator.generate(session_id, session_data['messages'])
        
        # 清理会话数据
        session_data = active_sessions.pop(session_id)
        
        return jsonify({
            'session_id': session_id,
            'status': 'ended',
            'final_report': final_report,
            'session_summary': {
                'created_at': session_data['created_at'].isoformat(),
                'ended_at': datetime.now().isoformat(),
                'message_count': len(session_data['messages'])
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error ending session: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=15003)