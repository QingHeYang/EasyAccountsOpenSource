<template>
  <div class="ai-plus-container">
    <van-sticky>
      <van-nav-bar
        title="AI+"
        left-text="返回"
        left-arrow
        @click-left="$router.go(-1)"
      >
      <template #right>
        <div class="nav-right-container">
          <div 
            class="connection-status" 
            :class="{ clickable: !wsConnected }"
            @click="handleConnectionClick"
          >
            <van-icon 
              :name="wsConnected ? 'success' : 'warning-o'" 
              :color="wsConnected ? '#07c160' : '#ff976a'"
              size="12"
            />
            <span :style="{color: wsConnected ? '#07c160' : '#ff976a'}" class="status-text">
              {{ wsConnected ? '已连接' : (reconnecting ? '连接中...' : '未连接') }}
            </span>
          </div>
          <van-button 
            type="primary" 
            size="mini"
            plain
            @click="startNewConversation"
            icon="plus"
          >
            新对话
          </van-button>
        </div>
      </template>
      </van-nav-bar>
    </van-sticky>
    
    <div class="content-area">
      <!-- 消息列表区域 -->
      <div class="messages-container">
        <van-empty 
          v-if="messages.length === 0 && !loading"
          description="有什么问题想问我呢？"
        />
        
        <!-- 消息列表 -->
        <div v-for="message in messages" :key="message.id" class="message-item">
          <div v-if="message.type === 'user'" class="user-message">
            <div class="message-content">{{ message.content }}</div>
            <div class="message-time">{{ message.timestamp }}</div>
          </div>
          
          <div v-else-if="message.type === 'ai'" class="ai-message" :class="{ 'error-message': message.isError }">
            <!-- 思维链区域 -->
            <div v-if="message.hasReasoning" class="reasoning-section">
              <div class="reasoning-header" @click="toggleReasoning(message.id)">
                <van-icon name="bulb-o" size="14" />
                <span class="reasoning-title">思考过程</span>
                <van-icon 
                  :name="message.reasoningExpanded ? 'arrow-up' : 'arrow-down'" 
                  size="12" 
                  class="reasoning-arrow"
                />
              </div>
              <div v-if="message.reasoningExpanded" class="reasoning-content">
                <div class="reasoning-text">{{ message.reasoning }}</div>
              </div>
            </div>
            
            <!-- AI回复内容 -->
            <div class="message-content" v-html="renderMarkdown(message.content)"></div>
            <div class="message-time">{{ message.timestamp }}</div>
          </div>
          
          <div v-else-if="message.type === 'tool'" class="tool-message" @click="showToolDetail(message)">
            <div class="tool-content" :class="{ success: message.status === true, failed: message.status === false, loading: message.status === null }">
              <van-tag type="primary" size="mini">🔧 {{ message.toolName }}</van-tag>
              <div class="tool-status">
                <van-loading v-if="message.status === null" type="spinner" size="12" />
                <van-icon v-else :name="message.status ? 'success' : 'cross'" size="12" />
                {{ message.status === null ? '执行中...' : (message.status ? '执行成功' : '执行失败') }}
              </div>
              <van-icon name="arrow" size="14" color="#969799" />
            </div>
            <div class="message-time">{{ message.timestamp }}</div>
          </div>
        </div>
        
        <!-- 当前正在输入的消息 -->
        <div v-if="currentMessage || currentReasoning" class="ai-message typing">
          <!-- 实时思维链区域 -->
          <div v-if="currentReasoning" class="reasoning-section current">
            <div class="reasoning-header">
              <van-icon name="bulb-o" size="14" />
              <span class="reasoning-title">思考中...</span>
            </div>
            <div class="reasoning-content">
              <div class="reasoning-text">{{ currentReasoning }}</div>
            </div>
          </div>
          
          <!-- 实时AI回复内容 -->
          <div v-if="currentMessage" class="message-content" v-html="renderMarkdown(currentMessage)"></div>
          <div class="typing-indicator">AI正在输入...</div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-message">
          <van-loading type="spinner" size="16" />
          <span>AI正在思考...</span>
        </div>
      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="input-container-wrapper">
      <div class="input-container">
        <div class="input-wrapper">
          <textarea
            v-model="inputMessage"
            ref="messageInput"
            class="message-textarea"
            placeholder="请输入您的问题..."
            rows="1"
            maxlength="500"
            @input="adjustTextareaHeight"
            @keydown="handleKeydown"
          ></textarea>
        </div>
        <van-button 
          type="primary" 
          size="small"
          class="send-button"
          :loading="sending"
          loading-text="发送中"
          @click="sendMessage"
          :disabled="!inputMessage.trim() || sending"
        >
          发送
        </van-button>
      </div>
    </div>
    
    <!-- 工具详情弹窗 -->
    <van-popup
      v-model:show="showToolDetailPopup"
      position="bottom"
      :style="{ height: '70%' }"
      round
      closeable
      close-on-click-overlay
    >
      <div class="tool-detail-popup">
        <div class="tool-detail-header">
          <h3>🔧 {{ currentToolDetail.toolName }}</h3>
          <div class="tool-status" :class="{ success: currentToolDetail.status, failed: !currentToolDetail.status }">
            <van-icon :name="currentToolDetail.status ? 'success' : 'cross'" size="14" />
            {{ currentToolDetail.status ? '执行成功' : '执行失败' }}
          </div>
        </div>
        
        <div class="tool-detail-content">
          <!-- 调用参数 -->
          <div class="console-section">
            <div class="section-title">📥 调用参数</div>
            <div class="console-box">
              <pre class="console-text">{{ formatConsoleText(currentToolDetail.toolCall) }}</pre>
            </div>
          </div>
          
          <!-- 返回结果 -->
          <div class="console-section">
            <div class="section-title">📤 返回结果</div>
            <div class="console-box">
              <pre class="console-text">{{ formatConsoleText(currentToolDetail.toolResponse) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script>
import aiHttpService from '@/utils/ai-request.js';
import aiWebSocketManager from '@/utils/websocket.js';
import MarkdownIt from 'markdown-it';
import markdownItMultimdTable from 'markdown-it-multimd-table';
import { showToast } from 'vant';

export default {
  name: 'AiPlus',
  data() {
    return {
      inputMessage: '',
      // 固定参数
      userId: 'user_67ce21d6-a11c-4340-851b-7a8949906aa3',
      conversationId: '', // 动态从localStorage读取
      apiBaseUrl: window.config?.aiApiUrl || 'http://localhost:8001',
      // UI状态
      loading: false,
      sending: false, // 发送消息状态
      wsConnected: false,
      reconnecting: false, // 重连状态
      // 消息相关
      messages: [], // 消息列表
      currentMessage: '', // 当前正在拼接的AI消息
      currentReasoning: '', // 当前正在拼接的思维链内容
      pendingToolCalls: new Map(), // 待处理的工具调用队列，使用Map存储 toolCallId -> messageId
      // 工具详情弹窗
      showToolDetailPopup: false,
      currentToolDetail: {
        toolName: '',
        status: false,
        toolCall: '',
        toolResponse: ''
      },
      md: new MarkdownIt('commonmark', {
        html: true,        // 启用HTML标签
        linkify: true,     // 自动转换URL为链接
        typographer: true, // 启用一些语言中性的替换和引号美化
        breaks: true       // 转换段落里的 '\n' 到 <br>
      }).enable(['table']).use(markdownItMultimdTable, {
        multiline: true,   // 允许多行表格
        rowspan: true,     // 允许行合并
        headerless: true,  // 允许无表头表格
        multibody: true    // 允许多个表体
      }),
      // WebSocket事件监听器清理函数
      wsCleanupFunctions: [],
    };
  },
  mounted() {
    this.initConversation();
    this.initAiService();
    this.initWebSocket();
  },
  beforeUnmount() {
    // 页面销毁时清理监听器并断开WebSocket连接
    this.cleanupWebSocketListeners();
    this.disconnectWebSocket();
  },
  methods: {
    // 初始化对话
    initConversation() {
      // 从localStorage读取conversation_id
      this.conversationId = localStorage.getItem('ai_conversation_id') || '';
      
      // 如果有conversation_id，加载历史消息
      if (this.conversationId) {
        this.loadMessages();
      }
    },
    
    // 保存conversation_id到localStorage
    saveConversationId(conversationId) {
      if (conversationId) {
        this.conversationId = conversationId;
        localStorage.setItem('ai_conversation_id', conversationId);
      }
    },
    
    // 开启新对话
    startNewConversation() {
      // 清空conversation_id
      this.conversationId = '';
      localStorage.removeItem('ai_conversation_id');
      
      // 清空消息列表
      this.messages = [];
      this.currentMessage = '';
      this.currentReasoning = '';
      this.pendingToolCalls.clear(); // 清理待处理队列
      
      // 重置状态
      this.loading = false;
      this.sending = false;
      
      showToast({
        type: 'success',
        message: '已开启新对话'
      });
    },
    
    sendMessage() {
      if (!this.inputMessage.trim() || this.sending) return;
      
      const messageContent = this.inputMessage.trim();
      this.sending = true; // 开始发送状态
      
      if (!this.wsConnected) {
        this.sending = false;
        showToast({
          type: 'fail',
          message: 'WebSocket未连接，无法发送消息'
        });
        return;
      }
      
      // 添加用户消息到消息列表，并滚动到底部
      this.addMessage({
        type: 'user',
        content: messageContent,
        timestamp: new Date().toLocaleTimeString()
      }, true);
      
      // 构造发送消息格式
      const message = {
        conversation_id: this.conversationId || '',
        content: messageContent
      };
      
      // 发送消息
      const success = aiWebSocketManager.send(message);
      if (success) {
        this.inputMessage = '';
        this.adjustTextareaHeight(); // 重置输入框高度
        this.loading = true;
        // 重置当前消息状态
        this.currentMessage = '';
        this.currentReasoning = '';
        this.currentToolCall = null;
      } else {
        this.sending = false; // 发送失败，重置状态
        showToast({
          type: 'fail',
          message: '消息发送失败'
        });
      }
    },
    
    // 解析历史消息（HTTP API格式）
    parseHistoryMessages(apiMessages) {
      const uiMessages = [];
      
      for (const msg of apiMessages) {
        if (msg.role === 'user') {
          // 用户消息
          uiMessages.push({
            id: `history_${msg.message_id}`,
            type: 'user',
            content: msg.text.content,
            timestamp: this.formatTimestamp(msg.timestamp)
          });
        } else if (msg.role === 'assistant') {
          // AI回复消息 - 只处理包含content的消息，跳过纯工具调用前的预备消息
          if (msg.text && msg.text.content && !msg.message_id.includes('_content')) {
            uiMessages.push({
              id: `history_${msg.message_id}`,
              type: 'ai',
              content: msg.text.content,
              reasoning: msg.text.reasoning_content || '', // 思维链内容
              hasReasoning: !!(msg.text.reasoning_content && msg.text.reasoning_content.trim()), // 是否包含思维链
              timestamp: this.formatTimestamp(msg.timestamp)
            });
          }
        } else if (msg.role === 'tool') {
          // 工具调用消息
          if (msg.tool) {
            uiMessages.push({
              id: `history_${msg.message_id}`,
              type: 'tool',
              content: `执行${msg.tool.tool_name}${msg.tool.tool_status === 1 ? '成功' : '失败'}`, 
              toolName: msg.tool.tool_name,
              toolCallId: msg.tool.tool_call_id || '', // 添加tool_call_id
              status: msg.tool.tool_status === 1,
              timestamp: this.formatTimestamp(msg.timestamp),
              toolCall: msg.tool.tool_arguments || '',
              toolResponse: msg.tool.tool_result || ''
            });
          }
        }
      }
      
      return uiMessages;
    },
    
    // 解析WebSocket消息为UI消息格式
    parseWebSocketMessage(data, messageType) {
      const timestamp = new Date().toLocaleTimeString();
      const id = `ws_${Date.now()}_${Math.random()}`;
      
      if (messageType === 'ai_segment') {
        // AI完整回复
        return {
          id,
          type: 'ai',
          content: data.text,
          reasoning: data.object?.reasoning_content || '', // 思维链内容
          hasReasoning: !!(data.object?.reasoning_content && data.object.reasoning_content.trim()), // 是否包含思维链
          timestamp
        };
      } else if (messageType === 'tool_complete') {
        // 工具调用完成
        return {
          id,
          type: 'tool',
          content: `执行${data.toolName}${data.status ? '成功' : '失败'}`,
          toolName: data.toolName,
          status: data.status,
          timestamp,
          toolCall: data.toolCall || '',
          toolResponse: data.toolResponse || ''
        };
      }
      
      return null;
    },
    
    // 格式化时间戳
    formatTimestamp(timestamp) {
      if (!timestamp) return new Date().toLocaleTimeString();
      
      // 处理不同的时间格式
      let date;
      if (timestamp.includes('-') && timestamp.includes(':')) {
        // "2025-07-12 17:56:50" 格式
        date = new Date(timestamp);
      } else {
        date = new Date(timestamp);
      }
      
      return date.toLocaleTimeString();
    },
    
    // 添加消息到列表
    addMessage(message, shouldScroll = false) {
      const newMessage = {
        id: Date.now() + Math.random(),
        ...message
      };
      this.messages.push(newMessage);
      // 只在指定时滚动到底部
      if (shouldScroll) {
        this.scrollToBottom();
      }
    },
    
    // 滚动到底部
    scrollToBottom() {
      this.$nextTick(() => {
        // 尝试多种方式确保滚动成功
        const container = this.$el?.querySelector('.messages-container');
        const contentArea = this.$el?.querySelector('.content-area');
        
        if (container) {
          // 方法1：使用scrollTo
          container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
          });
        } else if (contentArea) {
          // 方法2：如果messages-container找不到，使用content-area
          contentArea.scrollTo({
            top: contentArea.scrollHeight,
            behavior: 'smooth'
          });
        }
        
        // 方法3：延迟再次尝试（确保DOM更新完成）
        setTimeout(() => {
          const retryContainer = this.$el?.querySelector('.messages-container') || this.$el?.querySelector('.content-area');
          if (retryContainer) {
            retryContainer.scrollTop = retryContainer.scrollHeight;
          }
        }, 100);
      });
    },
    
    // 初始化AI服务
    initAiService() {
      aiHttpService.updateConfig(this.apiBaseUrl);
    },
    
    // 加载消息列表
    async loadMessages() {
      // 没有conversation_id时不加载历史消息
      if (!this.conversationId) {
        return;
      }
      
      try {
        this.loading = true;
        
        const url = `/api/v1/conversations/${this.conversationId}/messages`;
        
        // 使用 aiHttpService，它已经配置了正确的 baseURL 和 headers
        const response = await aiHttpService.get(url);
        
        if (response && response.data && response.data.messages) {
          // 将API消息转换为UI消息格式，并反转顺序（API返回的是倒序）
          const apiMessages = response.data.messages.reverse();
          this.messages = this.parseHistoryMessages(apiMessages);
          
          // 历史消息加载完成后滚动到底部
          this.$nextTick(() => {
            this.scrollToBottom();
          });
        }
        
      } catch (error) {
        console.error('加载消息失败:', error);
        showToast({
          type: 'fail',
          message: '加载历史消息失败'
        });
      } finally {
        this.loading = false;
      }
    },
    
    
    // 初始化WebSocket连接
    initWebSocket() {
      // 先清理之前的监听器
      this.cleanupWebSocketListeners();
      
      // 注册新的监听器并保存清理函数
      const cleanupConnect = aiWebSocketManager.onConnect(() => {
        const wasReconnecting = this.reconnecting;
        this.wsConnected = true;
        this.reconnecting = false; // 连接成功时重置重连状态
        
        if (wasReconnecting) {
          showToast({
            type: 'success',
            message: '重连成功'
          });
        }
      });
      
      const cleanupDisconnect = aiWebSocketManager.onDisconnect(() => {
        this.wsConnected = false;
      });
      
      const cleanupError = aiWebSocketManager.onError((error) => {
        console.error('WebSocket错误:', error);
      });
      
      const cleanupMessage = aiWebSocketManager.onMessage((data) => {
        this.handleWebSocketMessage(data);
      });
      
      // 保存清理函数
      this.wsCleanupFunctions = [
        cleanupConnect,
        cleanupDisconnect, 
        cleanupError,
        cleanupMessage
      ];
      
      // 开始连接，use_think_llm 固定为 false
      aiWebSocketManager.connect(this.userId, 'easy-accounts-agent', false);
    },
    
    // 清理WebSocket监听器
    cleanupWebSocketListeners() {
      if (this.wsCleanupFunctions.length > 0) {
        this.wsCleanupFunctions.forEach(cleanup => {
          if (typeof cleanup === 'function') {
            cleanup();
          }
        });
        this.wsCleanupFunctions = [];
      }
    },
    
    // 断开WebSocket连接
    disconnectWebSocket() {
      aiWebSocketManager.disconnect();
      this.wsConnected = false;
    },
    
    // 处理WebSocket消息
    handleWebSocketMessage(data) {
      if (!data || !data.type) {
        return;
      }
      
      // 更新会话ID
      if (data.conversation_id && data.conversation_id !== this.conversationId) {
        // 保存新的conversation_id到localStorage
        this.saveConversationId(data.conversation_id);
      }
      
      switch (data.type) {
        case 'chunk':
          this.handleChunkMessage(data);
          break;
        case 'segment':
          this.handleSegmentMessage(data);
          break;
        case 'tool_call':
          this.handleToolCallMessage(data);
          break;
        case 'tool_response':
          this.handleToolResponseMessage(data);
          break;
        case 'exit':
          this.handleExitMessage(data);
          break;
        case 'error':
          this.handleErrorMessage(data);
          break;
      }
    },
    
    // 处理chunk消息（流式文本）
    handleChunkMessage(data) {
      if (data.text) {
        // 根据content_type区分是正常内容还是思维链
        const contentType = data.object?.content_type || 'content';
        
        if (contentType === 'reasoning') {
          // 思维链内容
          this.currentReasoning += data.text;
        } else {
          // 正常回复内容
          this.currentMessage += data.text;
        }
        
        this.loading = false; // 开始接收内容时停止loading
        // 接收消息时不自动滚动
      }
    },
    
    
    // 处理segment消息（完整段落）
    handleSegmentMessage(data) {
      if (data.text) {
        // 使用新的解析方法
        const uiMessage = this.parseWebSocketMessage(data, 'ai_segment');
        if (uiMessage) {
          // 如果有实时拼接的思维链内容，优先使用
          if (this.currentReasoning.trim()) {
            uiMessage.reasoning = this.currentReasoning;
            uiMessage.hasReasoning = true;
          }
          this.addMessage(uiMessage); // 接收AI消息时不滚动
        }
      }
      
      // 重置当前拼接的消息和思维链
      this.currentMessage = '';
      this.currentReasoning = '';
      this.loading = false;
    },
    
    // 处理tool_call消息（工具调用）
    handleToolCallMessage(data) {
      const toolName = data.object?.tool_name || data.text || '未知工具';
      const toolCallId = data.object?.tool_call_id || `tool_${Date.now()}`;
      const toolArguments = data.object?.tool_arguments || '';
      
      console.log('收到tool_call:', { toolName, toolCallId });
      
      // 检查是否已在待处理队列中
      if (this.pendingToolCalls.has(toolCallId)) {
        console.log('tool_call已在队列中，跳过:', toolCallId);
        return;
      }
      
      // 创建唯一的消息ID
      const messageId = `tool_msg_${toolCallId}_${Date.now()}`;
      
      // 添加到待处理队列
      this.pendingToolCalls.set(toolCallId, messageId);
      
      // 添加工具调用消息（loading状态）
      this.addMessage({
        id: messageId,
        type: 'tool',
        content: `执行${toolName}中...`,
        toolName: toolName,
        toolCallId: toolCallId, // 保存tool_call_id用于后续匹配
        status: null, // null表示正在执行
        timestamp: new Date().toLocaleTimeString(),
        toolCall: toolArguments,
        toolResponse: ''
      }); // 工具执行时不滚动
    },
    
    // 处理tool_response消息（工具响应）
    handleToolResponseMessage(data) {
      const toolName = data.object?.tool_name || data.text || '未知工具';
      const toolCallId = data.object?.tool_call_id || '';
      const toolResponse = data.object?.tool_response || '';
      const isSuccess = data.status === true;
      
      console.log('收到tool_response:', { toolName, toolCallId, isSuccess });
      
      // 首先检查待处理队列
      if (this.pendingToolCalls.has(toolCallId)) {
        const messageId = this.pendingToolCalls.get(toolCallId);
        
        // 通过消息ID查找对应的工具消息
        const toolMessage = this.messages.find(msg => msg.id === messageId);
        
        if (toolMessage) {
          // 更新找到的工具消息
          toolMessage.content = `执行${toolName}${isSuccess ? '成功' : '失败'}`;
          toolMessage.status = isSuccess;
          toolMessage.toolResponse = toolResponse;
          
          // 从待处理队列中移除
          this.pendingToolCalls.delete(toolCallId);
          console.log('成功匹配并更新tool_call:', toolCallId);
          return;
        }
      }
      
      // 如果队列中没有，尝试通过toolCallId直接查找（兼容历史消息）
      const toolMessage = this.messages.find(msg => 
        msg.type === 'tool' && msg.toolCallId === toolCallId && msg.status === null
      );
      
      if (toolMessage) {
        // 更新找到的工具消息
        toolMessage.content = `执行${toolName}${isSuccess ? '成功' : '失败'}`;
        toolMessage.status = isSuccess;
        toolMessage.toolResponse = toolResponse;
        console.log('通过toolCallId匹配并更新:', toolCallId);
      } else {
        // 如果都没找到，创建新消息
        console.warn(`未找到对应的tool_call消息，创建新响应消息:`, toolCallId);
        this.addMessage({
          id: `tool_response_${toolCallId}_${Date.now()}`,
          type: 'tool',
          content: `执行${toolName}${isSuccess ? '成功' : '失败'}`,
          toolName: toolName,
          toolCallId: toolCallId,
          status: isSuccess,
          timestamp: new Date().toLocaleTimeString(),
          toolCall: '', // 没有原始调用参数
          toolResponse: toolResponse
        });
      }
    },
    
    
    // 处理exit消息（对话结束）
    handleExitMessage(data) {
      // 一轮对话结束，重置发送状态
      this.sending = false;
      this.loading = false;
      // 清理未完成的工具调用（如果有）
      if (this.pendingToolCalls.size > 0) {
        console.log('清理未完成的工具调用:', Array.from(this.pendingToolCalls.keys()));
        this.pendingToolCalls.clear();
      }
      console.log('对话轮次结束:', data);
    },
    
    // 处理error消息（错误处理）
    handleErrorMessage(data) {
      // 重置所有状态
      this.sending = false;
      this.loading = false;
      this.currentMessage = '';
      this.currentReasoning = '';
      this.pendingToolCalls.clear(); // 清理待处理队列
      
      // 添加错误消息到聊天界面
      this.addMessage({
        type: 'ai',
        content: `❌ 抱歉，处理您的请求时出现了错误：\n\n${data.object?.message || data.text || '未知错误'}\n\n请稍后重试或重新开始对话。`,
        timestamp: new Date().toLocaleTimeString(),
        isError: true // 标记为错误消息
      });
      
      console.error('WebSocket错误消息:', data);
    },
    
    // 显示工具详情
    showToolDetail(message) {
      if (message.toolCall || message.toolResponse) {
        this.currentToolDetail = {
          toolName: message.toolName || '未知工具',
          status: message.status,
          toolCall: message.toolCall || '',
          toolResponse: message.toolResponse || ''
        };
        this.showToolDetailPopup = true;
      }
    },
    
    // 格式化控制台文本
    formatConsoleText(data) {
      if (!data) return '暂无数据';
      
      // 如果是JSON字符串，尝试格式化
      try {
        const parsed = JSON.parse(data);
        return JSON.stringify(parsed, null, 2);
      } catch (e) {
        // 如果不是JSON，直接返回
        return data;
      }
    },

    // 渲染Markdown内容
    renderMarkdown(text) {
      let html = this.md.render(text || '');
      
      // 为表格添加滚动容器包装
      html = html.replace(
        /<table([^>]*)>/g,
        '<div class="table-wrapper"><table$1>'
      );
      html = html.replace(
        /<\/table>/g,
        '</table></div>'
      );
      
      return html;
    },
    
    // 调整输入框高度
    adjustTextareaHeight() {
      this.$nextTick(() => {
        const textarea = this.$refs.messageInput;
        if (textarea) {
          // 重置高度以获取正确的scrollHeight
          textarea.style.height = 'auto';
          // 设置最小高度和最大高度
          const minHeight = 40; // 最小高度
          const maxHeight = 120; // 最大高度（约3行）
          const scrollHeight = textarea.scrollHeight;
          
          if (scrollHeight > maxHeight) {
            textarea.style.height = maxHeight + 'px';
            textarea.style.overflowY = 'auto';
          } else if (scrollHeight < minHeight) {
            textarea.style.height = minHeight + 'px';
            textarea.style.overflowY = 'hidden';
          } else {
            textarea.style.height = scrollHeight + 'px';
            textarea.style.overflowY = 'hidden';
          }
        }
      });
    },
    
    // 处理键盘事件
    handleKeydown(event) {
      // Shift + Enter = 换行，Enter = 发送
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        this.sendMessage();
      }
    },
    
    
    // 处理连接状态点击
    handleConnectionClick() {
      // 只有未连接时才可以点击重连
      if (!this.wsConnected && !this.reconnecting) {
        this.reconnectWebSocket();
      }
    },
    
    // 重新连接WebSocket
    reconnectWebSocket() {
      if (this.reconnecting) return;
      
      this.reconnecting = true;
      console.log('开始重新连接WebSocket...');
      
      // 先断开现有连接
      this.disconnectWebSocket();
      
      // 延迟重连
      setTimeout(() => {
        this.initWebSocket();
        
        // 设置重连超时
        setTimeout(() => {
          if (!this.wsConnected) {
            this.reconnecting = false;
            showToast({
              type: 'fail',
              message: '重连失败，请检查网络'
            });
          }
        }, 5000); // 5秒超时
        
      }, 1000);
    },
    
    // 切换思维链展开/折叠状态
    toggleReasoning(messageId) {
      const message = this.messages.find(msg => msg.id === messageId);
      if (message && message.hasReasoning) {
        // 切换展开状态，默认为false（折叠）
        message.reasoningExpanded = !message.reasoningExpanded;
      }
    }
  }
};
</script>

