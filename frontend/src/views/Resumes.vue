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

    <!-- 查看简历对话框 - PDF预览 -->
    <el-dialog
      v-model="showViewDialog"
      :title="currentResume?.name || '简历预览'"
      width="85%"
      top="2vh"
      destroy-on-close
    >
      <div class="resume-viewer" v-if="currentResume">
        <!-- 基本信息 -->
        <div class="preview-header">
          <span class="file-info">
            {{ currentResume.name }} ({{ currentResume.file_type?.toUpperCase() }})
          </span>
        </div>

        <!-- PDF预览区域 -->
        <div class="pdf-container" v-loading="loadingPreview">
          <iframe
            v-if="pdfUrl"
            :src="pdfUrl"
            class="pdf-iframe"
            frameborder="0"
          ></iframe>

          <!-- 错误提示 -->
          <el-alert
            v-if="previewError"
            type="error"
            :title="previewError"
            show-icon
            :closable="false"
          />
        </div>
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
import { ref, reactive, onMounted } from 'vue'
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
const pdfUrl = ref('')
const loadingPreview = ref(false)
const previewError = ref('')
const authStore = useAuthStore()

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

const viewResume = (resume: Resume) => {
  showViewDialog.value = true
  currentResume.value = resume
  loadingPreview.value = true
  previewError.value = ''
  pdfUrl.value = ''

  // 构建PDF预览URL（添加token参数用于认证）
  const token = authStore.token
  pdfUrl.value = `/api/resumes/${resume.id}/pdf?token=${token}`
  loadingPreview.value = false
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
  display: flex;
  flex-direction: column;
  height: calc(80vh - 120px);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 10px;
}

.file-info {
  font-weight: 500;
  color: #303133;
}

.pdf-container {
  flex: 1;
  min-height: 500px;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  min-height: 500px;
}
</style>