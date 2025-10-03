<template>
  <div class="exam-ui">
    <div class="exam-container">
      <header class="exam-header">
        <div class="exam-info">
          <h1 class="exam-title">{{ exam?.title || 'Đề luyện tập' }}</h1>
          <p class="exam-meta">
            <span>{{ labelLevel(exam?.level) }}</span>
            <span>{{ Math.round((exam?.durationSec || 0) / 60) }} phút</span>
            <span>{{ questions.length }} câu</span>
            <span>Đạt ≥ {{ exam?.passCount || Math.ceil(questions.length * 0.6) }} câu</span>
          </p>
        </div>
        <div class="exam-tools">
          <div class="timer" :class="{ danger: timeLeft <= 60 }">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="timer-icon">
              <path fill-rule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zM12.75 6a.75.75 0 00-1.5 0v6c0 .414.336.75.75.75h4.5a.75.75 0 000-1.5h-3.75V6z" clip-rule="evenodd" />
            </svg>
            <span>{{ fmtTime(timeLeft) }}</span>
          </div>
          <button class="btn btn-ghost" @click="goBack">Thoát</button>
        </div>
      </header>

      <div v-if="loading" class="skeleton-wrapper">
        <div class="skeleton-line" style="width: 60%;"></div>
        <div class="skeleton-box"></div>
        <div class="skeleton-line" style="width: 80%;"></div>
      </div>

      <main v-else class="exam-main">
        <div class="question-navigator">
          <h3 class="navigator-title">Danh sách câu hỏi</h3>
          <div class="dots-grid">
            <button
              v-for="(ans, i) in answers"
              :key="i"
              class="dot"
              :class="{ active: i === idx, done: isAnswered(ans) }"
              @click="go(i)"
            >{{ i + 1 }}</button>
          </div>
        </div>

        <div class="question-card-wrapper">
          <div v-if="q" class="question-card">
            <div class="q-header">
              <span class="q-number">Câu {{ idx + 1 }}</span>
              <span class="q-type">{{ q.type }}</span>
            </div>
            <div class="q-content">
              <template v-if="q.type === 'mcq'">
                <div class="q-text" v-html="q.text"></div>
                <ul class="q-options">
                  <li v-for="opt in q.options" :key="opt.key">
                    <label class="opt-label">
                      <input type="radio" :name="'q_' + idx" :value="opt.key" :checked="answers[idx] === opt.key" @change="setAnswer(idx, opt.key)" />
                      <span class="opt-key">{{ opt.key }}</span>
                      <span class="opt-text" v-html="opt.text"></span>
                    </label>
                  </li>
                </ul>
              </template>
              <template v-else-if="q.type === 'tf'">
                <div class="q-text" v-html="q.text"></div>
                <div class="q-tf-options">
                  <label class="opt-btn">
                    <input type="radio" :name="'q_' + idx" value="T" :checked="answers[idx] === 'T'" @change="setAnswer(idx, 'T')" />
                    <span>Đúng</span>
                  </label>
                  <label class="opt-btn">
                    <input type="radio" :name="'q_' + idx" value="F" :checked="answers[idx] === 'F'" @change="setAnswer(idx, 'F')" />
                    <span>Sai</span>
                  </label>
                </div>
              </template>
              <template v-else>
                <div class="q-text" v-html="q.text"></div>
                <input class="q-input-fill" :value="answers[idx] ?? ''" @input="setAnswer(idx, ($event.target as HTMLInputElement).value)" placeholder="Nhập câu trả lời của bạn..." />
              </template>
            </div>
          </div>
          <div class="card-footer">
            <button class="btn btn-secondary" :disabled="idx === 0" @click="prev">‹ Câu trước</button>
            <div v-if="idx === questions.length - 1 && questions.length > 0" class="submit-area">
              <span class="answered-count">{{ answeredCount }}/{{ questions.length }} câu đã trả lời</span>
              <button class="btn btn-danger" :disabled="submitting" @click="submit">
                {{ submitting ? 'Đang nộp…' : 'Nộp bài' }}
              </button>
            </div>
            <button v-else class="btn btn-primary" :disabled="idx === questions.length - 1" @click="next">Câu tiếp ›</button>
          </div>
        </div>
      </main>
    </div>

    <!-- Popup xác nhận nộp bài -->
    <transition name="fade">
      <div v-if="showSubmitModal" class="modal-backdrop" @click.self="showSubmitModal=false">
        <div class="modal-card" role="dialog" aria-modal="true">
          <header class="modal-header">
            <h3 class="modal-title">Xác nhận nộp bài</h3>
            <button class="modal-close" aria-label="Đóng" @click="showSubmitModal=false">×</button>
          </header>

          <section class="modal-body">
            <p v-html="submitMsg"></p>
          </section>

          <footer class="modal-footer">
            <button class="btn btn-secondary" :disabled="submitting" @click="showSubmitModal=false">
              Tiếp tục làm
            </button>
            <button class="btn btn-danger" :disabled="submitting" @click="confirmSubmit">
              {{ submitting ? 'Đang nộp…' : 'Nộp bài' }}
            </button>
          </footer>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, computed, shallowRef, ref, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// --- Dữ liệu cục bộ thay thế cho Store ---
