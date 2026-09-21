<template>
  <div class="chat-container">
    <div class="header">
      <h1>🛒 电商客服 RAG 智能问答系统</h1>
      <p>输入客户问题，系统会自动检索政策文档并生成回答。</p>
    </div>

    <div class="chat-history">
      <div v-if="messages.length === 0" class="empty-tip">
        试试问："退货需要什么条件？" 或 "物流多久能到？"
      </div>

      <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
        <div class="bubble">
          {{ msg.content }}<span v-if="msg.streaming" class="cursor">▍</span>
        </div>
        <div v-if="msg.references && msg.references.length" class="references">
          <div class="ref-title">📚 引用来源：</div>
          <div v-for="(ref, i) in msg.references" :key="i" class="ref-item">
            [{{ i + 1 }}] {{ ref.source }}（相似度 {{ ref.score.toFixed(4) }}）
          </div>
        </div>
      </div>

      <div v-if="loading && !isStreamingActive" class="loading-tip">
        <el-icon class="is-loading"><Loading /></el-icon> 正在检索文档...
      </div>
    </div>

    <div class="input-area">
      <el-input
        v-model="question"
        placeholder="输入客户问题..."
        @keyup.enter="submit"
        :disabled="loading"
        size="large"
      />
      <el-button
        type="primary"
        @click="submit"
        :loading="loading"
        size="large"
      >提交</el-button>
      <el-button @click="clear" :disabled="loading" size="large">清空</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const question = ref('')
const messages = ref([])
const loading = ref(false)
const isStreamingActive = ref(false)

const submit = async () => {
  if (!question.value.trim()) return
  const q = question.value
  messages.value.push({ role: 'user', content: q })
  question.value = ''
  loading.value = true
  isStreamingActive.value = false

  // 先插入一个空的 assistant 消息，边收边更新
  const assistantMsg = { role: 'assistant', content: '', references: [], streaming: true }
  messages.value.push(assistantMsg)
  const msgIndex = messages.value.length - 1

  try {
    const response = await fetch('/api/query/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, top_k: 2 })
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE 消息以 \n\n 分隔
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith('data:')) continue

        const data = line.slice(5).trim()
        if (data === '[DONE]') continue

        try {
          const parsed = JSON.parse(data)

          if (parsed.type === 'content') {
            // 收到第一个内容片段时，标记流式已启动
            if (!isStreamingActive.value) {
              isStreamingActive.value = true
            }
            messages.value[msgIndex].content += parsed.text
          } else if (parsed.type === 'references') {
            messages.value[msgIndex].references = parsed.references || []
          } else if (parsed.type === 'error') {
            messages.value[msgIndex].content = '[ERROR] ' + parsed.message
          }
        } catch (e) {
          console.error('Parse SSE failed:', e, data)
        }
      }
    }
  } catch (e) {
    messages.value[msgIndex].content = '[ERROR] ' + e.message
  } finally {
    messages.value[msgIndex].streaming = false
    loading.value = false
    isStreamingActive.value = false
  }
}

const clear = () => {
  messages.value = []
  question.value = ''
}
</script>

<style scoped>
.chat-container { max-width: 900px; margin: 0 auto; padding: 20px; font-family: system-ui; }
.header { text-align: center; margin-bottom: 20px; }
.header h1 { margin: 0; }
.header p { color: #666; margin: 5px 0 0; }
.chat-history {
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 15px;
  background: #fafafa;
}
.empty-tip { color: #999; text-align: center; padding: 50px 0; }
.message { margin: 15px 0; display: flex; flex-direction: column; }
.message.user { align-items: flex-end; }
.message.assistant { align-items: flex-start; }
.bubble {
  padding: 12px 16px;
  border-radius: 10px;
  max-width: 75%;
  white-space: pre-wrap;
  line-height: 1.6;
}
.message.user .bubble { background: #409EFF; color: white; }
.message.assistant .bubble { background: white; color: #333; border: 1px solid #eee; }

/* ⚠️ 打字机光标 */
.cursor {
  display: inline-block;
  color: #409EFF;
  animation: blink 1s infinite;
  margin-left: 2px;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.references {
  font-size: 12px;
  color: #666;
  margin-top: 6px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  max-width: 75%;
}
.ref-title { font-weight: bold; margin-bottom: 4px; }
.ref-item { line-height: 1.6; }
.loading-tip { color: #409EFF; padding: 10px; text-align: center; }
.input-area { display: flex; gap: 10px; }
</style>