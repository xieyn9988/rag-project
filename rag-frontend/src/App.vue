<template>
  <div class="chat-container">
    <div class="header">
      <h1>🛒 电商客服 RAG 智能问答系统</h1>
      <p>输入客户问题，系统会自动检索政策文档并生成回答。</p>
    </div>

    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- ========== Tab 1：问答 ========== -->
      <el-tab-pane label="💬 问答" name="chat">
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
          <el-button type="primary" @click="submit" :loading="loading" size="large">提交</el-button>
          <el-button @click="clear" :disabled="loading" size="large">清空</el-button>
        </div>
      </el-tab-pane>

      <!-- ========== Tab 2：上传资料 ========== -->
      <el-tab-pane label="📤 上传资料" name="upload">
        <div class="upload-area">
          <el-alert
            title="上传 TXT / MD / PDF 文档，系统会自动保存并重建索引。上传后即可立即问答。"
            type="info"
            :closable="false"
            style="margin-bottom: 20px;"
          />

          <el-upload
            drag
            multiple
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="fileList"
            accept=".txt,.md,.pdf"
            style="margin-bottom: 20px;"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 TXT / MD / PDF 格式，可多选
              </div>
            </template>
          </el-upload>

          <el-button
            type="primary"
            @click="submitUpload"
            :loading="uploading"
            :disabled="fileList.length === 0"
            size="large"
          >
            上传并重建索引（{{ fileList.length }} 个文件）
          </el-button>

          <div v-if="uploadResult" class="upload-result">
            <el-alert
              :title="uploadResult.title"
              :type="uploadResult.type"
              :closable="false"
              show-icon
            >
              <div v-for="(line, i) in uploadResult.lines" :key="i">{{ line }}</div>
            </el-alert>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Loading, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('chat')

// ========== 问答相关 ==========
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

  const assistantMsg = { role: 'assistant', content: '', references: [], streaming: true }
  messages.value.push(assistantMsg)
  const msgIndex = messages.value.length - 1

  try {
    const response = await fetch('/api/query/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, top_k: 2 })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
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
            if (!isStreamingActive.value) isStreamingActive.value = true
            messages.value[msgIndex].content += parsed.text
          } else if (parsed.type === 'references') {
            messages.value[msgIndex].references = parsed.references || []
          } else if (parsed.type === 'error') {
            messages.value[msgIndex].content = '[ERROR] ' + parsed.message
          }
        } catch (e) {
          console.error('Parse SSE failed:', e)
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

// ========== 上传相关 ==========
const fileList = ref([])
const uploading = ref(false)
const uploadResult = ref(null)

const handleFileChange = (file, files) => {
  fileList.value = files
}

const handleFileRemove = (file, files) => {
  fileList.value = files
}

const submitUpload = async () => {
  if (fileList.value.length === 0) return

  const formData = new FormData()
  fileList.value.forEach(f => {
    formData.append('files', f.raw)
  })

  uploading.value = true
  uploadResult.value = null

  try {
    const res = await fetch('/api/ingest/upload', {
      method: 'POST',
      body: formData
    })

    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()

    uploadResult.value = {
      type: 'success',
      title: `上传成功！当前知识库共 ${data.total} 个文本块`,
      lines: [
        `✅ 成功上传：${data.uploaded.join('、')}`,
        data.skipped.length > 0 ? `⚠️ 已跳过：${data.skipped.join('、')}` : '',
        `⏱ 耗时：${data.elapsed_ms} ms`
      ].filter(Boolean)
    }

    ElMessage.success('上传成功，知识库已更新！')

    // 清空文件列表
    fileList.value = []

    // 提示切换到问答 Tab
    setTimeout(() => {
      activeTab.value = 'chat'
    }, 1500)
  } catch (e) {
    uploadResult.value = {
      type: 'error',
      title: '上传失败',
      lines: [e.message]
    }
    ElMessage.error('上传失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.chat-container { max-width: 900px; margin: 0 auto; padding: 20px; font-family: system-ui; }
.header { text-align: center; margin-bottom: 20px; }
.header h1 { margin: 0; }
.header p { color: #666; margin: 5px 0 0; }
.main-tabs { margin-top: 20px; }

/* 聊天区 */
.chat-history {
  min-height: 400px;
  max-height: 500px;
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

/* 上传区 */
.upload-area { padding: 20px 0; }
.upload-result { margin-top: 20px; }
</style>