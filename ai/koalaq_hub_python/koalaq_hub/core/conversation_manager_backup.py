    def _process_messages_for_frontend(self, raw_messages: List[Message]) -> List[Dict[str, Any]]:
        """
        将数据库原始消息转换为前端需要的格式 (支持新的消息类型)

        处理逻辑：
        1. user + content -> type: user
        2. assistant + content -> type: segment
        3. assistant + agent_start -> type: agent_start
        4. assistant + tool_call -> type: segment (如果有内容) + tool_call
        5. tool + tool_result -> type: tool_response
        6. tool + agent_end -> type: agent_response
        7. 忽略error类型消息

        Args:
            raw_messages: 原始消息列表（Message 对象）

        Returns:
            处理后的消息列表（保持正确的显示顺序）
        """

        processed = []

        for i, message in enumerate(raw_messages):
            if message.role == "user" and message.type == MessageType.CONTENT:
                processed.append({
                    "message_id": message.message_id, 
                    "round_id": message.round_id, 
                    "type": "user", 
                    "content": message.content, 
                    "timestamp": message.timestamp
                })
            
            elif message.role == "assistant" and message.type == MessageType.CONTENT:
                segment_data = {
                    "message_id": message.message_id, 
                    "round_id": message.round_id, 
                    "type": "segment", 
                    "content": message.content, 
                    "timestamp": message.timestamp
                }
                if message.reasoning_content:
                    segment_data["reasoning_content"] = message.reasoning_content
                processed.append(segment_data)
            
            # 新增：处理 AGENT_START 类型
            elif message.role == "assistant" and message.type == MessageType.AGENT_START:
                processed.append({
                    "message_id": message.message_id,
                    "round_id": message.round_id,
                    "type": "agent_start",
                    "content": message.content,
                    "agent_id": message.agent_id,
                    "timestamp": message.timestamp
                })
            
            # 修改：统一的 TOOL_CALL 类型处理
            elif message.type == MessageType.TOOL_CALL:
                # 先添加 AI 的回复内容（如果有）
                if message.content:
                    segment_data = {
                        "message_id": f"{message.message_id}_segment",
                        "round_id": message.round_id,
                        "type": "segment",
                        "content": message.content,
                        "timestamp": message.timestamp
                    }
                    if message.reasoning_content:
                        segment_data["reasoning_content"] = message.reasoning_content
                    processed.append(segment_data)
                
                # 解析 tool_calls
                if message.tool_calls:  # 使用属性访问
                    try:
                        for tool_call in message.tool_calls:
                            processed.append({
                                "message_id": f"{message.message_id}_tc_{tool_call['id']}",
                                "round_id": message.round_id,
                                "type": "tool_call",
                                "tool_name": tool_call["function"]["name"],
                                "tool_call_id": tool_call["id"],
                                "tool_arguments": tool_call["function"]["arguments"],
                                "timestamp": message.timestamp
                            })
                    except:
                        pass
            
            # 处理工具结果
            elif message.type == MessageType.TOOL_RESULT:
                processed.append({
                    "message_id": message.message_id,
                    "round_id": message.round_id,
                    "type": "tool_response",
                    "tool_name": message.tool_name or "",
                    "tool_call_id": message.tool_call_ids or "",
                    "content": message.content,
                    "status": message.tool_success,
                    "timestamp": message.timestamp
                })
            
            # 新增：处理 AGENT_END 类型
            elif message.type == MessageType.AGENT_END:
                processed.append({
                    "message_id": message.message_id,
                    "round_id": message.round_id,
                    "type": "agent_response",
                    "agent_id": message.agent_id,
                    "sub_conversation_id": message.sub_conversation_id,
                    "content": message.content,
                    "timestamp": message.timestamp
                })
            
            else:
                continue

        return processed