<template>
  <div class="accounts-page">
    <el-card>
      <template #header>
        <span>平台账号管理</span>
      </template>

      <el-row :gutter="20">
        <!-- BOSS直聘 -->
        <el-col :span="6">
          <el-card class="platform-card" shadow="hover">
            <div class="platform-info">
              <h3>BOSS直聘</h3>
              <el-tag :type="bossAccount.bound ? 'success' : 'info'">
                {{ bossAccount.bound ? '已绑定' : '未绑定' }}
              </el-tag>
            </div>
            <div class="platform-actions">
              <el-button type="primary" @click="startBossLogin" v-if="!bossAccount.bound">
                绑定账号
              </el-button>
              <el-button @click="checkBossStatus" v-if="bossAccount.bound">
                检查状态
              </el-button>
              <el-button type="danger" @click="unbindBoss" v-if="bossAccount.bound">
                解绑
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- 脉脉 -->
        <el-col :span="6">
          <el-card class="platform-card" shadow="hover">
            <div class="platform-info">
              <h3>脉脉</h3>
              <el-tag type="info">暂不支持</el-tag>
            </div>
          </el-card>
        </el-col>

        <!-- 猎聘 -->
        <el-col :span="6">
          <el-card class="platform-card" shadow="hover">
            <div class="platform-info">
              <h3>猎聘</h3>
              <el-tag type="info">暂不支持</el-tag>
            </div>
          </el-card>
        </el-col>

        <!-- 拉勾 -->
        <el-col :span="6">
          <el-card class="platform-card" shadow="hover">
            <div class="platform-info">
              <h3>拉勾</h3>
              <el-tag type="info">暂不支持</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- BOSS登录对话框 -->
    <el-dialog v-model="showLoginDialog" title="BOSS直聘登录" width="500px">
      <div class="login-content">
        <p class="login-tip">请使用 BOSS直聘 App 扫描下方二维码登录</p>
        <div class="qrcode-container" v-if="qrcodeUrl">
          <img :src="qrcodeUrl" alt="登录二维码" />
        </div>
        <el-button type="primary" @click="checkLoginStatus" :loading="checking">
          检查登录状态
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { request } from '@/utils/api'

const bossAccount = reactive({
  bound: false,
  status: 'not_bound',
  lastSync: ''
})

const showLoginDialog = ref(false)
const qrcodeUrl = ref('')
const checking = ref(false)

const loadAccounts = async () => {
  try {
    const data = await request.get<{ bound: boolean; status: string; last_sync?: string }>('/accounts/boss/status')
    bossAccount.bound = data.bound
    bossAccount.status = data.status
    bossAccount.lastSync = data.last_sync || ''
  } catch (error) {
    console.error('获取账号状态失败', error)
  }
}

const startBossLogin = async () => {
  try {
    const data = await request.post<{ status: string; qrcode_url?: string }>('/crawler/boss/login')
    if (data.status === 'waiting_qrcode') {
      showLoginDialog.value = true
      qrcodeUrl.value = data.qrcode_url || ''
    } else if (data.status === 'logged_in') {
      ElMessage.success('登录成功')
      loadAccounts()
    }
  } catch (error) {
    ElMessage.error('启动登录失败')
  }
}

const checkLoginStatus = async () => {
  checking.value = true
  try {
    const data = await request.get<{ status: string; message?: string }>('/crawler/boss/login/status')
    if (data.status === 'logged_in') {
      ElMessage.success('登录成功')
      showLoginDialog.value = false
      loadAccounts()
    } else if (data.status === 'waiting_qrcode') {
      ElMessage.info('等待扫码...')
    }
  } catch (error) {
    ElMessage.error('检查状态失败')
  } finally {
    checking.value = false
  }
}

const checkBossStatus = async () => {
  try {
    const data = await request.get<{ status: string }>('/accounts/boss/status')
    if (data.status === 'active') {
      ElMessage.success('账号状态正常')
    } else {
      ElMessage.warning('账号状态异常，请重新登录')
    }
  } catch (error) {
    ElMessage.error('检查状态失败')
  }
}

const unbindBoss = async () => {
  try {
    await ElMessageBox.confirm('确定要解绑 BOSS直聘账号吗？', '提示', {
      type: 'warning'
    })
    // 查找账号ID并删除
    const accountsData = await request.get<{ items: { id: string; platform: string }[] }>('/accounts')
    const bossAcc = accountsData.items.find(a => a.platform === 'boss')
    if (bossAcc) {
      await request.delete(`/accounts/${bossAcc.id}`)
      ElMessage.success('已解绑')
      loadAccounts()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('解绑失败')
    }
  }
}

onMounted(() => {
  loadAccounts()
})
</script>

<style scoped>
.platform-card {
  text-align: center;
}

.platform-info {
  margin-bottom: 20px;
}

.platform-info h3 {
  margin-bottom: 10px;
}

.platform-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.login-content {
  text-align: center;
}

.login-tip {
  margin-bottom: 20px;
  color: #909399;
}

.qrcode-container {
  margin-bottom: 20px;
}

.qrcode-container img {
  max-width: 200px;
}
</style>