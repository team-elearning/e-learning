<template>
  <el-card class="register-card" shadow="hover">
    <h2>Đăng ký tài khoản</h2>
    <el-form
      :model="form"
      :rules="rules"
      ref="registerForm"
      label-width="120px"
    >
      <el-form-item label="Tên đăng nhập" prop="username">
        <el-input v-model="form.username" placeholder="Nhập tên đăng nhập" />
      </el-form-item>
      <el-form-item label="Email" prop="email">
        <el-input v-model="form.email" placeholder="Nhập email" />
      </el-form-item>
      <el-form-item label="Mật khẩu" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="Nhập mật khẩu"
        />
      </el-form-item>
      <el-form-item label="Xác nhận mật khẩu" prop="confirm">
        <el-input
          v-model="form.confirm"
          type="password"
          placeholder="Nhập lại mật khẩu"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSubmit">Đăng ký</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";

const form = ref({
  username: "",
  email: "",
  password: "",
  confirm: "",
});

const rules = {
  username: [
    { required: true, message: "Vui lòng nhập tên đăng nhập", trigger: "blur" },
  ],
  email: [
    { required: true, message: "Vui lòng nhập email", trigger: "blur" },
    { type: "email", message: "Email không hợp lệ", trigger: "blur" },
  ],
  password: [
    { required: true, message: "Vui lòng nhập mật khẩu", trigger: "blur" },
    { min: 6, message: "Mật khẩu ít nhất 6 ký tự", trigger: "blur" },
  ],
  confirm: [
    { required: true, message: "Vui lòng xác nhận mật khẩu", trigger: "blur" },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== form.value.password) {
          callback(new Error("Mật khẩu xác nhận không khớp"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
};

const registerForm = ref();

function onSubmit() {
  registerForm.value?.validate((valid: boolean) => {
    if (valid) {
      ElMessage.success("Đăng ký thành công!");
      // Thực hiện đăng ký ở đây
    } else {
      ElMessage.error("Vui lòng kiểm tra lại thông tin!");
    }
  });
}
</script>

<style scoped>
.register-card {
  max-width: 400px;
  margin: 40px auto;
  padding: 24px;
}
</style>
