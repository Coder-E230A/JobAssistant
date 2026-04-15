<template>
  <div class="rules-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>筛选规则</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建规则
          </el-button>
        </div>
      </template>

      <el-table :data="rules" v-loading="loading">
        <el-table-column prop="name" label="规则名称" />
        <el-table-column prop="salary_min" label="薪资范围">
          <template #default="{ row }">
            {{ row.salary_min || '?' }}k - {{ row.salary_max || '?' }}k
          </template>
        </el-table-column>
        <el-table-column prop="locations" label="目标城市">
          <template #default="{ row }">
            <el-tag v-for="loc in row.locations" :key="loc" style="margin-right: 5px">{{ loc }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="skills_required" label="技能要求">
          <template #default="{ row }">
            <el-tag v-for="skill in row.skills_required" :key="skill" style="margin-right: 5px">{{ skill }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editRule(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteRule(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" title="筛选规则" width="600px">
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="规则名称">
          <el-input v-model="ruleForm.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="薪资范围">
          <el-col :span="11">
            <el-input-number v-model="ruleForm.salary_min" :min="0" placeholder="最低" />
          </el-col>
          <el-col :span="2" style="text-align: center">-</el-col>
          <el-col :span="11">
            <el-input-number v-model="ruleForm.salary_max" :min="0" placeholder="最高" />
          </el-col>
        </el-form-item>
        <el-form-item label="工作年限">
          <el-col :span="11">
            <el-input-number v-model="ruleForm.experience_min" :min="0" placeholder="最低" />
          </el-col>
          <el-col :span="2" style="text-align: center">-</el-col>
          <el-col :span="11">
            <el-input-number v-model="ruleForm.experience_max" :min="0" placeholder="最高" />
          </el-col>
        </el-form-item>
        <el-form-item label="目标城市">
          <el-select v-model="ruleForm.locations" multiple filterable allow-create placeholder="选择或输入城市">
            <el-option label="北京" value="北京" />
            <el-option label="上海" value="上海" />
            <el-option label="广州" value="广州" />
            <el-option label="深圳" value="深圳" />
            <el-option label="杭州" value="杭州" />
            <el-option label="成都" value="成都" />
          </el-select>
        </el-form-item>
        <el-form-item label="接受远程">
          <el-switch v-model="ruleForm.remote_accepted" />
        </el-form-item>
        <el-form-item label="技能关键词">
          <el-select v-model="ruleForm.skills_required" multiple filterable allow-create placeholder="选择或输入技能">
            <el-option label="Python" value="Python" />
            <el-option label="Java" value="Java" />
            <el-option label="Go" value="Go" />
            <el-option label="前端" value="前端" />
            <el-option label="React" value="React" />
            <el-option label="Vue" value="Vue" />
          </el-select>
        </el-form-item>
        <el-form-item label="包含关键词">
          <el-input v-model="ruleForm.keywords_include_str" placeholder="多个关键词用逗号分隔" />
        </el-form-item>
        <el-form-item label="排除关键词">
          <el-input v-model="ruleForm.keywords_exclude_str" placeholder="多个关键词用逗号分隔" />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="ruleForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRule" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { request } from '@/utils/api'

interface Rule {
  id: string
  name: string
  salary_min: number | null
  salary_max: number | null
  experience_min: number | null
  experience_max: number | null
  locations: string[]
  remote_accepted: boolean
  skills_required: string[]
  keywords_include: string[]
  keywords_exclude: string[]
  is_active: boolean
  created_at: string
}

const rules = ref<Rule[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const saving = ref(false)
const editingId = ref<string | null>(null)

const ruleForm = reactive({
  name: '',
  salary_min: null as number | null,
  salary_max: null as number | null,
  experience_min: null as number | null,
  experience_max: null as number | null,
  locations: [] as string[],
  remote_accepted: false,
  skills_required: [] as string[],
  keywords_include_str: '',
  keywords_exclude_str: '',
  is_active: true
})

const loadRules = async () => {
  loading.value = true
  try {
    const data = await request.get<{ items: Rule[] }>('/rules')
    rules.value = data.items
  } catch (error) {
    console.error('获取规则列表失败', error)
  } finally {
    loading.value = false
  }
}

const editRule = (rule: Rule) => {
  editingId.value = rule.id
  ruleForm.name = rule.name
  ruleForm.salary_min = rule.salary_min
  ruleForm.salary_max = rule.salary_max
  ruleForm.experience_min = rule.experience_min
  ruleForm.experience_max = rule.experience_max
  ruleForm.locations = rule.locations
  ruleForm.remote_accepted = rule.remote_accepted
  ruleForm.skills_required = rule.skills_required
  ruleForm.keywords_include_str = rule.keywords_include.join(',')
  ruleForm.keywords_exclude_str = rule.keywords_exclude.join(',')
  ruleForm.is_active = rule.is_active
  showCreateDialog.value = true
}

const saveRule = async () => {
  if (!ruleForm.name) {
    ElMessage.warning('请输入规则名称')
    return
  }

  saving.value = true
  try {
    const data = {
      name: ruleForm.name,
      salary_min: ruleForm.salary_min,
      salary_max: ruleForm.salary_max,
      experience_min: ruleForm.experience_min,
      experience_max: ruleForm.experience_max,
      locations: ruleForm.locations,
      remote_accepted: ruleForm.remote_accepted,
      skills_required: ruleForm.skills_required,
      keywords_include: ruleForm.keywords_include_str.split(',').filter(s => s.trim()),
      keywords_exclude: ruleForm.keywords_exclude_str.split(',').filter(s => s.trim()),
      is_active: ruleForm.is_active
    }

    if (editingId.value) {
      await request.put(`/rules/${editingId.value}`, data)
      ElMessage.success('更新成功')
    } else {
      await request.post('/rules', data)
      ElMessage.success('创建成功')
    }

    showCreateDialog.value = false
    resetForm()
    loadRules()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const deleteRule = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这条规则吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/rules/${id}`)
    ElMessage.success('删除成功')
    loadRules()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetForm = () => {
  editingId.value = null
  ruleForm.name = ''
  ruleForm.salary_min = null
  ruleForm.salary_max = null
  ruleForm.experience_min = null
  ruleForm.experience_max = null
  ruleForm.locations = []
  ruleForm.remote_accepted = false
  ruleForm.skills_required = []
  ruleForm.keywords_include_str = ''
  ruleForm.keywords_exclude_str = ''
  ruleForm.is_active = true
}

onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>