<style scoped>
.ai-plus-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden; /* 强制隐藏水平滚动 */
  height: calc(100vh - 54px); /* 只需减去顶部导航栏高度 */
}

.messages-container {
  padding: 16px;
  padding-bottom: 100px; /* 增加底部padding，为固定输入框留出空间 */
  min-height: calc(100vh - 54px);
  overflow-x: hidden; /* 强制隐藏水平滚动 */
}

.message-item {
  margin-bottom: 16px;
}

.user-message, .ai-message {
  max-width: 80%;
  width: 80%; /* 强制固定宽度，防止被内容撑开 */
  margin-bottom: 8px;
  box-sizing: border-box; /* 确保padding不会撑开容器 */
}

.user-message {
  margin-left: auto;
  text-align: right;
}

.user-message .message-content {
  background: #1989fa;
  color: white;
  padding: 10px 12px;
  font-size: 13px;
  border-radius: 18px 18px 4px 18px;
  display: inline-block;
  word-wrap: break-word;
}

.ai-message .message-content {
  background: #f7f8fa;
  color: #323233;
  padding: 10px 12px;
  font-size: 13px;
  border-radius: 18px 18px 18px 4px;
  display: block; /* 改为block，避免inline-block被内容撑开 */
  word-wrap: break-word;
  width: 100%; /* 占满父容器 */
  box-sizing: border-box; /* 确保padding不撑开 */
  overflow: hidden; /* 防止内容溢出 */
}

