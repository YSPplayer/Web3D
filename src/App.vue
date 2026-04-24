<template>
  <div class="app rowflex">
    <div class="left_container">
    <el-row class="side-menu ">
      <el-col>
        <h3>列表</h3>
        <el-menu
          default-active="2"
          class="el-menu-vertical"
        >
       <el-menu-item index="1">
          <span>导航一</span>
      </el-menu-item>
        </el-menu>
      </el-col>
    </el-row>
    </div>
    <div class="mid_container">
      <GrayImage />
    </div>

  </div>
</template>

<script setup lang="ts">
import { request } from '@/api/request'
import { onMounted } from 'vue';
import GrayImage from '@/module/grayImage.vue'


onMounted(async () => {
  const apiUrl = import.meta.env.VITE_SERVER_API_URL;
  request.create(apiUrl) //初始化接口
});
</script>

<style scoped>
.app {
  position: relative;
  width: 100vw;
  height: 100vh;
}
h3 {
  margin-left: 10px;
}
.side-menu {
  width: 95%;
  height: 100%;
}
.mid_container {
  margin :10px;
}

.left_container {
  width: clamp(180px, 20vw, 320px);
  min-width: 180px;
  max-width: 320px;
  height: 100%;
  border-right: 1px solid #cac8c8;
  /* border: 1px solid #2e2d2d; */
}
.el-menu-vertical {
  min-height: 480px;
  border:none;
}
:deep(.el-menu-vertical) {
  border-right: none;
}
</style>
