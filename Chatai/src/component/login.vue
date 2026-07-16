<template>
    <el-dialog v-model="dialogVisible" :title="dialogTitle" class="login_dialog" align-center :close-on-click-modal="false">
        <div class="flex_colum_center">
            <el-input v-model="loginForm.username" placeholder="请输入账号" ref="usernameRef" class="login_input"  @input="onUserNameInput"></el-input>
            <el-input placeholder="请输入密码" v-model="loginForm.password" show-password ref="passwordRef" class="login_input" @input="onUserPasswordInput"></el-input>
            <el-input v-if="registerVisible" placeholder="确认密码" v-model="loginForm.dfpassword" show-password
             ref="dfpasswordRef" class="login_input" @input="onUserDfPasswordInput"></el-input>
            <div class="flex_row_center" style="margin-top: 1rem">
            <el-button v-if="!registerVisible" type="primary" class = 'login_button'
            @click = "clickLoginButton"  >登录</el-button>
            <a href="#" v-if="!registerVisible" class="a_link" @click="clickRegisterA">没有账号？去注册</a>
            <el-button v-if="registerVisible" type="primary" class = 'register_button' @click = "clickRegisterButton" >注册</el-button>
           <a href="#" v-if="registerVisible" class="a_link" @click="clickLoginA">返回登录</a>     
        </div>

        </div>

    </el-dialog>

</template>
<script setup>
    import { ref,reactive,computed  } from 'vue'
    import { ChatAiApi } from '@/api/api'
    import { ElMessage } from 'element-plus'
    import CryptoJS from 'crypto-js'
    import {user} from '@/store/store'
    const dialogVisible = ref(true)
    const registerVisible = ref(false)
    const usernameRef = ref(null)
    const passwordRef = ref(null)
    const dfpasswordRef = ref(null)
    const dialogTitle = computed(() => {
    return registerVisible.value ? '账号注册' : '账号登录'
    })
    const loginForm = reactive({
        username: '',
        password: '',
        dfpassword: ''
    })
    const clearLoginForm = ()=> {
        loginForm.username = ''
        loginForm.password = ''
        loginForm.dfpassword = ''
    }
    const openDialog = () => {
        dialogVisible.value = true
    }
    const closeDialog = () => {
        dialogVisible.value = false
    }
    const clickRegisterButton = async () => {
        if(loginForm.username === '') {
            ElMessage.warning('账号不能为空！')
            return
        }
        if(loginForm.password === '') {
            ElMessage.warning('密码不能为空！')
            return
        }
        if(loginForm.dfpassword === '') {
            ElMessage.warning('确认密码不能为空！')
            return
        }
        if(loginForm.password !== loginForm.dfpassword) {
            ElMessage.error('密码不一致，请检查！')
            return
        }
        const result = await ChatAiApi.userRegisterApi({
            username : loginForm.username,
            password : CryptoJS.SHA256(loginForm.password).toString() //密码加密
        })
        if(result.code == 200) {
            ElMessage.success('用户注册成功！')
            clickLoginA()
        } else {
            ElMessage.error('用户注册失败！')
        }
    }
    const clickLoginButton = async ()=> {
         if(loginForm.username === '') {
            ElMessage.warning('账号不能为空！')
            return
        }
        if(loginForm.password === '') {
            ElMessage.warning('密码不能为空！')
            return
        }
        const result = await ChatAiApi.userLoginApi({
            username : loginForm.username,
            password : CryptoJS.SHA256(loginForm.password).toString()
        })
        if(result.code == 200) {
            const data = result.data
            user.userid = data.id
            user.username = data.username
            ElMessage.success('用户登录成功！')
            closeDialog()
        } else {
            ElMessage.error('用户登录失败！')
        }
    }
    const clickRegisterA = ()=> {
        clearLoginForm()
        registerVisible.value = true
    }
    const clickLoginA = ()=> {
        clearLoginForm()
        registerVisible.value = false
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
    const onUserDfPasswordInput = (val) => {
        // 只保留字母、数字、下划线
        loginForm.dfpassword = val.replace(/[^a-zA-Z0-9_-]/g, '')
    }
</script>

<style>
.el-dialog.login_dialog {
    width: 500px;
}
.el-button.login_button,.el-button.register_button {
    width: 110px;
    height: 40px;
    /* margin-left: auto; */

} 
.a_link {
    margin-left: 1rem;
}
.a_link:hover {
    cursor: pointer;
    color: rgb(226, 192, 56);
}
.el-input.login_input {
    margin-top: 1rem;
    width: 100%;
    --el-input-height: 42px;
    font-size: 18px;
}
</style>