.ai-message.typing .message-content {
  background: #e8f3ff;
  border: 1px dashed #1989fa;
}

.ai-message.error-message .message-content {
  background: #fff2f0;
  border: 1px solid #ffb3b3;
  color: #ff4d4f;
}

.message-time {
  font-size: 11px;
  color: #969799;
  margin-top: 4px;
}

.user-message .message-time {
  text-align: right;
}

.typing-indicator {
  font-size: 11px;
  color: #1989fa;
  margin-top: 4px;
  font-style: italic;
}

.tool-message {
  margin: 8px 0;
  cursor: pointer;
}

.tool-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid;
  transition: all 0.2s ease;
}

.tool-content.success {
  background: #f0f9f0;
  border-color: #b7eb8f;
}

.tool-content.failed {
  background: #fff2f0;
  border-color: #ffb3b3;
}

.tool-content.loading {
  background: #fff9e6;
  border-color: #ffc107;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
  100% {
    opacity: 1;
  }
}

.tool-content:active {
  transform: scale(0.98);
}

.tool-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  flex: 1;
}

.tool-status {
  color: #07c160;
}

.tool-content.failed .tool-status {
  color: #ff4d4f;
}

.loading-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #969799;
  font-size: 14px;
  margin: 16px 0;
}

/* 导航栏右侧容器 */
.nav-right-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 3px;
  transition: all 0.2s ease;
}