const exams = ref([
  { id: 1, title: 'Đề thi thử TOEIC Reading Part 5', level: 'basic' as const, durationSec: 25 * 60, passCount: 20 },
  { id: 2, title: 'Kiểm tra kiến thức Vue.js nâng cao', level: 'advanced' as const, durationSec: 30 * 60, passCount: 25 },
  { id: 3, title: 'Đề thi thử cuối kỳ môn Lập trình Web', level: 'basic' as const, durationSec: 60 * 60, passCount: 36 }
]);

type Mcq = { type: 'mcq'; text: string; options: { key: string; text: string }[]; answer: string };
type Tf  = { type: 'tf';  text: string; answer: 'T' | 'F' };
type Fill = { type: 'fill'; text: string; answer: string };
type Q = Mcq | Tf | Fill;

const router = useRouter(); 
const route = useRoute();

const exam = computed(() => exams.value.find(x => String(x.id) === String(route.params.id)));

const loading = ref(true); 
const questions = shallowRef<Q[]>([]); 
const answers = shallowRef<(string | null)[]>([]); 
const idx = ref(0); 
const submitting = ref(false);
const duration = ref(exam.value?.durationSec || 20 * 60); 
const timeLeft = ref(duration.value); 
let timer: number | null = null;

const q = computed(() => questions.value[idx.value]);
const answeredCount = computed(() => answers.value.filter(v => (v ?? '').toString().trim() !== '').length);

function labelLevel(l?: 'basic' | 'advanced') { return l === 'advanced' ? 'Nâng cao' : 'Cơ bản' }
function fmtTime(s: number) { const m = Math.floor(s / 60); const ss = s % 60; return `${m.toString().padStart(2, '0')}:${ss.toString().padStart(2, '0')}` }

// ===== Popup nộp bài =====
const showSubmitModal = ref(false);
const submitMsg = computed(() => {
  const unanswered = questions.value.length - answeredCount.value;
  return unanswered > 0
    ? `Bạn còn <b>${unanswered}</b> câu chưa trả lời. Bạn có chắc chắn muốn nộp bài không?`
    : 'Bạn đã trả lời hết các câu hỏi. Xác nhận nộp bài?';
});

// Mở popup khi ấn nút "Nộp bài"
function submit() {
  showSubmitModal.value = true;
}

// Thực sự nộp bài khi người dùng xác nhận trong popup
async function confirmSubmit() {
  if (submitting.value) return; 
  submitting.value = true; 
  stopTimer(); 
  await nextTick();
  
  const userAnswersData = questions.value.map((question, index) => {
    return {
      questionText: question.text,
      userAnswer: (answers.value[index] ?? 'Chưa trả lời').toString().trim(),
      correctAnswer: question.answer,
      explanation: `Đây là giải thích cho câu ${index + 1}.` 
    };
  });

  showSubmitModal.value = false;
  
  router.push({ 
    name: 'student-exam-result',
    params: { id: route.params.id },
    state: {
      userAnswers: userAnswersData
    }
  });

  submitting.value = false;
}

// ===== Các hàm sẵn có =====
function goBack() { 
  if (window.confirm('Bạn có chắc chắn muốn thoát không? Mọi tiến trình làm bài sẽ không được lưu lại.')) {
    router.back();
  }
}
function go(i: number) { if (i >= 0 && i < questions.value.length) idx.value = i }
function next() { if (idx.value < questions.value.length - 1) idx.value++ }
function prev() { if (idx.value > 0) idx.value-- }
function isAnswered(v: string | null) { return (v ?? '').toString().trim() !== '' }
function stopTimer() { if (timer) { clearInterval(timer); timer = null } }

