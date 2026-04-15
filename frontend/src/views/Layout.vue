<template>
  <el-container class="layout-container">
    <el-header class="layout-header">
      <div class="logo">
        <el-icon :size="24"><Briefcase /></el-icon>
        <span>JobAssistant</span>
      </div>
      <div class="header-right">
        <span class="user-name">{{ authStore.user?.nickname || authStore.user?.email }}</span>
        <el-dropdown @command="handleCommand">
          <el-button type="primary" circle>
            <el-icon><User /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container>
      <el-aside width="200px" class="layout-aside">
        <el-menu :default-active="activeMenu" router>
          <el-menu-item index="/">
            <el-icon><DataLine /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/accounts">
            <el-icon><Link /></el-icon>
            <span>平台账号</span>
          </el-menu-item>
          <el-menu-item index="/resumes">
            <el-icon><Document /></el-icon>
            <span>简历管理</span>
          </el-menu-item>
          <el-menu-item index="/rules">
            <el-icon><Filter /></el-icon>
            <span>筛选规则</span>
          </el-menu-item>
          <el-menu-item index="/jobs">
            <el-icon><Search /></el-icon>
            <span>岗位搜索</span>
          </el-menu-item>
          <el-menu-item index="/applications">
            <el-icon><List /></el-icon>
            <span>投递记录</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #409eff;
  color: white;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-name {
  font-size: 14px;
}

.layout-aside {
  background: #f5f7fa;
}

.layout-main {
  background: #f0f2f5;
  padding: 20px;
}
</style>