.connection-status.clickable {
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 8px;
  background: rgba(255, 151, 106, 0.1);
}

.connection-status.clickable:hover {
  background: rgba(255, 151, 106, 0.2);
}

.connection-status.clickable:active {
  transform: scale(0.95);
}

.status-text {
  font-size: 10px;
}

/* 设置面板样式 */
.settings-panel {
  background: #fff;
  border-top: 1px solid #ebedf0;
}

.settings-content {
  padding: 16px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #323233;
  font-weight: 500;
}

.new-conversation-btn {
  width: 100%;
  height: 36px;
  border-radius: 18px;
}

.setting-desc {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #969799;
  background: #f7f8fa;
  padding: 8px 12px;
  border-radius: 8px;
  margin-top: 8px;
  line-height: 1.4;
}

/* 工具详情弹窗样式 */
.tool-detail-popup {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tool-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebedf0;
}

.tool-detail-header h3 {
  margin: 0;
  font-size: 18px;
  color: #323233;
}

.tool-detail-header .tool-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
}

.tool-detail-header .tool-status.success {
  color: #07c160;
}

.tool-detail-header .tool-status.failed {
  color: #ee0a24;
}

.tool-detail-content {
  flex: 1;
  overflow-y: auto;
}

.console-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.console-box {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 0;
  max-height: 250px;
  overflow-y: auto;
  position: relative;
}

