import asyncio
import inspect
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI


async def safe_close_stream(stream) -> None:
    """安全关闭 stream，兼容协程和非协程的 close 方法"""
    if stream is None:
        return

    close_method = getattr(stream, 'close', None) or getattr(stream, 'aclose', None)
    if close_method is None:
        return

    try:
        result = close_method()
        # 如果返回的是协程，await 它
        if asyncio.iscoroutine(result):
            await result
    except Exception:
        pass

from ...models.agent import Agent
from ...models.llm import LLM
from ..logging_utils import ManagerLogger
from ..websocket_handler import MessageBuilder, WebSocketHandler


class OutputType(Enum):
    """输出类型枚举"""

    WEBSOCKET = "websocket"
    SSE = "sse"
    BLOCK = "block"


@dataclass
class TokenUsage:
    """Token使用情况"""
    total_tokens: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0

@dataclass
class ToolCall:
    """工具调用信息 - 对应 OpenAI Function Calling 格式"""
    id: str
    type: str = "function"
    function: Dict[str, Any] = field(default_factory=dict)  # {"name": "tool_name", "arguments": "json_string"}

@dataclass
class LLMResponse:
    """LLM响应结果"""
    content: str
    reasoning_content: str = ""
    token_usage: TokenUsage = None
    is_interrupted: bool = False
    tool_calls: List[ToolCall] = field(default_factory=list)  # Function Calling 的工具调用列表


