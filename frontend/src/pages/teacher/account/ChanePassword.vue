<template>
  <div class="p-6">
    <section class="mx-auto w-full max-w-3xl rounded-2xl border bg-white p-6 shadow-sm">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-gray-800">Đổi mật khẩu</h2>
          <p class="text-sm text-gray-500">Nhập mật khẩu hiện tại và thiết lập mật khẩu mới.</p>
        </div>
      </div>

      <!-- Form -->
      <form class="mt-6 space-y-5" @submit.prevent="onSubmit">
        <!-- Old password -->
        <div>
          <label class="text-sm text-gray-600">Mật khẩu hiện tại</label>
          <div class="relative mt-1">
            <input
              :type="show.old ? 'text' : 'password'"
              v-model.trim="form.oldPassword"
              class="w-full rounded-lg border px-3 py-2 pr-12 focus:ring-2 focus:ring-blue-500"
              autocomplete="current-password"
              placeholder="••••••••"
            />
            <button
              type="button"
              class="absolute inset-y-0 right-2 my-auto text-sm text-gray-500"
              @click="show.old = !show.old"
            >
              {{ show.old ? 'Ẩn' : 'Hiện' }}
            </button>
          </div>
          <p v-if="errors.oldPassword" class="mt-1 text-xs text-red-600">{{ errors.oldPassword }}</p>
        </div>

        <!-- New password -->
        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="text-sm text-gray-600">Mật khẩu mới</label>
            <div class="relative mt-1">
              <input
                :type="show.new ? 'text' : 'password'"
                v-model.trim="form.newPassword"
                class="w-full rounded-lg border px-3 py-2 pr-12 focus:ring-2 focus:ring-blue-500"
                autocomplete="new-password"
                placeholder="Ít nhất 8 ký tự"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-2 my-auto text-sm text-gray-500"
                @click="show.new = !show.new"
              >
                {{ show.new ? 'Ẩn' : 'Hiện' }}
              </button>
            </div>
            <p v-if="errors.newPassword" class="mt-1 text-xs text-red-600">
              {{ errors.newPassword }}
            </p>
          </div>

          <div>
            <label class="text-sm text-gray-600">Xác nhận mật khẩu mới</label>
            <div class="relative mt-1">
              <input
                :type="show.confirm ? 'text' : 'password'"
                v-model.trim="form.confirmPassword"
                class="w-full rounded-lg border px-3 py-2 pr-12 focus:ring-2 focus:ring-blue-500"
                autocomplete="new-password"
                placeholder="Nhập lại mật khẩu mới"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-2 my-auto text-sm text-gray-500"
                @click="show.confirm = !show.confirm"
              >
                {{ show.confirm ? 'Ẩn' : 'Hiện' }}
              </button>
            </div>
            <p v-if="errors.confirmPassword" class="mt-1 text-xs text-red-600">
              {{ errors.confirmPassword }}
            </p>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-3 pt-1">
          <button
            type="submit"
            class="rounded-xl bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-60"
            :disabled="loading"
          >
            <span v-if="loading">Đang đổi…</span>
            <span v-else>Đổi mật khẩu</span>
          </button>

          <RouterLink to="/teacher/account/profile" class="text-sm text-blue-600 hover:underline">
            Quay lại hồ sơ
          </RouterLink>

          <span v-if="done" class="text-sm text-green-600">Đổi mật khẩu thành công!</span>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useAuthStore } from '@/store/auth.store'

const auth = useAuthStore()

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})
const errors = reactive<{ [k: string]: string }>({})
const loading = ref(false)
const done = ref(false)
const show = reactive({ old: false, new: false, confirm: false })

const validate = () => {
  errors.oldPassword = ''
  errors.newPassword = ''
  errors.confirmPassword = ''
  let ok = true

  if (!form.oldPassword) {
    errors.oldPassword = 'Vui lòng nhập mật khẩu hiện tại.'
    ok = false
  }
  if (form.newPassword.length < 8) {
    errors.newPassword = 'Mật khẩu mới phải có ít nhất 8 ký tự.'
    ok = false
  }
  if (form.confirmPassword !== form.newPassword) {
    errors.confirmPassword = 'Xác nhận mật khẩu mới không khớp.'
    ok = false
  }
  return ok
}
const onSubmit = async () => {
  done.value = false
  if (!validate()) return
  loading.value = true
  try {
    // Gọi action trong store (mock hoặc service thật tuỳ bạn đã cấu hình)
    await auth.changePassword(form.oldPassword, form.newPassword)

    done.value = true
    form.oldPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    setTimeout(() => (done.value = false), 1800)
  } finally {
    loading.value = false
  }
}
</script>