.console-text {
  color: #00ff00;
  font-family: 'Courier New', Monaco, 'Lucida Console', monospace;
  font-size: 12px;
  line-height: 1.4;
  margin: 0;
  padding: 16px;
  white-space: pre-wrap;
  word-break: break-word;
  background: transparent;
  overflow-wrap: break-word;
}

.console-box::before {
  content: '';
  position: absolute;
  top: 8px;
  left: 12px;
  width: 8px;
  height: 8px;
  background: #00ff00;
  border-radius: 50%;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}


/* 输入容器包装器 */
.input-container-wrapper {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: white;
  border-top: 1px solid #ebedf0;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  /* 确保在键盘弹起时紧贴键盘 */
  padding-bottom: env(safe-area-inset-bottom);
  /* 移动端视口单位，确保跟随键盘 */
  bottom: env(keyboard-inset-height, 0);
}

.input-container {
  display: flex;
  align-items: flex-end;
  padding: 12px 16px;
  background-color: #fff;
  gap: 12px;
}

.input-wrapper {
  flex: 1;
  background: #f7f8fa;
  border-radius: 20px;
  padding: 8px 16px;
  border: 1px solid #ebedf0;
  transition: border-color 0.3s ease;
}

.input-wrapper:focus-within {
  border-color: #1989fa;
  background: #fff;
}

