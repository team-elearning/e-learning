<!-- src/pages/teacher/students/Feedback.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-6 py-8 md:px-10">
      <!-- Header -->
      <div class="mb-5 flex items-center justify-between gap-3">
        <h1 class="text-2xl font-semibold">Phản hồi học sinh</h1>
        <button class="rounded-xl border px-4 py-2 text-sm hover:bg-slate-50" @click="goBack">
          ← Quay lại danh sách
        </button>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <!-- Left: student list -->
        <section class="lg:col-span-1 rounded-2xl border border-slate-200 bg-white p-4">
          <div class="mb-3 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" aria-hidden="true">
              <circle cx="11" cy="11" r="8" stroke-width="2" />
              <path d="M21 21l-4.3-4.3" stroke-width="2" />
            </svg>
            <input
              v-model.trim="q"
              placeholder="Tìm học sinh…"
              class="w-full bg-transparent outline-none"
              @input="debouncedFilter"
            />
          </div>

          <div v-if="loading" class="space-y-2">
            <div v-for="i in 6" :key="'sk-'+i" class="flex items-center gap-3 rounded-xl px-2 py-2">
              <div class="h-9 w-9 rounded-full bg-slate-200 animate-pulse"></div>
              <div class="flex-1">
                <div class="h-3 w-2/3 rounded bg-slate-200 animate-pulse mb-2"></div>
                <div class="h-3 w-1/2 rounded bg-slate-100 animate-pulse"></div>
              </div>
            </div>
          </div>

          <ul v-else-if="students.length" class="max-h-[560px] space-y-2 overflow-auto pr-1">
            <li v-for="s in students" :key="s.id">
              <button
                class="flex w-full items-center gap-3 rounded-xl px-2 py-2 text-left hover:bg-slate-50"
                :class="selectedId === s.id ? 'bg-slate-100' : ''"
                @click="select(s.id)"
              >
                <img :src="s.avatar" :alt="s.name" class="h-9 w-9 rounded-full object-cover" />
                <div class="min-w-0 flex-1">
                  <div class="truncate text-sm font-medium">{{ s.name }}</div>
                  <div class="truncate text-xs text-slate-500">{{ s.classCode }} · {{ s.course }}</div>
                </div>
              </button>
            </li>
          </ul>
          <div v-else class="py-10 text-center text-sm text-slate-500">Không có học sinh phù hợp.</div>
        </section>

        <!-- Right: composer -->
        <section class="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-4">
          <div v-if="!current" class="p-6 text-center text-slate-500">
            Chọn một học sinh ở danh sách bên trái để viết phản hồi.
          </div>

          <div v-else class="space-y-4">
            <div class="flex items-center gap-3">
              <img :src="current.avatar" :alt="current.name" class="h-12 w-12 rounded-full object-cover" />
              <div>
                <div class="font-semibold">{{ current.name }}</div>
                <div class="text-xs text-slate-500">{{ current.classCode }} · {{ current.course }}</div>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div class="rounded-xl bg-slate-50 p-3 text-sm">
                Tiến độ: <span class="font-medium">{{ current.progress }}%</span>
              </div>
              <div class="rounded-xl bg-slate-50 p-3 text-sm">
                Điểm TB: <span class="font-medium">{{ current.avgScore.toFixed(1) }}/10</span>
              </div>
              <div class="rounded-xl bg-slate-50 p-3 text-sm">
                Hoạt động: <span class="font-medium">{{ current.lastActive }}</span>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div class="space-y-2 md:col-span-2">
                <label class="text-sm font-medium">Nội dung phản hồi</label>
                <textarea
                  v-model="message"
                  rows="7"
                  class="w-full rounded-2xl border border-slate-200 p-3 outline-none ring-sky-200 focus:ring"
                  placeholder="Viết nhận xét, gợi ý ôn tập, điểm cần cải thiện…"
                ></textarea>

                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="(t,i) in chipTexts"
                    :key="'chip-'+i"
                    type="button"
                    class="rounded-full border px-2 py-1 text-xs hover:bg-slate-50"
                    @click="append(t)"
                  >
                    {{ t }}
                  </button>
                </div>
              </div>

              <div class="space-y-3">
                <div>
                  <label class="mb-1 block text-sm font-medium">Mức độ hoàn thành</label>
                  <input type="range" min="0" max="10" step="0.5" v-model.number="rating" class="w-full" />
                  <div class="mt-1 text-sm">
                    <span class="font-medium">{{ rating.toFixed(1) }}</span> / 10
                  </div>
                </div>

                <div>
                  <label class="mb-1 block text-sm font-medium">Mẫu phản hồi</label>
                  <select v-model="template" class="w-full rounded-xl border border-slate-200 p-2 text-sm">
                    <option value="">— Chọn mẫu —</option>
                    <option value="praise">Khen ngợi</option>
                    <option value="improve">Cần cải thiện</option>
                    <option value="suggest">Gợi ý ôn tập</option>
                  </select>
                </div>

                <button
                  class="w-full rounded-xl px-3 py-2 font-semibold text-white hover:brightness-105"
                  :class="canSend ? 'bg-sky-600' : 'bg-sky-400 cursor-not-allowed'"
                  :disabled="!canSend"
                  @click="send"
                >
                  Gửi phản hồi
                </button>
                <p v-if="sent" class="text-center text-sm text-emerald-600">Đã gửi phản hồi 🎉</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/** ========= Types ========= */