function setAnswer(i: number, val: string) { 
  const next = answers.value.slice(); 
  next[i] = val; 
  answers.value = next;
}

// Các hàm tạo câu hỏi mẫu
function makeMcq(i: number): Mcq { const letters = ['A', 'B', 'C', 'D']; const correct = letters[i % 4]; return { type: 'mcq', text: `Nội dung câu hỏi trắc nghiệm số <b>${i}</b>. Đâu là đáp án đúng cho phép tính: <b>${i} + ${i}</b>?`, options: letters.map(k => ({ key: k, text: (k === correct ? String(i + i) : String(i + i + (k.charCodeAt(0) % 3 - 1))) })), answer: correct } }
function makeTf(i: number): Tf { return { type: 'tf', text: `Xét tính đúng sai của mệnh đề sau: "<b>${i} là một số chẵn</b>"`, answer: (i % 2 === 0 ? 'T' : 'F') } }
function makeFill(i: number): Fill { return { type: 'fill', text: `Điền kết quả đúng cho phép tính sau: <b>${i} × 2</b>`, answer: String(i * 2) } }

async function buildQuestions(total = 60, chunk = 20) {
  const buffer: Q[] = []; 
  questions.value = []; 
  answers.value = [];
  for (let i = 1; i <= total; i++) {
    const t = i % 3 === 1 ? makeMcq(i) : i % 3 === 2 ? makeTf(i) : makeFill(i);
    buffer.push(t);
    if (i % chunk === 0 || i === total) {
      questions.value = questions.value.concat(buffer);
      answers.value = answers.value.concat(Array(buffer.length).fill(null));
      buffer.length = 0;
      await new Promise(r => requestAnimationFrame(() => r(null)));
    }
  }
}

onMounted(async () => {
  const numberOfQuestions = exam.value?.passCount ? exam.value.passCount + 10 : 60;
  await buildQuestions(numberOfQuestions, 20);
  
  loading.value = false;
  timeLeft.value = exam.value?.durationSec || 20 * 60;
  
  timer = window.setInterval(() => {
    timeLeft.value--;
    if (timeLeft.value <= 0) {
      clearInterval(timer!);
      // Hết giờ: tự động nộp (giữ đúng hành vi cũ, không hiện alert)
      confirmSubmit();
    }
  }, 1000) as unknown as number;
});

onBeforeUnmount(() => { 
  stopTimer(); 
});
</script>