.message-textarea {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 16px;
  line-height: 1.5;
  resize: none;
  color: #323233;
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Segoe UI, Arial, Roboto, 'PingFang SC', 'miui', 'Hiragino Sans GB', 'Microsoft Yahei', sans-serif;
}

.message-textarea::placeholder {
  color: #969799;
}

.send-button {
  min-width: 60px;
  height: 40px;
  border-radius: 20px;
  flex-shrink: 0;
}

/* 思维链样式 */
.reasoning-section {
  margin-bottom: 8px;
  border: 1px solid #e8f3ff;
  border-radius: 8px;
  background: #f8fcff;
  overflow: hidden;
}

.reasoning-section.current {
  border-color: #1989fa;
  background: #e8f3ff;
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f0f9ff;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease;
}

.reasoning-section.current .reasoning-header {
  background: #dbeafe;
}

.reasoning-header:hover {
  background: #e8f3ff;
}

.reasoning-title {
  font-size: 12px;
  color: #1989fa;
  font-weight: 500;
  flex: 1;
}

.reasoning-arrow {
  color: #969799;
  transition: transform 0.2s ease;
}

.reasoning-content {
  padding: 0;
  animation: fadeIn 0.2s ease;
}

.reasoning-text {
  padding: 12px;
  font-size: 13px;
  line-height: 1.5;
  color: #646566;
  font-style: italic;
  white-space: pre-wrap;
  word-break: break-word;
  background: #fafbfc;
  border-top: 1px solid #eee;
}

