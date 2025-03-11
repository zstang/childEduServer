import ollama

# 指定Ollama服务的地址和端口
client = ollama.Client("http://192.168.1.13:11434/")

'''
response = client.generate("gemma2:latest", "请为我写一个简短的故事。", options={
    "num_generations": 1,  # 生成的文本数量
    "max_tokens": 100,    # 最大的生成令牌数量（近似于单词数量）
    "temperature": 0.7    # 控制生成的随机性，取值范围一般在0 - 1之间
})

print(response['response'])
'''

# 问题验证提示词模板
VALIDATION_PROMPT = """你是一个专业的心理咨询问题分析专家。你的任务是判断用户提出的问题是否属于心理咨询范畴，并确保问题符合用户的角色定位。

当前用户角色是：{role}

对于不同角色，我们只接受以下范围内的咨询问题：

学生：
- 学生成长相关问题
- 心理健康问题
- 性格特点分析
- 行为习惯改善
- 学习方法指导
- 人际交往困扰

家长：
- 家庭关系处理
- 孩子教养方法
- 工作压力调适
- 个人情绪管理
- 性格和习惯调整
- 社会交往问题

教师：
- 家庭关系协调
- 社会交往技巧
- 工作压力处理
- 情绪管理方法
- 性格发展指导
- 教育教学问题

用户问题：{question}

请严格按照以下规则进行判断：
1. 问题必须属于心理咨询范畴
2. 问题必须符合该用户角色的咨询范围
3. 判断是否是一个新的咨询主题

请以JSON格式返回分析结果：
{{
    "is_valid": true/false,         // 问题是否合法
    "topic": "具体主题",            // 识别出的具体主题
    "reason": "判断理由",           // 详细的判断理由
    "is_new_topic": true/false,     // 是否是新主题
    "confidence": 0.0-1.0           // 判断的置信度
}}

只返回JSON格式的结果，不要包含其他内容。对于不合法的问题，请在reason中详细说明原因。"""


prompt_usr = VALIDATION_PROMPT.format(
    role="学生",
    question="在学校里同学总是欺负我，我打不过他，他还威胁我不许告诉老师，我该怎么办？")

#print(prompt_usr)
#print(type(prompt_usr))

response = client.chat(
  model="gemma2:latest",
  messages=[
    {
      "role": "user",
      "content": prompt_usr
    }
  ]
)

print('----')
print(type(response))
print(response)
