<template>
  <div class="login-page">
    <el-form
      :model="form"
      :rules="rules"
      ref="loginForm"
      class="login-form"
      @submit.prevent="handleLogin"
    >
      <h2>Đăng nhập</h2>
      <el-form-item label="Email" prop="email">
        <el-input
          v-model="form.email"
          type="email"
          placeholder="Nhập email"
          autocomplete="username"
        />
      </el-form-item>
      <el-form-item label="Mật khẩu" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="Nhập mật khẩu"
          autocomplete="current-password"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleLogin" style="width: 100%">
          Đăng nhập
        </el-button>
      </el-form-item>
      <p v-if="error" class="error">{{ error }}</p>
    </el-form>
  </div>
</template>

<script>
export default {
  name: "LoginPage",
  data() {
    return {
      form: {
        email: "",
        password: "",
      },
      error: "",
      rules: {
        email: [
          { required: true, message: "Vui lòng nhập email", trigger: "blur" },
          { type: "email", message: "Email không hợp lệ", trigger: "blur" },
        ],
        password: [
          {
            required: true,
            message: "Vui lòng nhập mật khẩu",
            trigger: "blur",
          },
        ],
      },
    };
  },
  methods: {
    handleLogin() {
      this.error = "";
      this.$refs.loginForm.validate((valid) => {
        if (valid) {
          // Giả lập đăng nhập, thay bằng API thực tế
          if (
            this.form.email === "admin@gmail.com" &&
            this.form.password === "123456"
          ) {
            this.$router.push({ name: "StudentDashboard" });
          } else {
            this.error = "Email hoặc mật khẩu không đúng.";
          }
        }
      });
    },
  },
};
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f6fa;
}
.login-form {
  background: #fff;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 350px;
}
.error {
  color: #e74c3c;
  margin-top: 1rem;
  text-align: center;
}
</style>