.reasoning-section.current .reasoning-text {
  background: #f5f9ff;
  border-top-color: #dbeafe;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

/* 表格滚动容器 - 包装表格实现内部滚动 */
.message-content :deep(.table-wrapper) {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin: 12px 0;
}

/* 美化表格容器滚动条 */
.message-content :deep(.table-wrapper)::-webkit-scrollbar {
  height: 6px;
}

.message-content :deep(.table-wrapper)::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 3px;
}

.message-content :deep(.table-wrapper)::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.message-content :deep(.table-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #a6acb8;
}

/* Markdown 表格样式 */
.message-content :deep(table) {
  width: auto; /* 改为auto，让表格根据内容调整 */
  min-width: 300px; /* 降低最小宽度 */
  border-collapse: collapse;
  background: #fff;
  margin: 0; /* 由父容器控制外边距 */
  border-radius: 0; /* 由父容器控制圆角 */
  box-shadow: none; /* 由父容器控制阴影 */
}

.message-content :deep(th) {
  background: #f7f8fa;
  color: #323233;
  font-weight: 600;
  text-align: left;
  padding: 8px 12px; /* 减少padding节省空间 */
  border: 1px solid #ebedf0;
  font-size: 13px; /* 稍微减小字体 */
  white-space: nowrap; /* 表头不换行，保持紧凑 */
  min-width: 60px; /* 减少最小列宽 */
}

