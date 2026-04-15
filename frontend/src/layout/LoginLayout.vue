<template>
  <div class="login-layout">
    <slot></slot>
  </div>
</template>

<script setup>
// 登录页布局容器，可扩展背景、全局样式等
</script>

<style scoped>
.login-layout {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>