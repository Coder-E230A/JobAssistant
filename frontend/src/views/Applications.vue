<template>
  <div class="applications-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>投递记录</span>
          <div class="filters">
            <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px">
              <el-option label="已投递" value="applied" />
              <el-option label="已查看" value="viewed" />
              <el-option label="面试邀请" value="interview" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
            <el-select v-model="platformFilter" placeholder="平台筛选" clearable style="width: 120px">
              <el-option label="BOSS直聘" value="boss" />
            </el-select>
          </div>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-statistic title="总投递" :value="stats.total_applied" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="待查看" :value="stats.pending" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="已查看" :value="stats.viewed" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="面试邀请" :value="stats.interview" />
        </el-col>
      </el-row>

      <el-table :data="applications" v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="job_title" label="岗位" />
        <el-table-column prop="company" label="公司" />
        <el-table-column prop="platform" label="平台" />
        <el-table-column prop="resume_name" label="使用简历" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="applied_at" label="投递时间">
          <template #default="{ row }">
            {{ formatDate(row.applied_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="updateStatus(row.id, 'viewed')" v-if="row.status === 'applied'">
              已查看
            </el-button>
            <el-button size="small" type="success" @click="updateStatus(row.id, 'interview')" v-if="row.status === 'viewed'">
              面试
            </el-button>
            <el-button size="small" type="danger" @click="updateStatus(row.id, 'rejected')" v-if="row.status !== 'rejected'">
              拒绝
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { request } from '@/utils/api'

interface Application {
  id: string
  job_id: string
  job_title: string
  company: string
  platform: string
  resume_name: string
  status: string
  applied_at: string
}

interface Stats {
  total_applied: number
  pending: number
  viewed: number
  interview: number
  rejected: number
}

const applications = ref<Application[]>([])
const stats = ref<Stats>({
  total_applied: 0,
  pending: 0,
  viewed: 0,
  interview: 0,
  rejected: 0
})
const loading = ref(false)
const statusFilter = ref('')
const platformFilter = ref('')

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    applied: 'info',
    viewed: 'primary',
    interview: 'success',
    rejected: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    applied: '已投递',
    viewed: '已查看',
    interview: '面试邀请',
    rejected: '已拒绝'
  }
  return texts[status] || status
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const loadApplications = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (statusFilter.value) params.append('status', statusFilter.value)
    if (platformFilter.value) params.append('platform', platformFilter.value)

    const data = await request.get<{ items: Application[] }>(`/applications?${params.toString()}`)
    applications.value = data.items
  } catch (error) {
    console.error('获取投递记录失败', error)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const data = await request.get<Stats>('/applications/stats')
    stats.value = data
  } catch (error) {
    console.error('获取统计数据失败', error)
  }
}

const updateStatus = async (id: string, status: string) => {
  try {
    await request.put(`/applications/${id}/status?status=${status}`)
    ElMessage.success('状态已更新')
    loadApplications()
    loadStats()
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

watch([statusFilter, platformFilter], () => {
  loadApplications()
})

onMounted(() => {
  loadApplications()
  loadStats()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  display: flex;
  gap: 10px;
}

.stats-row {
  padding: 20px 0;
  border-bottom: 1px solid #ebeef5;
}
</style>