.message-content :deep(td) {
  padding: 8px 12px; /* 减少padding节省空间 */
  border: 1px solid #ebedf0;
  color: #646566;
  font-size: 13px; /* 稍微减小字体 */
  line-height: 1.4;
  white-space: nowrap; /* 单元格内容不换行，让滚动生效 */
  min-width: 60px; /* 减少最小列宽 */
  word-wrap: break-word; /* 长单词自动换行 */
}

.message-content :deep(tr:nth-child(even)) {
  background: #fafbfc;
}

.message-content :deep(tr:hover) {
  background: #f2f3f5;
}

/* Markdown 其他元素美化 */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3),
.message-content :deep(h4),
.message-content :deep(h5),
.message-content :deep(h6) {
  color: #323233;
  margin: 16px 0 8px 0;
  font-weight: 600;
}

.message-content :deep(h1) {
  font-size: 20px;
  border-bottom: 2px solid #1989fa;
  padding-bottom: 4px;
}

.message-content :deep(h2) {
  font-size: 18px;
  border-bottom: 1px solid #ebedf0;
  padding-bottom: 4px;
}

.message-content :deep(h3) {
  font-size: 16px;
}

.message-content :deep(code) {
  background: #f7f8fa;
  color: #e74c3c;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', Monaco, monospace;
  font-size: 13px;
}

.message-content :deep(pre) {
  background: #f7f8fa;
  border: 1px solid #ebedf0;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-content :deep(pre code) {
  background: none;
  color: #323233;
  padding: 0;
}

.message-content :deep(blockquote) {
  border-left: 4px solid #1989fa;
  background: #f8fcff;
  padding: 12px 16px;
  margin: 12px 0;
  color: #646566;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.message-content :deep(li) {
  margin: 4px 0;
  line-height: 1.6;
}
</style>