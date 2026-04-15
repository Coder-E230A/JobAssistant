<template>
  <div class="jobs-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>岗位搜索</span>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keywords" placeholder="请输入搜索关键词" />
        </el-form-item>
        <el-form-item label="城市">
          <el-select v-model="searchForm.location" placeholder="选择城市" clearable>
            <el-option label="北京" value="北京" />
            <el-option label="上海" value="上海" />
            <el-option label="广州" value="广州" />
            <el-option label="深圳" value="深圳" />
            <el-option label="杭州" value="杭州" />
            <el-option label="成都" value="成都" />
          </el-select>
        </el-form-item>
        <el-form-item label="薪资">
          <el-col :span="11">
            <el-input-number v-model="searchForm.salary_min" :min="0" placeholder="最低" size="small" />
          </el-col>
          <el-col :span="2" style="text-align: center">-</el-col>
          <el-col :span="11">
            <el-input-number v-model="searchForm.salary_max" :min="0" placeholder="最高" size="small" />
          </el-col>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchJobs" :loading="searching">搜索</el-button>
        </el-form-item>
      </el-form>

      <!-- 搜索结果 -->
      <el-table :data="jobs" v-loading="searching" style="margin-top: 20px">
        <el-table-column prop="title" label="岗位" />
        <el-table-column prop="company" label="公司" />
        <el-table-column prop="salary_text" label="薪资" />
        <el-table-column prop="location" label="地点" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="applyJob(row)">投递</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 批量投递 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>批量投递</span>
      </template>
      <el-form :model="batchForm" inline>
        <el-form-item label="选择规则">
          <el-select v-model="batchForm.ruleId" placeholder="选择筛选规则">
            <el-option v-for="rule in rules" :key="rule.id" :label="rule.name" :value="rule.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="startBatchDelivery" :loading="batching">
            开始投递
          </el-button>
        </el-form-item>
      </el-form>
      <el-alert v-if="batchResult" :title="batchResult.message" type="info" style="margin-top: 10px" />
    </el-card>

    <!-- 已保存岗位 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>已保存岗位</span>
      </template>
      <el-table :data="savedJobs" v-loading="loadingSaved">
        <el-table-column prop="title" label="岗位" />
        <el-table-column prop="company" label="公司" />
        <el-table-column prop="salary_min" label="薪资">
          <template #default="{ row }">
            {{ row.salary_min || '?' }}k - {{ row.salary_max || '?' }}k
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'applied' ? 'success' : 'info'">
              {{ row.status === 'applied' ? '已投递' : '待投递' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="applySavedJob(row)" v-if="row.status !== 'applied'">
              投递
            </el-button>
            <el-button size="small" type="danger" @click="deleteJob(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { request } from '@/utils/api'

interface Job {
  job_id: string
  title: string
  company: string
  salary_text: string
  salary_min: number
  salary_max: number
  location: string
}

interface SavedJob {
  id: string
  title: string
  company: string
  salary_min: number | null
  salary_max: number | null
  location: string
  status: string
}

interface Rule {
  id: string
  name: string
}

const searchForm = reactive({
  keywords: '',
  location: '',
  salary_min: null as number | null,
  salary_max: null as number | null
})

const batchForm = reactive({
  ruleId: ''
})

const jobs = ref<Job[]>([])
const savedJobs = ref<SavedJob[]>([])
const rules = ref<Rule[]>([])
const searching = ref(false)
const batching = ref(false)
const loadingSaved = ref(false)
const batchResult = ref<{ message: string } | null>(null)

const searchJobs = async () => {
  if (!searchForm.keywords) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  try {
    const params = new URLSearchParams()
    params.append('keywords', searchForm.keywords)
    if (searchForm.location) params.append('location', searchForm.location)
    if (searchForm.salary_min) params.append('salary_min', String(searchForm.salary_min))
    if (searchForm.salary_max) params.append('salary_max', String(searchForm.salary_max))

    const data = await request.post<{ jobs: Job[]; message: string }>(`/crawler/boss/search?${params.toString()}`)
    jobs.value = data.jobs
    ElMessage.success(data.message)
  } catch (error) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

const applyJob = async (job: Job) => {
  try {
    // 先保存岗位
    await request.post('/jobs', {
      platform: 'boss',
      platform_job_id: job.job_id,
      title: job.title,
      company: job.company,
      salary_min: job.salary_min,
      salary_max: job.salary_max,
      location: job.location,
      status: 'pending'
    })

    // 然后投递
    await request.post(`/crawler/boss/apply/${job.job_id}`)
    ElMessage.success('投递成功')
    loadSavedJobs()
  } catch (error) {
    ElMessage.error('投递失败')
  }
}

const loadSavedJobs = async () => {
  loadingSaved.value = true
  try {
    const data = await request.get<{ items: SavedJob[] }>('/jobs')
    savedJobs.value = data.items
  } catch (error) {
    console.error('获取已保存岗位失败', error)
  } finally {
    loadingSaved.value = false
  }
}

const loadRules = async () => {
  try {
    const data = await request.get<{ items: Rule[] }>('/rules')
    rules.value = data.items
  } catch (error) {
    console.error('获取规则列表失败', error)
  }
}

const startBatchDelivery = async () => {
  if (!batchForm.ruleId) {
    ElMessage.warning('请选择筛选规则')
    return
  }

  batching.value = true
  try {
    const data = await request.post<{ jobs_found: number; jobs_applied: number; message: string }>(
      `/crawler/boss/delivery?rule_id=${batchForm.ruleId}`
    )
    batchResult.value = data
    ElMessage.success(data.message)
  } catch (error) {
    ElMessage.error('批量投递启动失败')
  } finally {
    batching.value = false
  }
}

const applySavedJob = async (job: SavedJob) => {
  try {
    await request.post(`/jobs/${job.id}/apply`)
    ElMessage.success('投递成功')
    loadSavedJobs()
  } catch (error) {
    ElMessage.error('投递失败')
  }
}

const deleteJob = async (id: string) => {
  try {
    await request.delete(`/jobs/${id}`)
    ElMessage.success('删除成功')
    loadSavedJobs()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadSavedJobs()
  loadRules()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}
</style>