type StudentRow = {
  id: number
  name: string
  avatar: string
  classCode: string
  course: string
  progress: number
  avgScore: number
  lastActive: string
}

/** ========= Router / state ========= */
const route = useRoute()
const router = useRouter()

const q = ref('')
const selectedId = ref<number | null>(route.query.id ? Number(route.query.id) : null)
const message = ref('')
const rating = ref(7.5)
type Tpl = '' | 'praise' | 'improve' | 'suggest'
const template = ref<Tpl>('')
const sent = ref(false)

const loading = ref(true)
const allStudents = ref<StudentRow[]>([])

/** ========= Debounce search ========= */
let t: number | null = null
const debouncedFilter = () => {
  if (t) clearTimeout(t)
  t = window.setTimeout(() => { /* trigger computed filter */ }, 250) as unknown as number
}

/** ========= Chips (fixed as ref) ========= */
const chipTexts = ref<string[]>([
  'Em làm tốt phần lý thuyết.',
  'Cần luyện thêm bài tập vận dụng.',
  'Cố gắng đọc kỹ câu hỏi trước khi trả lời.',
  'Rất tích cực phát biểu.',
  'Ôn lại từ vựng chương này nhé.',
])

/** ========= Data source =========
 * Ưu tiên dùng userService (mock có sẵn). Nếu không có, dùng mock tại chỗ.
 */
async function fetchStudents() {
  loading.value = true
  try {
    // dynamic import để không phụ thuộc cứng
    // @ts-ignore
    const mod = await import('@/services/user.service')
    const userService = mod.userService as {
      list: (p: any) => Promise<{ items: Array<{ id:number|string; name:string; username:string }> }>
    }
    const res = await userService.list({ role: 'student', pageSize: 50, page: 1 })
    const now = Date.now()
    allStudents.value = res.items.map((u, i) => {
      const id = Number(u.id)
      const cls = `L${(id % 5) + 1}0${(id % 3) + 1}`
      const course = `Khoá ${(id % 6) + 1}`
      return {
        id,
        name: u.name,
        avatar: `https://api.dicebear.com/7.x/thumbs/svg?seed=${encodeURIComponent(u.username)}&backgroundType=gradientLinear`,
        classCode: cls,
        course,
        progress: 40 + ((id + i) % 50), // 40..89
        avgScore: 6 + ((id + i) % 40) / 10, // 6.0..9.9
        lastActive: new Date(now - ((i + 1) * 36e5)).toLocaleString(),
      }
    })
  } catch {
    // Fallback mock (nếu không resolve được service)
    const N = 24
    const now = Date.now()
    allStudents.value = Array.from({ length: N }).map((_, i) => {
      const id = i + 1
      return {
        id,
        name: `Học sinh ${id}`,
        avatar: `https://api.dicebear.com/7.x/thumbs/svg?seed=hs-${id}&backgroundType=gradientLinear`,
        classCode: `L${(id % 5) + 1}0${(id % 3) + 1}`,
        course: `Khoá ${(id % 6) + 1}`,
        progress: 45 + (id % 40),
        avgScore: 6 + (id % 35) / 10,
        lastActive: new Date(now - id * 36e5).toLocaleString(),
      }
    })
  } finally {
    loading.value = false
  }
}

/** ========= Derived ========= */
const students = computed(() => {
  const key = q.value.trim().toLowerCase()
  return allStudents.value.filter(s =>
    !key ||
    s.name.toLowerCase().includes(key) ||
    s.classCode.toLowerCase().includes(key) ||
    s.course.toLowerCase().includes(key)
  )
})

const current = computed<StudentRow | null>(() =>
  students.value.find(s => s.id === selectedId.value) ?? null
)

const canSend = computed(() => !!current.value && message.value.trim().length > 0)

/** ========= Effects / actions ========= */
function select(id: number) {
  if (selectedId.value === id) return
  selectedId.value = id
  // reset compose
  sent.value = false
  message.value = ''
  rating.value = 7.5
  template.value = ''
}

// đồng bộ id vào URL (để F5 vẫn giữ lựa chọn)
watch(selectedId, (val) => {
  const q = { ...route.query }
  if (val) q.id = String(val)
  else delete q.id
  router.replace({ query: q })
})

watch(template, (t) => {
  if (!t) return
  if (t === 'praise') message.value = 'Cô/Thầy đánh giá cao sự nỗ lực của em. Tiếp tục phát huy nhé!'
  if (t === 'improve') message.value = 'Em cần chú ý hơn ở các bài tập vận dụng và luyện thêm ví dụ tương tự.'
  if (t === 'suggest') message.value = 'Gợi ý: Ôn lại các mục trọng tâm và làm bài luyện tập ở cuối chương.'
})

function append(t: string) {
  message.value = message.value ? `${message.value} ${t}` : t
}

function send() {
  if (!canSend.value || !current.value) return
  // TODO: gọi API thật
  console.log('SEND_FEEDBACK', {
    studentId: current.value.id,
    rating: rating.value,
    message: message.value.trim(),
  })
  sent.value = true
}

function goBack() {
  router.push({ path: '/teacher/students' })
}

/** ========= Mount ========= */
onMounted(async () => {
  await fetchStudents()
  // nếu có ?id nhưng không khớp data → clear
  if (selectedId.value && !allStudents.value.some(s => s.id === selectedId.value)) {
    selectedId.value = null
  }
})
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
</style>
