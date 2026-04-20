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
            <div class="cookie-import-tip" v-if="!bossAccount.bound">
              <el-link type="primary" @click="showCookieImportDialog = true">
                手动导入Cookie
              </el-link>
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
        <!-- 登录状态显示 -->
        <div class="login-status">
          <el-tag :type="loginStatusTag" size="large">
            {{ loginStatusText }}
          </el-tag>
        </div>

        <p class="login-tip">请使用 BOSS直聘 App 扫描下方二维码登录</p>

        <div class="qrcode-container" v-if="qrcodeUrl && loginStatus !== 'expired' && loginStatus !== 'error'">
          <img :src="qrcodeUrl" alt="登录二维码" />
        </div>

        <!-- 二维码过期或出错时显示刷新按钮 -->
        <div class="qrcode-error" v-if="loginStatus === 'expired' || loginStatus === 'error'">
          <el-icon :size="60" color="#909399"><WarningFilled /></el-icon>
          <p>{{ loginStatus === 'expired' ? '二维码已过期' : loginErrorMessage }}</p>
          <el-button type="primary" @click="refreshQrcode">刷新二维码</el-button>
        </div>

        <div class="login-actions">
          <el-button type="primary" @click="checkLoginStatus" :loading="checking" v-if="loginStatus === 'waiting_qrcode'">
            检查登录状态
          </el-button>
          <el-button @click="switchToCookieImport" v-if="loginStatus !== 'logged_in'">
            使用Cookie导入
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- Cookie导入对话框 -->
    <el-dialog v-model="showCookieImportDialog" title="手动导入Cookie" width="600px">
      <div class="cookie-import-content">
        <el-alert type="info" :closable="false" style="margin-bottom: 15px">
          <template #title>
            <p>当二维码登录失败时，可以手动从浏览器导出Cookie绑定账号</p>
          </template>
          <p style="margin-top: 10px">
            <strong>操作步骤：</strong>
          </p>
          <ol style="margin-left: 20px; margin-top: 5px">
            <li>在浏览器中登录 BOSS直聘网站</li>
            <li>打开开发者工具 (F12) → Application → Cookies</li>
            <li>复制 zhipin.com 域名下的所有Cookie</li>
            <li>将Cookie转换为JSON格式后粘贴到下方输入框</li>
          </ol>
        </el-alert>

        <el-form label-width="100px">
          <el-form-item label="Cookie JSON">
            <el-input
              v-model="cookieJson"
              type="textarea"
              :rows="10"
              placeholder="请输入Cookie JSON格式数据，例如：
[
  {\"name\": \"cookie_name\", \"value\": \"cookie_value\", \"domain\": \".zhipin.com\", \"path\": \"/\"}
]"
            />
          </el-form-item>
        </el-form>

        <el-button type="primary" @click="importCookies" :loading="importing">
          导入Cookie
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { request } from '@/utils/api'

const bossAccount = reactive({
  bound: false,
  status: 'not_bound',
  lastSync: ''
})

const showLoginDialog = ref(false)
const showCookieImportDialog = ref(false)
const qrcodeUrl = ref('')
const checking = ref(false)
const loginStatus = ref('waiting_qrcode')
const loginErrorMessage = ref('')
const cookieJson = ref('')
const importing = ref(false)

// 登录状态标签颜色
const loginStatusTag = computed(() => {
  switch (loginStatus.value) {
    case 'waiting_qrcode': return 'info'
    case 'scanned': return 'warning'
    case 'logged_in': return 'success'
    case 'expired': return 'danger'
    case 'error': return 'danger'
    default: return 'info'
  }
})

// 登录状态文本
const loginStatusText = computed(() => {
  switch (loginStatus.value) {
    case 'waiting_qrcode': return '等待扫码'
    case 'scanned': return '已扫码，请确认'
    case 'logged_in': return '登录成功'
    case 'expired': return '二维码过期'
    case 'error': return loginErrorMessage.value || '登录出错'
    default: return '等待扫码'
  }
})

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
  loginStatus.value = 'waiting_qrcode'
  loginErrorMessage.value = ''
  try {
    const data = await request.post<{ status: string; qrcode_url?: string; message?: string }>('/crawler/boss/login')
    if (data.status === 'waiting_qrcode') {
      showLoginDialog.value = true
      qrcodeUrl.value = data.qrcode_url || ''
    } else if (data.status === 'logged_in') {
      ElMessage.success('登录成功')
      loadAccounts()
    } else if (data.status === 'error') {
      loginStatus.value = 'error'
      loginErrorMessage.value = data.message || '启动登录失败'
      showLoginDialog.value = true
    }
  } catch (error: any) {
    ElMessage.error('启动登录失败')
    loginStatus.value = 'error'
    loginErrorMessage.value = error.response?.data?.detail || '启动登录失败'
    showLoginDialog.value = true
  }
}

const refreshQrcode = async () => {
  loginStatus.value = 'waiting_qrcode'
  loginErrorMessage.value = ''
  await startBossLogin()
}

const checkLoginStatus = async () => {
  checking.value = true
  try {
    const data = await request.get<{ status: string; message?: string }>('/crawler/boss/login/status')
    loginStatus.value = data.status

    if (data.status === 'logged_in') {
      ElMessage.success('登录成功')
      showLoginDialog.value = false
      loadAccounts()
    } else if (data.status === 'scanned') {
      ElMessage.info('已扫码，请在手机上确认登录')
      // 继续轮询检查
      setTimeout(checkLoginStatus, 3000)
    } else if (data.status === 'expired') {
      ElMessage.warning('二维码已过期，请刷新')
    } else if (data.status === 'error') {
      loginErrorMessage.value = data.message || '登录出错'
    }
  } catch (error) {
    ElMessage.error('检查状态失败')
  } finally {
    checking.value = false
  }
}

const switchToCookieImport = () => {
  showLoginDialog.value = false
  showCookieImportDialog.value = true
}

const importCookies = async () => {
  if (!cookieJson.value.trim()) {
    ElMessage.warning('请输入Cookie数据')
    return
  }

  importing.value = true
  try {
    const data = await request.post<{ success: boolean; message: string }>('/accounts/boss/import-cookies', {
      cookies_json: cookieJson.value
    })

    if (data.success) {
      ElMessage.success(data.message)
      showCookieImportDialog.value = false
      cookieJson.value = ''
      loadAccounts()
    } else {
      ElMessage.error(data.message)
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || 'Cookie导入失败')
  } finally {
    importing.value = false
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

.cookie-import-tip {
  margin-top: 15px;
}

.login-content {
  text-align: center;
}

.login-status {
  margin-bottom: 20px;
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

.qrcode-error {
  margin-bottom: 20px;
  padding: 20px;
}

.qrcode-error p {
  margin: 10px 0;
  color: #909399;
}

.login-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.cookie-import-content {
  padding: 10px;
}

.cookie-import-content ol {
  line-height: 1.8;
}
</style>