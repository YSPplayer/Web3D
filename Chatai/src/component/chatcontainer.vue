<template>
    <div class="chatcontainer flex_colum_center">
        <div class="chat_main"></div>
        <div class="chat_input"></div>
    </div>
</template>

<script setup>

</script>

<style scoped>
.chatcontainer {
    gap:1rem;
}
.chat_main {
    width: 95%;
    height:auto;
    border: 1px solid #ccc;
    border-radius: 10px;
}
.chat_input {
     width: 95%;
     height: 7.375rem;
     border-radius: 10px;
     background-color: aqua;
}
</style>