class EnhancedLLMClient:
    """增强版LLM客户端 - 支持动态配置和多种输出方式"""
    
    @staticmethod
    def _extract_usage_tokens(usage, total_tokens: int, prompt_tokens: int,
                              completion_tokens: int, reasoning_tokens: int):
        """从一个 usage 来源（chunk.usage / choice.usage / delta.usage）提取四项 token。

        统一处理两种形态：
          - 对象形态（标准 OpenAI、moonshot 的 delta.usage、对象版 choice.usage）；
          - 字典形态（Kimi 风格把 usage 放在 choice 里且为 dict）。
        某一项取不到时回退到传入的当前值，行为与原先各处分散写法等价：
        正常 usage 对象/字典一定带这些字段，取到即用；缺失才保留旧值，不会抛错。
        reasoning_tokens 在标准 usage 中常缺省，回退尤为重要。

        Args:
            usage: 待提取的 usage 来源（对象或 dict），可能为 None。
            total_tokens/prompt_tokens/completion_tokens/reasoning_tokens: 当前已累积值，
                作为缺失字段的回退。

        Returns:
            (total_tokens, prompt_tokens, completion_tokens, reasoning_tokens) 四元组；
            usage 为 None 时原样返回传入值。
        """
        if not usage:
            return total_tokens, prompt_tokens, completion_tokens, reasoning_tokens

        if isinstance(usage, dict):
            getter = usage.get
        else:
            def getter(key, default=None):
                return getattr(usage, key, default)

        return (
            getter("total_tokens", total_tokens),
            getter("prompt_tokens", prompt_tokens),
            getter("completion_tokens", completion_tokens),
            getter("reasoning_tokens", reasoning_tokens),
        )

    @staticmethod
    def _accumulate_tool_calls(tool_calls_list: List[Dict], tool_call_delta) -> None:
        """累积流式传输的工具调用
        
        Args:
            tool_calls_list: 工具调用列表
            tool_call_delta: 流式传输的工具调用片段
        """
        # OpenAI 协议要求 tool_call delta 必带 index，但部分兼容平台（如小米）
        # 可能下发缺失/为 None 的 index，导致 None+1 抛 TypeError。此处兜底为 0。
        # 注意：刻意兜底为固定的 0，而非“追加到末尾”——已知平台单工具调用恒为 index=0，
        # 若改成追加，遇到后续真带 index=0 的 arguments 分片会错位到不同槽位，反而拆散同一个工具调用。
        index = getattr(tool_call_delta, "index", None)
        if index is None:
            index = 0

        # 根据 index 扩充列表
        if len(tool_calls_list) < (index + 1):
            tool_calls_list.extend([{}] * (index + 1 - len(tool_calls_list)))
        
        # 获取对应的 tool_call 对象
        tool_call = tool_calls_list[index]
        
        # 填充 id 和 type（通常在第一个 chunk 中）
        if tool_call_delta.id:
            tool_call["id"] = tool_call_delta.id
        if tool_call_delta.type:
            tool_call["type"] = tool_call_delta.type
            
        # 处理 function 字段
        if tool_call_delta.function:
            if "function" not in tool_call:
                tool_call["function"] = {}
                
            # 填充函数名（通常在第一个 chunk 中）
            if tool_call_delta.function.name:
                tool_call["function"]["name"] = tool_call_delta.function.name
                
            # 累积 arguments（流式传输）
            if tool_call_delta.function.arguments:
                if "arguments" not in tool_call["function"]:
                    tool_call["function"]["arguments"] = tool_call_delta.function.arguments
                else:
                    tool_call["function"]["arguments"] += tool_call_delta.function.arguments
    
    @staticmethod
    def _convert_tool_calls_list(tool_calls_list: List[Dict]) -> List[ToolCall]:
        """将工具调用列表转换为 ToolCall 对象
        Args:
            tool_calls_list: 工具调用字典列表
            
        Returns:
            ToolCall 对象列表
        """
        tool_calls = []
        for tool_call_dict in tool_calls_list:
            if not tool_call_dict:  # 过滤空字典
                continue
            function = tool_call_dict.get("function") or {}
            # 没函数名的 tool_call 无法执行，丢弃
            if not function.get("name"):
                continue
            # 部分 LLM 在无参调用时不发 arguments delta（OpenAI 协议要求必给空对象 "{}"），
            # 这里兜底，避免下游 tc["function"]["arguments"] KeyError
            if "arguments" not in function or function["arguments"] is None:
                function["arguments"] = "{}"
            tool_calls.append(ToolCall(
                id=tool_call_dict.get("id", ""),
                type=tool_call_dict.get("type", "function"),
                function=function
            ))
        return tool_calls

    def __init__(self, llm: Optional[LLM] = None, agent: Optional[Agent] = None):
        """
        初始化LLM客户端

        Args:
            llm: LLM对象（优先使用）
        """
        if llm:
            # 使用LLM对象
            self.llm = llm
            # 提取配置参数
            self.api_key = llm.api_key
            self.base_url = llm.url
            self.model = llm.model
            self.platform = llm.platform
            self.temperature = llm.temperature
            self.top_p = llm.top_p
            self.timeout = llm.timeout
            self.max_tokens = llm.max_tokens
        else:
            raise ValueError("必须提供 llm 对象")

        if agent:
            self.agent = agent
            # 初始化日志和客户端
            agent_id = self.agent.agent_id
        else:
            agent_id = "direct"

        self.logger = ManagerLogger(f"EnhancedLLMClient[{agent_id}]")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url if self.base_url else None, timeout=self.timeout)

        # 流控制相关（用于停止机制）
        self.current_stream = None   # 当前活跃的 stream
        self.should_stop = False     # 停止标志

        self.logger.info("初始化LLM客户端完成", {"agent_id": agent_id, "model": self.model, "base_url": self.base_url})

    async def block(self, messages: List[Dict[str, str]], conversation_id: str, 
                    tools: Optional[List[Dict[str, Any]]] = None,
                    **kwargs) -> LLMResponse:
        """
        阻塞式请求，返回完整结果
        内部使用流式接收，但对外表现为阻塞式

        Args:
            messages: 消息列表
            conversation_id: 会话ID
            tools: 工具列表（Function Calling格式）
            **kwargs: 其他参数(temperature, max_tokens, tool_choice等)

        Returns:
            LLMResponse: 完整的响应结果
        """
        # 构建API参数 - 使用流式
        params = self._build_api_params(messages, stream=True, tools=tools, **kwargs)

        self.logger.info("开始阻塞式请求（内部流式）", {"conversation_id": conversation_id, "model": params["model"]})

        full_content = ""
        reasoning_content = ""
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        reasoning_tokens = 0
        tool_calls_list = []  # 工具调用列表，按 index 存储

        try:
            stream = await self.client.chat.completions.create(**params)

            async for chunk in stream:
                # 安全检查：确保chunk有choices且不为空
                if not chunk.choices or len(chunk.choices) == 0:
                    # 处理token信息（某些chunk只包含usage信息）
                    total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = \
                        self._extract_usage_tokens(chunk.usage, total_tokens, prompt_tokens,
                                                   completion_tokens, reasoning_tokens)
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                # 处理工具调用
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        # 累积工具调用数据
                        self._accumulate_tool_calls(tool_calls_list, tool_call_delta)

                # 处理内容
                content = delta.content
                chunk_reasoning = getattr(delta, "reasoning_content", None)

                # 累积思考内容(如果模型支持)
                if chunk_reasoning:
                    reasoning_content += chunk_reasoning

                # 累积普通内容
                if content:
                    full_content += content

                # 处理token信息
                total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = \
                    self._extract_usage_tokens(chunk.usage, total_tokens, prompt_tokens,
                                               completion_tokens, reasoning_tokens)

                # 检查其他可能的 usage 位置（如 Kimi 将 usage 放在 choice 中，可能是 dict 或对象）
                if hasattr(choice, 'usage') and choice.usage:
                    total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = \
                        self._extract_usage_tokens(choice.usage, total_tokens, prompt_tokens,
                                                   completion_tokens, reasoning_tokens)

                # 特殊处理：moonshot 平台在 finish_reason="stop" 时，usage 在 delta 中
                if self.platform == "moonshot" and hasattr(choice, "finish_reason") and choice.finish_reason == "stop":
                    if hasattr(delta, "usage") and delta.usage:
                        total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = \
                            self._extract_usage_tokens(delta.usage, total_tokens, prompt_tokens,
                                                       completion_tokens, reasoning_tokens)

            # 将工具调用列表转换为 ToolCall 对象
            tool_calls = self._convert_tool_calls_list(tool_calls_list)

            result = LLMResponse(
                is_interrupted=False,
                content=full_content, 
                reasoning_content=reasoning_content, 
                token_usage=TokenUsage(
                    total_tokens=total_tokens,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    reasoning_tokens=reasoning_tokens
                ),
                tool_calls=tool_calls if tool_calls else None
            )

            self.logger.info("阻塞式请求完成", {
                "conversation_id": conversation_id, 
                "content_length": len(full_content), 
                "total_tokens": total_tokens, 
                "reasoning_length": len(reasoning_content),
                "has_tool_calls": bool(tool_calls)
            })

            return result

        except Exception as e:
            self.logger.error("阻塞式请求失败", exception=e, extra_data={"conversation_id": conversation_id})
            raise

    async def stream(self, messages: List[Dict[str, str]], conversation_id: str, 
                     output_type: OutputType = OutputType.WEBSOCKET, 
                     websocket_handler: Optional[WebSocketHandler] = None,
                     tools: Optional[List[Dict[str, Any]]] = None,
                     **kwargs) -> Union[AsyncGenerator, StreamingResponse]:
        """
        流式请求，支持WebSocket和SSE两种输出方式

        Args:
            messages: 消息列表
            conversation_id: 会话ID
            output_type: 输出类型(WEBSOCKET/SSE)
            websocket_handler: WebSocket处理器(仅WebSocket模式需要)
            tools: 工具列表（Function Calling格式）
            **kwargs: 其他参数(tool_choice, temperature等)

        Returns:
            AsyncGenerator或StreamingResponse
        """
        if output_type == OutputType.WEBSOCKET:
            return await self._stream_websocket(messages, conversation_id, websocket_handler, tools=tools, **kwargs)
        elif output_type == OutputType.SSE:
            return await self._stream_sse(messages, conversation_id, tools=tools, **kwargs)
        else:
            raise ValueError(f"不支持的输出类型: {output_type}")

    async def _stream_websocket(self, messages: List[Dict[str, str]], conversation_id: str, 
                                websocket_handler: WebSocketHandler,
                                tools: Optional[List[Dict[str, Any]]] = None,
                                **kwargs):
        """WebSocket流式输出"""
        import asyncio
        import time
        
        params = self._build_api_params(messages, stream=True, tools=tools, **kwargs)

        self.logger.info("开始WebSocket流式请求", {"conversation_id": conversation_id})
        full_content = ""
        reasoning_content = ""
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        reasoning_tokens = 0
        is_interrupted = False
        stream = None
        tool_calls_list = []  # 工具调用列表，按 index 存储
        
        # 超时重试配置
        max_attempts = 10  # 最大重试次数

        # 检测是否包含图片（VL 请求），VL 请求需要更长的超时时间
        has_images = False
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image_url":
                        has_images = True
                        break
            if has_images:
                break

        initial_timeout = 15 if has_images else 4  # VL 请求 15 秒，普通请求 4 秒
        if has_images:
            self.logger.info("检测到 VL 请求，使用较长超时", {"timeout": initial_timeout})
        
        for attempt in range(max_attempts):
            try:
                start_time = time.time()
                
                # 使用asyncio.wait_for添加超时控制
                # 第一次尝试30秒，第二次60秒，第三次120秒
                timeout_seconds = initial_timeout 
                
                if attempt > 0:
                    self.logger.warning(f"第{attempt + 1}次重试LLM请求", {
                        "conversation_id": conversation_id,
                        "timeout": timeout_seconds
                    })
                
                try:
                    stream = await asyncio.wait_for(
                        self.client.chat.completions.create(**params),
                        timeout=timeout_seconds
                    )
                    
                    # 如果成功创建stream，记录耗时并跳出重试循环
                    elapsed = time.time() - start_time
                    self.logger.info(f"LLM流创建成功，耗时: {elapsed:.2f}秒", {
                        "conversation_id": conversation_id,
                        "attempt": attempt + 1
                    })

                    # 保存 stream 引用（用于 stop() 方法关闭）
                    self.current_stream = stream

                    break  # 成功，跳出重试循环
                    
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    self.logger.error(f"LLM请求超时（{timeout_seconds}秒）", {
                        "conversation_id": conversation_id,
                        "attempt": attempt + 1,
                        "elapsed": elapsed
                    })
                    
                    if attempt < max_attempts - 1:
                        # 还有重试机会，等待一下再重试
                        await asyncio.sleep(1)
                        continue
                    else:
                        # 所有重试都失败了
                        raise Exception(f"LLM请求超时，已重试{max_attempts}次")
                        
            except Exception as e:
                error_str = str(e).lower()

                # VL 模型不支持检测：检测 image_url 相关错误
                if "image_url" in error_str or ("unknown variant" in error_str and "image" in error_str):
                    self.logger.error("当前模型不支持图片(VL)功能", {
                        "conversation_id": conversation_id,
                        "model": self.model,
                        "error": str(e)
                    })
                    raise Exception(f"当前模型 [{self.model}] 不支持图片功能，请开启新对话并切换到支持图片的模型")

                if "timeout" not in error_str and attempt < max_attempts - 1:
                    # 非超时错误，也可以重试
                    self.logger.error(f"LLM请求失败: {e}", {
                        "conversation_id": conversation_id,
                        "attempt": attempt + 1
                    })
                    await asyncio.sleep(2)
                    continue
                elif attempt == max_attempts - 1:
                    # 最后一次尝试也失败了
                    raise
        
        # 原有的流处理逻辑
        try:

            async for chunk in stream:
                # 检查停止标志（HTTP 停止接口触发）
                if self.should_stop:
                    is_interrupted = True
                    self.logger.info("检测到停止信号，中断LLM流", {
                        "conversation_id": conversation_id,
                        "current_tokens": total_tokens,
                        "content_length": len(full_content)
                    })
                    await safe_close_stream(stream)
                    break

                # 检查WebSocket连接状态，如果断开则中止流式调用
                if not websocket_handler.is_connected(conversation_id):
                    is_interrupted = True
                    self.logger.warning("WebSocket连接已断开，主动关闭LLM流式调用以节省token", {
                        "conversation_id": conversation_id,
                        "current_tokens": total_tokens,
                        "content_length": len(full_content)
                    })
                    # 主动关闭stream连接，真正停止服务器端生成
                    await safe_close_stream(stream)
                    break  # 中断循环，停止token消耗

                # 安全检查：确保chunk有choices且不为空
                # 部分平台（如小米 OpenAI 兼容 API）在工具调用流中会下发 choices 为空数组的
                # usage-only chunk，直接取 [0] 会抛 list index out of range。
                # 此处与 block()/_stream_sse() 保持一致：空 choices 时只提取 usage 后跳过。
                # （此分支无 choice 对象，只能取 chunk.usage）
                if not chunk.choices or len(chunk.choices) == 0:
                    total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = \
                        self._extract_usage_tokens(chunk.usage, total_tokens, prompt_tokens,
                                                   completion_tokens, reasoning_tokens)
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                # 兼容平台可能下发 delta 为空的边界 chunk（如仅含 finish_reason），
                # 此时仍需处理本 chunk 携带的 usage，故不能直接 continue 到循环顶部。
                # 此分支 choice 存在，故同时提取 chunk.usage 与 choice.usage（Kimi 风格），
                # 与正常路径保持一致，避免边界 chunk 的 token 统计丢失。
                if delta is None:
                    total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = \
                        self._extract_usage_tokens(chunk.usage, total_tokens, prompt_tokens,
                                                   completion_tokens, reasoning_tokens)
                    if hasattr(choice, 'usage') and choice.usage:
                        total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = \
                            self._extract_usage_tokens(choice.usage, total_tokens, prompt_tokens,
                                                       completion_tokens, reasoning_tokens)
                    continue

                # 处理工具调用
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        self._accumulate_tool_calls(tool_calls_list, tool_call_delta)

                # 处理内容
                content = getattr(delta, "content", None)
                chunk_reasoning = getattr(delta, "reasoning_content", None)

                # 发送思考内容(如果模型支持) 子agent模式不发送
                if chunk_reasoning and not self.agent.sub_agent_mode:
                    reasoning_content += chunk_reasoning
                    message = MessageBuilder.create_chunk_message(conversation_id, chunk_reasoning, "reasoning")
                    try:
                        await websocket_handler.send_message(conversation_id, message)
                    except Exception as send_error:
                        self.logger.warning("发送思考内容失败，连接可能已断开", {
                            "conversation_id": conversation_id,
                            "error": str(send_error)
                        })
                        continue

                # 发送普通内容 子agent模式不发送
                if content and not self.agent.sub_agent_mode:
                    full_content += content
                    message = MessageBuilder.create_chunk_message(conversation_id, content, "content")
                    try:
                        await websocket_handler.send_message(conversation_id, message)
                    except Exception as send_error:
                        self.logger.warning("发送内容失败，连接可能已断开", {
                            "conversation_id": conversation_id,
                            "error": str(send_error)
                        })
                        continue

                # 处理token信息
                total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = \
                    self._extract_usage_tokens(chunk.usage, total_tokens, prompt_tokens,
                                               completion_tokens, reasoning_tokens)

                # 检查其他可能的 usage 位置（如 Kimi 将 usage 放在 choice 中，可能是 dict 或对象）
                if hasattr(choice, 'usage') and choice.usage:
                    total_tokens, prompt_tokens, completion_tokens, reasoning_tokens = \
                        self._extract_usage_tokens(choice.usage, total_tokens, prompt_tokens,
                                                   completion_tokens, reasoning_tokens)

            # 将工具调用列表转换为 ToolCall 对象
            tool_calls = self._convert_tool_calls_list(tool_calls_list)

            return LLMResponse(
                is_interrupted=is_interrupted,
                content=full_content, 
                reasoning_content=reasoning_content, 
                token_usage=TokenUsage(
                    total_tokens=total_tokens,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    reasoning_tokens=reasoning_tokens
                ),
                tool_calls=tool_calls if tool_calls else None
            )

        except Exception as e:
            # 如果是主动停止导致的异常，不记录为错误
            if self.should_stop:
                self.logger.info("LLM流被主动停止", {"conversation_id": conversation_id})
                return LLMResponse(
                    is_interrupted=True,
                    content=full_content,
                    reasoning_content=reasoning_content,
                    token_usage=TokenUsage(
                        total_tokens=total_tokens,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        reasoning_tokens=reasoning_tokens
                    ),
                    tool_calls=None
                )

            error_msg = f"WebSocket流式请求失败: {str(e)}"
            self.logger.error("WebSocket流式请求失败", exception=e, extra_data={"conversation_id": conversation_id})

            # 发送错误消息
            error_message = MessageBuilder.create_error_message(conversation_id, error_msg)
            await websocket_handler.send_message(conversation_id, error_message)
            raise

        finally:
            # 清理状态（非常重要！）
            self.current_stream = None
            self.should_stop = False  # 重置，避免影响下次请求

            # 确保stream被正确关闭，避免资源泄漏
            await safe_close_stream(stream)
            self.logger.debug("Stream已正确关闭", {"conversation_id": conversation_id})

    async def _stream_sse(self, messages: List[Dict[str, str]], conversation_id: str,
                          tools: Optional[List[Dict[str, Any]]] = None,
                          **kwargs) -> StreamingResponse:
        """SSE流式输出"""
        params = self._build_api_params(messages, stream=True, tools=tools, **kwargs)

        self.logger.info("开始SSE流式请求", {"conversation_id": conversation_id})

        async def generate_sse():
            try:
                stream = await self.client.chat.completions.create(**params)

                async for chunk in stream:
                    # 安全检查：确保chunk有choices且不为空
                    if not chunk.choices or len(chunk.choices) == 0:
                        # 处理token信息（某些chunk只包含usage信息）
                        if chunk.usage:
                            sse_data = {
                                "type": "complete",
                                "conversation_id": conversation_id,
                                "usage": {"total_tokens": chunk.usage.total_tokens, "prompt_tokens": chunk.usage.prompt_tokens, "completion_tokens": chunk.usage.completion_tokens, "reasoning_tokens": getattr(chunk.usage, "reasoning_tokens", 0)},
                            }
                            yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"
                        continue

                    # 处理思考内容(如果模型支持)
                    chunk_reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                    if chunk_reasoning:
                        sse_data = {"type": "reasoning", "content": chunk_reasoning, "conversation_id": conversation_id}
                        yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"

                    # 处理普通内容
                    content = chunk.choices[0].delta.content
                    if content:
                        sse_data = {"type": "content", "content": content, "conversation_id": conversation_id}
                        yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"


                # 结束标记
                yield "data: [DONE]\n\n"

            except Exception as e:
                error_data = {"type": "error", "error": str(e), "conversation_id": conversation_id}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                self.logger.error("SSE流式请求失败", exception=e, extra_data={"conversation_id": conversation_id})

        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用nginx缓冲
            },
        )

    def _build_api_params(self, messages: List[Dict[str, str]], stream: bool = True, 
                          tools: Optional[List[Dict[str, Any]]] = None,
                          **kwargs) -> Dict:
        """构建API调用参数
        
        Args:
            messages: 消息列表
            stream: 是否流式
            tools: 工具列表（Function Calling格式）
            **kwargs: 其他参数(tool_choice, temperature等)
        """
        # 确保model不为None
        model = kwargs.get("model") or self.llm.model
        if not model:
            raise ValueError(f"模型参数不能为空，配置名称: {self.llm.agent_id}")
        
        # 基础参数
        params = {
            "model": model, 
            "messages": messages, 
            "temperature": kwargs.get("temperature", self.temperature), 
            "top_p": kwargs.get("top_p", self.top_p), 
            "max_tokens": kwargs.get("max_tokens", self.max_tokens), 
            "stream": stream
        }
        
        # Function Calling 相关参数
        if tools:
            params["tools"] = tools
            
            # tool_choice 参数（控制工具调用行为）
            # "auto": 模型自动决定是否调用工具（默认）
            # "none": 强制不使用工具
            # "required": 强制必须调用工具
            # {"type": "function", "function": {"name": "tool_name"}}: 强制调用特定工具
            if "tool_choice" in kwargs:
                params["tool_choice"] = kwargs["tool_choice"]
            else:
                params["tool_choice"] = "auto"  # 默认值
            
            # parallel_tool_calls 参数（是否支持并行调用多个工具）
            # 默认为 True，某些平台可能不支持
            if "parallel_tool_calls" in kwargs:
                params["parallel_tool_calls"] = kwargs["parallel_tool_calls"]
        
        # 检查平台类型
        platform = self.llm.platform if self.llm else None
        if platform == "tongyi":
            params["stream_options"] = {"include_usage": True}

        return params

    def get_config_info(self) -> Dict:
        """获取配置信息"""
        return {"config_name": self.config_name, "model": self.model, "base_url": self.base_url, "temperature": self.temperature, "max_tokens": self.max_tokens, "description": self.llm_config.get("description", "")}

    @classmethod
    def create_from_llm(cls, llm: LLM) -> "EnhancedLLMClient":
        """
        从LLM对象创建客户端（推荐方法）

        Args:
            llm: LLM对象

        Returns:
            配置好的LLM客户端
        """
        if not llm:
            raise ValueError("LLM对象不能为None")
        return cls(llm=llm)
    
    @classmethod
    def create_from_agent(cls, agent: Agent) -> "EnhancedLLMClient":
        """
        从Agent创建LLM客户端

        Args:
            agent: Agent实例

        Returns:
            配置好的LLM客户端
        """
        llmClient = cls(llm=agent.get_llm_for_mode(),agent=agent)
        return llmClient

    async def stop(self):
        """
        停止当前 LLM 生成

        调用此方法将：
        1. 设置停止标志，通知流式循环停止处理
        2. 关闭当前活跃的 stream，中断服务器端的生成

        注意：此方法是异步的，需要使用 await 调用
        """
        self.logger.info("收到停止LLM生成请求")

        # 设置停止标志
        self.should_stop = True

        # 尝试关闭当前活跃的 stream
        if self.current_stream:
            await safe_close_stream(self.current_stream)
            self.logger.info("成功关闭LLM流，已停止生成")
        else:
            self.logger.warning("没有活跃的stream可以停止")
