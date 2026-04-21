<template>
  <div class="app rowflex">
    <div class="left_container">
    <el-row class="side-menu ">
      <el-col>
        <h3>列表</h3>
        <el-menu
          default-active="2"
          class="el-menu-vertical-demo"
          @open="handleOpen"
          @close="handleClose"
        >
       <el-menu-item index="1">
          <span>导航一</span>
      </el-menu-item>
        </el-menu>
      </el-col>
    </el-row>
    </div>
    <div class="right_container"> 
      <div class="train_container"> 
        <el-table
      style="width: 100%">
      <el-table-column
        prop="date"
        label="日期"
        width="180">
      </el-table-column>
      <el-table-column
        prop="name"
        label="姓名"
        width="180">
      </el-table-column>
      <el-table-column
        prop="address"
        label="地址">
      </el-table-column>
    </el-table></div>
    </div>
  </div>
</template>

<script setup lang="ts">
const handleOpen = (key: string, keyPath: string[]) => {
  console.log("open", key, keyPath);
};

const handleClose = (key: string, keyPath: string[]) => {
  console.log("close", key, keyPath);
};
</script>

<style scoped>
/* 水平 */
.rowflex {
  display: flex;
   /* justify-content: center;
   align-items: center;   */
   flex-direction: row; 
}
/*垂直 */
.colflex {
  display: flex;
   justify-content: center;
   align-items: center;  
   flex-direction: column; 
}
.app {
  position: relative;
  width: 100vw;
  height: 100vh;
}
h3 {
  margin-left: 10px;
}
.side-menu {
  margin: 5px;
  width: 100%;
  height: 100%;
}
.left_container {
  width: clamp(180px, 20vw, 320px);
  min-width: 180px;
  max-width: 320px;
  height: 100%;
  /* border: 1px solid #2e2d2d; */
}

.el-menu-vertical-demo {
  min-height: 480px;
}
</style>
