<template>
  <div class="resumes-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>简历管理</span>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Plus /></el-icon>
            上传简历
          </el-button>
        </div>
      </template>

      <el-table :data="resumes" v-loading="loading">
        <el-table-column prop="name" label="简历名称">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewResume(row)">
              {{ row.name }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="文件类型">
          <template #default="{ row }">
            <el-tag>{{ row.file_type?.toUpperCase() || '未知' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" style="margin-right: 5px">{{ tag }}</el-tag>
            <span v-if="!row.tags?.length">无标签</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_default" label="默认">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success">默认</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="viewResume(row)">
              查看
            </el-button>
            <el-button size="small" @click="setDefault(row.id)" v-if="!row.is_default">
              设为默认
            </el-button>
            <el-button size="small" type="danger" @click="deleteResume(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- PDF预览对话框 -->
    <el-dialog
      v-model="showViewDialog"
      title="附件预览"
      width="85%"
      top="2vh"
      destroy-on-close
      class="pdf-preview-dialog"
    >
      <div class="pdf-preview-container" v-if="currentResume">
        <!-- 标题栏 -->
        <div class="preview-header-bar">
          <div class="header-left">
            <span class="file-name">{{ currentResume.name }}</span>
            <el-tag size="small" type="info">{{ currentResume.file_type?.toUpperCase() }}</el-tag>
          </div>
          <div class="header-right">
            <el-button type="primary" size="small">
              <el-icon><Edit /></el-icon>
              编辑（需要换新样式）
            </el-button>
          </div>
        </div>

        <!-- 工具栏 -->
        <div class="preview-toolbar">
          <!-- 页码导航 -->
          <div class="toolbar-section">
            <el-button-group>
              <el-button size="small" @click="prevPage" :disabled="currentPage <= 1">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <el-button size="small" class="page-info" disabled>
                {{ currentPage }} / {{ totalPages }}
              </el-button>
              <el-button size="small" @click="nextPage" :disabled="currentPage >= totalPages">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </el-button-group>
          </div>

          <el-divider direction="vertical" />

          <!-- 缩放控制 -->
          <div class="toolbar-section">
            <el-button-group>
              <el-button size="small" @click="zoomOut" :disabled="scale <= 0.5">
                <el-icon><ZoomOut /></el-icon>
              </el-button>
              <el-button size="small" class="zoom-info" disabled>
                {{ Math.round(scale * 100) }}%
              </el-button>
              <el-button size="small" @click="zoomIn" :disabled="scale >= 3">
                <el-icon><ZoomIn /></el-icon>
              </el-button>
            </el-button-group>
          </div>

          <el-divider direction="vertical" />

          <!-- 页面适应 -->
          <div class="toolbar-section">
            <el-button-group>
              <el-button size="small" @click="fitWidth" :type="fitMode === 'width' ? 'primary' : ''">
                <el-icon><ScaleToOriginal /></el-icon>
              </el-button>
              <el-button size="small" @click="fitPage" :type="fitMode === 'page' ? 'primary' : ''">
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </el-button-group>
          </div>

          <div class="toolbar-spacer"></div>

          <!-- 打印下载 -->
          <div class="toolbar-section">
            <el-button-group>
              <el-button size="small" @click="printPDF">
                <el-icon><Printer /></el-icon>
              </el-button>
              <el-button size="small" @click="downloadResume(currentResume?.id)">
                <el-icon><Download /></el-icon>
              </el-button>
            </el-button-group>
          </div>
        </div>

        <!-- PDF显示区域 -->
        <div class="pdf-viewer" ref="pdfViewerRef" v-loading="pdfLoading">
          <div class="pdf-canvas-container" :style="canvasContainerStyle">
            <canvas ref="pdfCanvas" class="pdf-page"></canvas>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showViewDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传简历" width="500px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="简历名称">
          <el-input v-model="uploadForm.name" placeholder="请输入简历名称" />
        </el-form-item>
        <el-form-item label="简历文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.doc,.docx"
            :on-change="handleFileChange"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 PDF、Word 格式</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="uploadForm.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="uploadForm.isDefault" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadResume" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { request } from '@/utils/api'
import { useAuthStore } from '@/stores/auth'
import * as pdfjsLib from 'pdfjs-dist'
import {
  Plus,
  ArrowLeft,
  ArrowRight,
  ZoomIn,
  ZoomOut,
  FullScreen,
  ScaleToOriginal,
  Printer,
  Download,
  Edit
} from '@element-plus/icons-vue'

// 设置pdf.js worker路径
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`

interface Resume {
  id: string
  name: string
  file_type: string
  tags: string[]
  is_default: boolean
  created_at: string
}

const resumes = ref<Resume[]>([])
const loading = ref(false)
const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadRef = ref()
const selectedFile = ref<File | null>(null)

// 上传表单
const uploadForm = reactive({
  name: '',
  tags: '',
  isDefault: false
})

// 查看简历相关（PDF预览）
const showViewDialog = ref(false)
const currentResume = ref<Resume | null>(null)
const authStore = useAuthStore()

// PDF相关状态
const pdfLoading = ref(false)
const pdfDocument = ref<pdfjsLib.PDFDocumentProxy | null>(null)
const currentPage = ref(1)
const totalPages = ref(1)
const scale = ref(1.0)
const fitMode = ref<'none' | 'width' | 'page'>('none')
const pdfCanvas = ref<HTMLCanvasElement | null>(null)
const pdfViewerRef = ref<HTMLElement | null>(null)

// 画布容器样式
const canvasContainerStyle = computed(() => {
  return {
    transform: `scale(${scale.value})`,
    transformOrigin: 'center top'
  }
})

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const handleFileChange = (file: { raw: File }) => {
  selectedFile.value = file.raw
}

const loadResumes = async () => {
  loading.value = true
  try {
    const data = await request.get<{ items: Resume[] }>('/resumes')
    resumes.value = data.items
  } catch (error) {
    console.error('获取简历列表失败', error)
  } finally {
    loading.value = false
  }
}

// 查看简历 - 使用pdf.js预览
const viewResume = async (resume: Resume) => {
  showViewDialog.value = true
  currentResume.value = resume
  pdfLoading.value = true
  currentPage.value = 1
  totalPages.value = 1
  scale.value = 1.0
  fitMode.value = 'none'

  try {
    const token = authStore.token
    const pdfUrl = `/api/resumes/${resume.id}/pdf?token=${token}`

    // 加载PDF文档
    const loadingTask = pdfjsLib.getDocument(pdfUrl)
    pdfDocument.value = await loadingTask.promise
    totalPages.value = pdfDocument.value.numPages

    // 渲染第一页
    await nextTick()
    await renderPage(currentPage.value)
  } catch (error) {
    console.error('加载PDF失败', error)
    ElMessage.error('加载PDF失败，请稍后重试')
  } finally {
    pdfLoading.value = false
  }
}

// 渲染指定页面
const renderPage = async (pageNum: number) => {
  if (!pdfDocument.value || !pdfCanvas.value) return

  try {
    const page = await pdfDocument.value.getPage(pageNum)
    const canvas = pdfCanvas.value
    const context = canvas.getContext('2d')
    if (!context) return

    // 获取视口
    const viewport = page.getViewport({ scale: 1.0 })

    // 根据适应模式调整缩放
    let renderScale = scale.value
    if (fitMode.value === 'width' && pdfViewerRef.value) {
      const containerWidth = pdfViewerRef.value.clientWidth - 40
      renderScale = containerWidth / viewport.width
    } else if (fitMode.value === 'page' && pdfViewerRef.value) {
      const containerWidth = pdfViewerRef.value.clientWidth - 40
      const containerHeight = pdfViewerRef.value.clientHeight - 40
      const scaleX = containerWidth / viewport.width
      const scaleY = containerHeight / viewport.height
      renderScale = Math.min(scaleX, scaleY)
    }

    const scaledViewport = page.getViewport({ scale: renderScale })

    // 设置canvas尺寸
    canvas.width = scaledViewport.width
    canvas.height = scaledViewport.height

    // 渲染页面
    const renderContext = {
      canvasContext: context,
      viewport: scaledViewport
    }
    await page.render(renderContext).promise
  } catch (error) {
    console.error('渲染页面失败', error)
  }
}

// 页面导航
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    renderPage(currentPage.value)
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    renderPage(currentPage.value)
  }
}

// 缩放控制
const zoomIn = () => {
  if (scale.value < 3) {
    scale.value += 0.25
    fitMode.value = 'none'
    renderPage(currentPage.value)
  }
}

const zoomOut = () => {
  if (scale.value > 0.5) {
    scale.value -= 0.25
    fitMode.value = 'none'
    renderPage(currentPage.value)
  }
}

// 页面适应
const fitWidth = () => {
  fitMode.value = fitMode.value === 'width' ? 'none' : 'width'
  renderPage(currentPage.value)
}

const fitPage = () => {
  fitMode.value = fitMode.value === 'page' ? 'none' : 'page'
  renderPage(currentPage.value)
}

// 打印PDF
const printPDF = () => {
  if (!currentResume.value) return
  const token = authStore.token
  const pdfUrl = `/api/resumes/${currentResume.value.id}/pdf?token=${token}`

  // 在新窗口打开PDF并打印
  const printWindow = window.open(pdfUrl, '_blank')
  if (printWindow) {
    printWindow.onload = () => {
      printWindow.print()
    }
  }
}

// 下载简历
const downloadResume = async (resumeId: string | undefined) => {
  if (!resumeId) return
  try {
    const token = authStore.token
    const url = `/api/resumes/${resumeId}/download?token=${token}`
    window.open(url, '_blank')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 上传简历
const uploadResume = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  if (!uploadForm.name) {
    ElMessage.warning('请输入简历名称')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('name', uploadForm.name)
    formData.append('file', selectedFile.value)
    if (uploadForm.tags) {
      formData.append('tags', uploadForm.tags)
    }
    formData.append('is_default', String(uploadForm.isDefault))

    await request.post('/resumes', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    ElMessage.success('上传成功')
    showUploadDialog.value = false
    uploadForm.name = ''
    uploadForm.tags = ''
    uploadForm.isDefault = false
    selectedFile.value = null
    loadResumes()
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const setDefault = async (id: string) => {
  try {
    await request.put(`/resumes/${id}/default`)
    ElMessage.success('已设为默认')
    loadResumes()
  } catch (error) {
    ElMessage.error('设置失败')
  }
}

const deleteResume = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这份简历吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/resumes/${id}`)
    ElMessage.success('删除成功')
    loadResumes()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 监听对话框关闭，清理PDF资源
watch(showViewDialog, (newVal) => {
  if (!newVal && pdfDocument.value) {
    pdfDocument.value.destroy()
    pdfDocument.value = null
  }
})

onMounted(() => {
  loadResumes()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* PDF预览对话框样式 */
:deep(.pdf-preview-dialog .el-dialog__body) {
  padding: 0;
}

.pdf-preview-container {
  display: flex;
  flex-direction: column;
  height: calc(80vh - 120px);
  background: #f5f7fa;
}

/* 标题栏 */
.preview-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

/* 工具栏 */
.preview-toolbar {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  gap: 10px;
}

.toolbar-section {
  display: flex;
  align-items: center;
}

.toolbar-spacer {
  flex: 1;
}

.page-info {
  min-width: 60px;
  text-align: center;
}

.zoom-info {
  min-width: 50px;
  text-align: center;
}

/* PDF查看区域 */
.pdf-viewer {
  flex: 1;
  overflow: auto;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.pdf-canvas-container {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.pdf-page {
  display: block;
}
</style>