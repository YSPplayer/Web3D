<template>
    <el-dialog v-model="dialogVisible" :title="dialogTitle" class="login_dialog" align-center :close-on-click-modal="false" :show-close="false">
        <div class="flex_colum_center">
            <div
                v-if="registerVisible"
                class="user_register_img"
                role="button"
                tabindex="0"
                title="点击选择头像"
                aria-label="选择注册头像"
                @click="openAvatarFilePicker"
                @keyup.enter="openAvatarFilePicker"
            >
                <img class="fill_img" :src="userImageUrl" alt="用户头像">
                <div class="avatar_select_mask">
                    <span>选择头像</span>
                </div>
            </div>
            <input
                v-if="registerVisible"
                ref="avatarFileRef"
                class="avatar_file_input"
                type="file"
                accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                @change="handleAvatarFileChange"
            >
            <el-input v-model="loginForm.username" placeholder="请输入账号" ref="usernameRef" class="login_input"  @input="onUserNameInput"></el-input>
            <el-input placeholder="请输入密码" v-model="loginForm.password" show-password ref="passwordRef" class="login_input" @input="onUserPasswordInput"></el-input>
            <el-input v-if="registerVisible" placeholder="确认密码" v-model="loginForm.dfpassword" show-password
             ref="dfpasswordRef" class="login_input" @input="onUserDfPasswordInput"></el-input>
            <div class="flex_row_center" style="margin-top: 1rem">
            <el-button :loading="loginLoading"  v-if="!registerVisible" type="primary" class = 'login_button'
            @click = "clickLoginButton"  >登录</el-button>
            <a href="#" v-if="!registerVisible" class="a_link" @click="clickRegisterA">没有账号？去注册</a>
            <el-button :loading="registerLoading" v-if="registerVisible" type="primary" class = 'register_button' @click = "clickRegisterButton" >注册</el-button>
           <a href="#" v-if="registerVisible" class="a_link" @click="clickLoginA">返回登录</a>     
        </div>
        </div>

    </el-dialog>

</template>
<script setup>
    import { ref,reactive,computed, defineEmits } from 'vue'
    import { ChatAiApi } from '@/api/api'
    import { ElMessage } from 'element-plus'
    import CryptoJS from 'crypto-js'
    import {applyAuthenticatedUser} from '@/store/store'
    const AVATAR_MAX_FILE_SIZE = 2 * 1024 * 1024
    const AVATAR_OUTPUT_SIZE = 256
    const userImageUrl = ref('')
    const avatarFileRef = ref(null)
    const loginLoading = ref(false)
    const registerLoading = ref(false)
    const dialogVisible = ref(false)
    const registerVisible = ref(false)
    const usernameRef = ref(null)
    const passwordRef = ref(null)
    const dfpasswordRef = ref(null)
    const emits = defineEmits(['updateUserModelConfig'])
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
        clearLoginForm()
        registerVisible.value = false
        dialogVisible.value = true
    }
    const closeDialog = () => {
        dialogVisible.value = false
    }
    const openAvatarFilePicker = () => {
        avatarFileRef.value?.click()
    }
    const createAvatarDataUrl = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader()
            reader.onerror = () => reject(new Error('头像文件读取失败'))
            reader.onload = () => {
                const image = new Image()
                image.onerror = () => reject(new Error('头像不是有效图片'))
                image.onload = () => {
                    if(image.width <= 0 || image.height <= 0) {
                        reject(new Error('头像尺寸无效'))
                        return
                    }
                    const canvas = document.createElement('canvas')
                    const context = canvas.getContext('2d')
                    if(!context) {
                        reject(new Error('无法创建头像画布'))
                        return
                    }
                    canvas.width = AVATAR_OUTPUT_SIZE
                    canvas.height = AVATAR_OUTPUT_SIZE
                    const sourceSize = Math.min(image.width,image.height)
                    const sourceX = (image.width - sourceSize) / 2
                    const sourceY = (image.height - sourceSize) / 2
                    context.drawImage(
                        image,
                        sourceX,
                        sourceY,
                        sourceSize,
                        sourceSize,
                        0,
                        0,
                        AVATAR_OUTPUT_SIZE,
                        AVATAR_OUTPUT_SIZE
                    )
                    const outputType = file.type === 'image/png'
                        ? 'image/png'
                        : 'image/jpeg'
                    resolve(canvas.toDataURL(outputType,0.9))
                }
                image.src = String(reader.result)
            }
            reader.readAsDataURL(file)
        })
    }
    const handleAvatarFileChange = async (event) => {
        const input = event.target
        const file = input.files?.[0]
        input.value = ''
        if(!file) return

        const extension = file.name.split('.').pop()?.toLowerCase() || ''
        const allowedExtensions = ['jpg','jpeg','png']
        const allowedTypes = ['image/jpeg','image/png']
        if(!allowedExtensions.includes(extension) || !allowedTypes.includes(file.type)) {
            ElMessage.warning('头像只支持 JPG、JPEG 或 PNG 格式')
            return
        }
        if(file.size > AVATAR_MAX_FILE_SIZE) {
            ElMessage.warning('头像文件不能超过 2MB')
            return
        }

        try {
            userImageUrl.value = await createAvatarDataUrl(file)
        } catch(error) {
            ElMessage.error(error instanceof Error ? error.message : '头像读取失败，请重新选择')
        }
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
        loginLoading.value = true
        const result = await ChatAiApi.userRegisterApi({
            username : loginForm.username,
            password : CryptoJS.SHA256(loginForm.password).toString(), //密码加密
            imgurl:userImageUrl.value
        })
        if(result?.code == 200) {
            ElMessage.success('用户注册成功！')
            clickLoginA()
        } else {
            ElMessage.error('用户注册失败！')
        }
        loginLoading.value = false
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
        loginLoading.value = true
        const result = await ChatAiApi.userLoginApi({
            username : loginForm.username,
            password : CryptoJS.SHA256(loginForm.password).toString()
        })
        if(result?.code == 200) {
            const data = result.data?.user
            applyAuthenticatedUser(data)
            ElMessage.success('用户登录成功！')
            closeDialog()
            emits('updateUserModelConfig')
        } else {
            ElMessage.error('用户登录失败！')
        }
        loginLoading.value = false
    }
    const clickRegisterA = async ()=> {
        clearLoginForm()
        registerVisible.value = true
        const result = await ChatAiApi.getDefaultUserImageApi()
        if(result.code == 200) {
            const data = result.data
            userImageUrl.value = data.imageurl
        }
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
.user_register_img {
    position: relative;
    width: 100px;
    height: 100px;
    overflow: hidden;
    border-radius: 8px;
    border: 1px solid #ccc;
    cursor: pointer;
}
.user_register_img img {
    width: 100%;
    height: 100%;
    border-radius: 8px;
    object-fit: cover;
}
.avatar_file_input {
    display: none;
}
.avatar_select_mask {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background-color: rgb(0 0 0 / 42%);
    color: #fff;
    font-size: 14px;
    opacity: 0;
    transition: opacity 0.18s ease;
}
.user_register_img:hover .avatar_select_mask,
.user_register_img:focus-visible .avatar_select_mask {
    opacity: 1;
}
.user_register_img:focus-visible {
    outline: 2px solid var(--el-color-primary);
    outline-offset: 2px;
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
