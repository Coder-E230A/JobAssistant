<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="今日投递" :value="stats.todayApplied" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="总投递数" :value="stats.totalApplied" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="已查看" :value="stats.viewed" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="面试邀请" :value="stats.interview" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card class="action-card">
      <template #header>
        <span>快捷操作</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-button type="primary" @click="$router.push('/accounts')">
            <el-icon><Link /></el-icon>
            绑定平台账号
          </el-button>
        </el-col>
        <el-col :span="8">
          <el-button type="success" @click="$router.push('/resumes')">
            <el-icon><Document /></el-icon>
            上传简历
          </el-button>
        </el-col>
        <el-col :span="8">
          <el-button type="warning" @click="$router.push('/rules')">
            <el-icon><Filter /></el-icon>
            配置筛选规则
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 最近投递 -->
    <el-card class="recent-card">
      <template #header>
        <span>最近投递</span>
      </template>
      <el-table :data="recentApplications" v-loading="loading">
        <el-table-column prop="job_title" label="岗位" />
        <el-table-column prop="company" label="公司" />
        <el-table-column prop="platform" label="平台" />
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
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { request } from '@/utils/api'

interface Stats {
  todayApplied: number
  totalApplied: number
  viewed: number
  interview: number
  pending: number
  rejected: number
}

interface Application {
  id: string
  job_title: string
  company: string
  platform: string
  status: string
  applied_at: string
}

const stats = ref<Stats>({
  todayApplied: 0,
  totalApplied: 0,
  viewed: 0,
  interview: 0,
  pending: 0,
  rejected: 0
})

const recentApplications = ref<Application[]>([])
const loading = ref(false)

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

onMounted(async () => {
  loading.value = true
  try {
    // 获取统计数据
    const statsData = await request.get<Stats>('/applications/stats')
    stats.value = statsData

    // 获取最近投递
    const appsData = await request.get<{ items: Application[] }>('/applications?limit=10')
    recentApplications.value = appsData.items
  } catch (error) {
    console.error('获取数据失败', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stat-card {
  text-align: center;
}

.action-card {
  margin-top: 20px;
}

.recent-card {
  margin-top: 20px;
}
</style>