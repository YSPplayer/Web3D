<template>
    <el-dialog v-model="dialogVisible" class="login_dialog" align-center>
        <div class="flex_colum_center">
            <el-input v-model="loginForm.username" placeholder="请输入账号"  class="login_input"  @input="onUserNameInput"></el-input>
            <el-input placeholder="请输入密码" v-model="loginForm.password" show-password  class="login_input" @input="onUserPasswordInput"></el-input>
            <el-button type="primary" class = 'login_button'>登录</el-button>
        </div>

    </el-dialog>

</template>
<script setup>
    import { ref,reactive  } from 'vue'
    const dialogVisible = ref(true)
    const loginForm = reactive({
        username: '',
        password: ''
    })
    const openDialog = () => {
        dialogVisible.value = true
    }
    const closeDialog = () => {
        dialogVisible.value = false
    }
    defineExpose({
        openDialog,
        closeDialog
    })
    const onUserNameInput = (val) => {
        // 只保留字母、数字、下划线
        loginForm.username = val.replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, '')
    }
    const onUserPasswordInput = (val) => {
        // 只保留字母、数字、下划线
        loginForm.password = val.replace(/[^a-zA-Z0-9_-]/g, '')
    }
</script>

<style>
.el-dialog.login_dialog {
    width: 500px;
}
.el-button.login_button {
    margin-top: 1rem;
    width: 110px;
    height: 40px;
    /* margin-left: auto; */

} 

.el-input.login_input {
    margin-top: 1rem;
    width: 100%;
    --el-input-height: 50px;
    font-size: 18px;
}
</style>