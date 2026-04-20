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

    <!-- 查看简历对话框 -->
    <el-dialog
      v-model="showViewDialog"
      :title="currentResume?.name || '简历预览'"
      width="80%"
      top="3vh"
    >
      <div class="resume-viewer" v-if="currentResume" v-loading="loadingPreview">
        <!-- 基本信息 -->
        <div class="preview-header">
          <span class="file-info">
            {{ currentResume.name }} ({{ currentResume.file_type?.toUpperCase() }})
          </span>
          <span class="page-info" v-if="previewData">
            共 {{ previewData.total_pages }} 页
          </span>
        </div>

        <!-- 简历图片预览 -->
        <div class="preview-images" v-if="previewData && previewData.pages.length > 0">
          <div class="page-navigation" v-if="previewData.total_pages > 1">
            <el-button-group>
              <el-button @click="prevPage" :disabled="currentPage <= 1">
                上一页
              </el-button>
              <el-button @click="nextPage" :disabled="currentPage >= previewData.total_pages">
                下一页
              </el-button>
            </el-button-group>
            <span class="current-page">第 {{ currentPage }} / {{ previewData.total_pages }} 页</span>
          </div>

          <!-- 图片显示区域 -->
          <div class="image-container">
            <img
              :src="currentPageUrl"
              :alt="`简历第 ${currentPage} 页`"
              class="preview-image"
              @click="openFullImage"
            />
          </div>

          <!-- 页面缩略图（多页时显示） -->
          <div class="page-thumbnails" v-if="previewData.total_pages > 1">
            <div
              v-for="page in previewData.pages"
              :key="page.page_number"
              class="thumbnail-item"
              :class="{ active: currentPage === page.page_number }"
              @click="currentPage = page.page_number"
            >
              <img :src="getUrlWithToken(page.image_url)" :alt="`第 ${page.page_number} 页`" class="thumbnail-image" />
              <span class="thumbnail-label">{{ page.page_number }}</span>
            </div>
          </div>
        </div>

        <!-- 错误提示 -->
        <el-alert
          v-if="previewError"
          type="error"
          :title="previewError"
          show-icon
          :closable="false"
        />
      </div>

      <template #footer>
        <el-button @click="downloadResume(currentResume?.id)">
          下载原文件
        </el-button>
        <el-button type="primary" @click="showViewDialog = false">关闭</el-button>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { request } from '@/utils/api'
import { useAuthStore } from '@/stores/auth'

interface Resume {
  id: string
  name: string
  file_type: string
  tags: string[]
  is_default: boolean
  created_at: string
}

interface PreviewPage {
  page_number: number
  image_url: string
}

interface PreviewData {
  resume_name: string
  file_type: string
  total_pages: number
  pages: PreviewPage[]
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

// 查看简历相关（图片预览）
const showViewDialog = ref(false)
const currentResume = ref<Resume | null>(null)
const previewData = ref<PreviewData | null>(null)
const currentPage = ref(1)
const loadingPreview = ref(false)
const previewError = ref('')
const authStore = useAuthStore()

// 计算当前页面的图片URL（添加token参数用于认证）
const currentPageUrl = computed(() => {
  if (!previewData.value || !currentResume.value) return ''
  const page = previewData.value.pages.find(p => p.page_number === currentPage.value)
  if (!page) return ''
  return getUrlWithToken(page.image_url)
})

// 为URL添加token认证参数
const getUrlWithToken = (url: string) => {
  const token = authStore.token
  return `${url}?token=${token}`
}

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

const viewResume = async (resume: Resume) => {
  showViewDialog.value = true
  currentResume.value = resume
  loadingPreview.value = true
  previewData.value = null
  previewError.value = ''
  currentPage.value = 1

  try {
    // 获取简历预览图片列表
    const data = await request.get<PreviewData>(`/resumes/${resume.id}/preview`)
    previewData.value = data
  } catch (error: any) {
    console.error('获取简历预览失败', error)
    previewError.value = error.response?.data?.detail || '获取预览图片失败，请稍后重试'
  } finally {
    loadingPreview.value = false
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (previewData.value && currentPage.value < previewData.value.total_pages) {
    currentPage.value++
  }
}

const openFullImage = () => {
  // 在新窗口打开完整图片
  if (currentPageUrl.value) {
    window.open(currentPageUrl.value, '_blank')
  }
}

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

.resume-viewer {
  padding: 10px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 15px;
}

.file-info {
  font-weight: 500;
  color: #303133;
}

.page-info {
  color: #909399;
}

.preview-images {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.page-navigation {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px 0;
}

.current-page {
  color: #606266;
}

.image-container {
  display: flex;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  min-height: 300px;
}

.preview-image {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
  cursor: pointer;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.preview-image:hover {
  transform: scale(1.02);
}

.page-thumbnails {
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 15px 0;
  overflow-x: auto;
}

.thumbnail-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.thumbnail-item:hover {
  background: #f0f2f5;
}

.thumbnail-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.thumbnail-image {
  width: 60px;
  height: 80px;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.thumbnail-label {
  margin-top: 5px;
  font-size: 12px;
  color: #606266;
}
</style>