<style scoped>
.exam-ui {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: #f8fafc;
  min-height: 100vh;
  color: #1e293b;
}
.exam-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.exam-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #e2e8f0; }
.exam-title { font-size: 28px; font-weight: 800; color: #0f172a; margin: 0 0 8px 0; }
.exam-meta { display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 14px; color: #64748b; margin: 0; }
.exam-meta span::after { content: '•'; margin-left: 16px; color: #cbd5e1; }
.exam-meta span:last-child::after { content: ''; }
.exam-tools { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.timer { display: flex; align-items: center; gap: 8px; background-color: #fff; border: 1px solid #e2e8f0; border-radius: 999px; padding: 8px 16px; font-weight: 700; font-size: 16px; font-variant-numeric: tabular-nums; transition: all 0.2s ease; }
.timer.danger { background-color: #fef2f2; border-color: #fecaca; color: #dc2626; }
.timer-icon { width: 20px; height: 20px; }
.skeleton-wrapper { border-radius: 16px; padding: 24px; }
.skeleton-line { height: 16px; background: #e2e8f0; border-radius: 8px; margin-bottom: 12px; }
.skeleton-box { height: 200px; background: #e2e8f0; border-radius: 12px; margin-top: 20px; }
.exam-main { display: grid; grid-template-columns: 320px 1fr; gap: 24px; align-items: flex-start; }
@media (max-width: 900px) { .exam-main { grid-template-columns: 1fr; } }
.question-navigator { position: sticky; top: 24px; background-color: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05); }
.navigator-title { margin: 0 0 16px 0; font-size: 16px; font-weight: 700; color: #334155; }
.dots-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.dot { width: 40px; height: 40px; border-radius: 10px; border: 1px solid #e2e8f0; background-color: #fff; font-weight: 700; font-size: 14px; cursor: pointer; transition: all 0.2s ease; display: grid; place-items: center; }
.dot:hover { background-color: #f1f5f9; border-color: #cbd5e1; }
.dot.done { background-color: #f0fdf4; border-color: #bbf7d0; color: #166534; }
.dot.active { background-color: #16a34a; border-color: #16a34a; color: #fff; box-shadow: 0 0 0 3px #bbf7d0; }
.question-card-wrapper { background-color: #fff; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05); }
.question-card { padding: 24px; }
.q-header { display: flex; gap: 10px; align-items: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #f1f5f9; }
.q-number { background-color: #16a34a; color: #fff; border-radius: 8px; font-weight: 700; padding: 6px 12px; font-size: 16px; }
.q-type { text-transform: uppercase; font-size: 12px; font-weight: 700; color: #64748b; background-color: #f1f5f9; padding: 4px 8px; border-radius: 6px; }
.q-text { font-size: 18px; line-height: 1.7; margin-bottom: 24px; }
.q-text :deep(b) { color: #0f172a; }
.q-options { display: grid; gap: 12px; list-style: none; padding: 0; }
.opt-label { display: flex; align-items: center; gap: 16px; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; cursor: pointer; transition: all 0.2s ease; }
.opt-label:hover { border-color: #94a3b8; }
.opt-label:has(input:checked) { border-color: #16a34a; background-color: #dcfce7; box-shadow: 0 0 0 2px #bbf7d0; }
.opt-key { width: 32px; height: 32px; border-radius: 8px; border: 1px solid #e2e8f0; background-color: #f8fafc; font-weight: 700; display: grid; place-items: center; flex-shrink: 0; }
.opt-label:has(input:checked) .opt-key { background-color: #16a34a; color: #fff; border-color: #16a34a; }
.opt-text { font-size: 16px; line-height: 1.6; }
.q-tf-options { display: flex; gap: 12px; }
.opt-btn { flex: 1; text-align: center; padding: 16px; border: 1px solid #e2e8f0; border-radius: 12px; cursor: pointer; font-weight: 700; font-size: 16px; transition: all 0.2s ease; }
.opt-btn:hover { border-color: #94a3b8; }
.opt-btn:has(input:checked) { border-color: #16a34a; background-color: #dcfce7; color: #166534; box-shadow: 0 0 0 2px #bbf7d0; }
.opt-btn input { position: absolute; opacity: 0; width: 0; height: 0; }
.q-input-fill { width: 100%; font-size: 16px; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; transition: all 0.2s ease; }
.q-input-fill:focus { border-color: #16a34a; box-shadow: 0 0 0 3px #bbf7d0; outline: none; }
.card-footer { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; }
.submit-area { display: flex; align-items: center; gap: 16px; }
.answered-count { font-size: 14px; font-weight: 500; color: #64748b; }
.btn { padding: 10px 20px; border-radius: 10px; font-weight: 700; font-size: 15px; cursor: pointer; border: 1px solid transparent; transition: all 0.2s ease; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-ghost { background-color: #fff; border-color: #e2e8f0; color: #334155; }
.btn-ghost:hover:not(:disabled) { background-color: #f1f5f9; }
.btn-secondary { background-color: #f1f5f9; color: #334155; }
.btn-secondary:hover:not(:disabled) { background-color: #e2e8f0; }
.btn-primary { background-color: #16a34a; color: #fff; }
.btn-primary:hover:not(:disabled) { background-color: #15803d; }
.btn-danger { background-color: #dc2626; color: #fff; }
.btn-danger:hover:not(:disabled) { background-color: #b91c1c; }

/* ===== Modal styles ===== */
.fade-enter-active, .fade-leave-active { transition: opacity .15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(15,23,42,.5); display: grid; place-items: center; z-index: 50; }
.modal-card { width: 100%; max-width: 520px; background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; box-shadow: 0 20px 50px rgba(2,6,23,.15); overflow: hidden; animation: pop .15s ease-out; }
@keyframes pop { from { transform: translateY(8px); opacity: .9 } to { transform: translateY(0); opacity: 1 } }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
.modal-title { margin: 0; font-size: 18px; font-weight: 800; color: #0f172a; }
.modal-close { background: transparent; border: 0; font-size: 24px; line-height: 1; cursor: pointer; color: #64748b; }
.modal-body { padding: 20px; color: #334155; font-size: 16px; }
.modal-footer { display: flex; gap: 12px; justify-content: flex-end; padding: 16px 20px; background: #f8fafc; border-top: 1px solid #f1f5f9; }
</style>
