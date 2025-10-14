<template>
  <div class="min-h-screen bg-slate-50 p-4 sm:p-6">
    <div class="mx-auto max-w-4xl">
      <section class="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div class="flex items-center justify-between border-b border-slate-200 p-6">
          <div>
            <h2 class="text-xl font-bold text-slate-800">Hồ sơ giảng viên</h2>
            <p class="mt-1 text-sm text-slate-500">
              Cập nhật thông tin cá nhân và giới thiệu của bạn.
            </p>
          </div>
          <button
            class="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
            @click="resetForm"
            :disabled="loading || !isDirty"
          >
            Hoàn tác
          </button>
        </div>

        <form class="space-y-6 p-6" @submit.prevent="onSave">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
            <img
              :src="preview || form.avatar || fallback"
              class="h-20 w-20 rounded-full object-cover ring-2 ring-slate-200"
              alt="avatar"
            />
            <div class="space-y-2">
              <label
                class="inline-flex cursor-pointer items-center rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
              >
                <input type="file" class="hidden" accept="image/*" @change="onPick" />
                <span>Đổi ảnh đại diện</span>
              </label>
              <p class="text-xs text-slate-500">Chấp nhận PNG, JPG, WebP. Kích thước tối đa 2MB.</p>
              <p v-if="errors.avatar" class="text-xs text-red-600">{{ errors.avatar }}</p>
            </div>
          </div>

          <hr class="border-slate-200" />

          <div class="grid grid-cols-1 gap-x-6 gap-y-5 sm:grid-cols-2">
            <div class="space-y-1.5">
              <label for="name" class="text-sm font-medium text-slate-700">Họ tên</label>
              <input
                id="name"
                v-model.trim="form.name"
                class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800 transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Nguyễn Văn A"
              />
              <p v-if="errors.name" class="mt-1 text-xs text-red-600">{{ errors.name }}</p>
            </div>

            <div class="space-y-1.5">
              <label for="email" class="text-sm font-medium text-slate-700">Email</label>
              <input
                id="email"
                v-model.trim="form.email"
                type="email"
                class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800 transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="teacher@example.com"
              />
              <p v-if="errors.email" class="mt-1 text-xs text-red-600">{{ errors.email }}</p>
            </div>

            <div class="space-y-1.5">
              <label for="phone" class="text-sm font-medium text-slate-700">Số điện thoại</label>
              <input
                id="phone"
                v-model.trim="form.phone"
                class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800 transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="09xx xxx xxx"
              />
            </div>

            <div class="space-y-1.5">
              <label for="title" class="text-sm font-medium text-slate-700">Chức danh</label>
              <input
                id="title"
                v-model.trim="form.title"
                class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800 transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Giảng viên / Mentor"
              />
            </div>
          </div>

          <div class="space-y-1.5">
            <label for="bio" class="text-sm font-medium text-slate-700">Giới thiệu</label>
            <textarea
              id="bio"
              v-model.trim="form.bio"
              rows="4"
              class="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-800 transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Mô tả ngắn về kinh nghiệm, thế mạnh giảng dạy…"
            ></textarea>
          </div>

          <hr class="border-slate-200" />

          <div class="flex items-center gap-4">
            <button
              type="submit"
              class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
              :disabled="loading || !isDirty"
            >
              <span v-if="loading">Đang lưu...</span>
              <span v-else>Lưu thay đổi</span>
            </button>

            <RouterLink
              to="/teacher/account/change-password"
              class="text-sm font-medium text-blue-600 transition-colors hover:underline"
            >
              Đổi mật khẩu
            </RouterLink>

            <transition
              enter-active-class="transition ease-out duration-300"
              enter-from-class="transform opacity-0 scale-95"
              enter-to-class="transform opacity-100 scale-100"
              leave-active-class="transition ease-in duration-200"
              leave-from-class="transform opacity-100 scale-100"
              leave-to-class="transform opacity-0 scale-95"
            >
              <span v-if="saved" class="flex items-center gap-2 text-sm text-green-600">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  class="h-5 w-5"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                    clip-rule="evenodd"
                  />
                </svg>
                Đã lưu thành công!
              </span>
            </transition>
          </div>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useAuthStore } from '@/store/auth.store'
import type { AuthUser } from '@/services/auth.service'

const auth = useAuthStore()
const user = computed<AuthUser | null>(() => auth.user)

const fallback = 'https://i.pravatar.cc/120?img=5'

// --- form state ---
const original = reactive({
  name: user.value?.name ?? '',
  email: user.value?.email ?? '',
  phone: user.value?.phone ?? '',
  title: user.value?.title ?? '',
  bio: user.value?.bio ?? '',
  avatar: user.value?.avatar ?? '',
})

const form = reactive({ ...original })
const errors = reactive<{ [k: string]: string }>({})
const loading = ref(false)
const saved = ref(false)

// derived
const isDirty = computed(() => JSON.stringify(form) !== JSON.stringify(original))

// preview avatar
const preview = ref<string | null>(null)
const onPick = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!/^image\/(png|jpe?g|webp)$/.test(file.type)) {
    errors.avatar = 'Chỉ nhận PNG/JPG/WebP'
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    errors.avatar = 'Ảnh vượt quá 2MB'
    return
  }
  errors.avatar = ''
  const reader = new FileReader()
  reader.onload = () => (preview.value = reader.result as string)
  reader.readAsDataURL(file)
}

// validate đơn giản
const validate = () => {
  errors.name = form.name ? '' : 'Vui lòng nhập họ tên'
  errors.email = /\S+@\S+\.\S+/.test(form.email) ? '' : 'Email không hợp lệ'
  return !errors.name && !errors.email
}

const onSave = async () => {
  saved.value = false
  if (!validate()) return
  loading.value = true
  try {
    await auth.updateProfile({
      ...form,
      avatar: preview.value ?? form.avatar ?? undefined,
    })
    Object.assign(original, { ...form, avatar: preview.value ?? form.avatar })
    saved.value = true
    setTimeout(() => (saved.value = false), 2000) // Tăng thời gian hiển thị thông báo
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  Object.assign(form, original)
  preview.value = null
  Object.keys(errors).forEach((k) => (errors[k] = ''))
}

// nếu user được hydrate lại, cập nhật form
watch(user, (u) => {
  if (!u) return
  Object.assign(original, {
    name: u.name ?? '',
    email: u.email ?? '',
    phone: u.phone ?? '',
    title: u.title ?? '',
    bio: u.bio ?? '',
    avatar: u.avatar ?? '',
  })
  resetForm()
})
</script>