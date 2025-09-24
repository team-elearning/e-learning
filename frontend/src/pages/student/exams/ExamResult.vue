<template>
  <div class="result-page">
    <div class="result-card" :class="resultStatus.class">
      <h1>Hoàn thành!</h1>
      <p class="lead">Đây là kết quả bài làm của bạn:</p>

      <div class="score-display">
        <span class="score-value">{{ score }}</span>
        <span class="score-total">/ {{ total }}</span>
      </div>
      
      <p class="percentage" :style="{ color: resultStatus.color }">
        Đạt {{ percentage.toFixed(0) }}%
      </p>

      <p class="message">{{ resultStatus.message }}</p>

      <div class="actions">
        <button class="btn ghost" @click="toggleReview">
          {{ showReview ? 'Ẩn đáp án' : 'Xem lại đáp án' }}
        </button>
        <router-link
          class="btn primary"
          :to="{ name: 'student-exams-ranking' }"
          style="color: black; border: 1px;" 

        >
          Xem bảng xếp hạng
        </router-link>
      </div>
    </div>

    <Transition name="fade">
      <div v-if="showReview" class="review-section">
        <div class="review-header">
          <h2>Chi tiết bài làm</h2>
          <p>Hiển thị {{ paginatedAnswers.length }} câu hỏi trên trang {{ currentPage }}</p>
        </div>
        
        <div 
          v-for="(answer, index) in paginatedAnswers" 
          :key="answer.originalIndex" 
          class="question-review"
          :class="{ correct: answer.userAnswer === answer.correctAnswer, incorrect: answer.userAnswer !== answer.correctAnswer }"
        >
          <div class="question-header">
            <strong>Câu {{ answer.originalIndex + 1 }}:</strong>
            <div class="q-text" v-html="answer.questionText"></div>
          </div>
          <div class="answer-details">
            <p>Đáp án của bạn: <span class="user-answer">{{ answer.userAnswer || 'Chưa trả lời' }}</span></p>
            <p>Đáp án đúng: <span class="correct-answer">{{ answer.correctAnswer }}</span></p>
          </div>
          <div v-if="answer.userAnswer !== answer.correctAnswer && answer.explanation" class="explanation">
            <strong>Giải thích:</strong> {{ answer.explanation }}
          </div>
        </div>

        <div v-if="totalPages > 1" class="pagination-controls">
          <button class="btn-page" :disabled="currentPage === 1" @click="prevPage">‹ Trang trước</button>
          <span class="page-info">Trang {{ currentPage }} / {{ totalPages }}</span>
          <button class="btn-page" :disabled="currentPage === totalPages" @click="nextPage">Trang sau ›</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';

const showReview = ref(false);
const userAnswers = ref<any[]>([]);

// --- Cấu hình Phân trang ---
const currentPage = ref(1);
const itemsPerPage = 10; // Hiển thị 10 câu mỗi trang

// Dữ liệu mẫu nếu không nhận được gì từ trang trước
const mockUserAnswers = [
  { questionText: 'Có lỗi xảy ra, không nhận được dữ liệu bài làm.', userAnswer: '', correctAnswer: '', explanation: 'Vui lòng quay lại và thử nộp bài lần nữa.' }
];

onMounted(() => {
  if (history.state && history.state.userAnswers) {
    userAnswers.value = history.state.userAnswers;
  } else {
    console.warn("Không tìm thấy dữ liệu bài làm, đang sử dụng dữ liệu giả (mock data).");
    userAnswers.value = mockUserAnswers;
  }
});

const total = computed(() => userAnswers.value.length);
const score = computed(() => userAnswers.value.filter(a => a.userAnswer === a.correctAnswer).length);
const percentage = computed(() => {
  if (total.value === 0 || userAnswers.value === mockUserAnswers) return 0;
  return (score.value / total.value) * 100;
});

const resultStatus = computed(() => {
  if (userAnswers.value === mockUserAnswers) {
    return { class: 'status-danger', message: 'Không thể tính toán kết quả.', color: '#ef4444' };
  }
  if (percentage.value >= 80) {
    return { class: 'status-success', message: 'Xuất sắc! Bạn đã làm rất tốt! 🎉', color: '#16a34a' };
  } else if (percentage.value >= 50) {
    return { class: 'status-warning', message: 'Khá tốt! Cùng cố gắng hơn ở lần sau nhé. 👍', color: '#f59e0b' };
  } else {
    return { class: 'status-danger', message: 'Đừng nản lòng, hãy xem lại và thử lại nhé! 💪', color: '#ef4444' };
  }
});

// --- Logic Phân trang ---
const totalPages = computed(() => Math.ceil(userAnswers.value.length / itemsPerPage));

const paginatedAnswers = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  // Thêm originalIndex để giữ đúng số thứ tự câu hỏi
  return userAnswers.value.slice(start, end).map((answer, index) => ({
    ...answer,
    originalIndex: start + index
  }));
});

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    scrollToReviewTop();
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    scrollToReviewTop();
  }
}

function toggleReview() {
  showReview.value = !showReview.value;
  // Reset về trang 1 mỗi khi mở lại
  if(showReview.value) {
    currentPage.value = 1;
  }
}

function scrollToReviewTop() {
  const reviewElement = document.querySelector('.review-section');
  if (reviewElement) {
    reviewElement.scrollIntoView({ behavior: 'smooth' });
  }
}
</script>

<style scoped>
/* Giữ nguyên style cũ và thêm style cho phân trang, transition */
:root{--success-color:#16a34a;--warning-color:#f59e0b;--danger-color:#ef4444;--text-primary:#1e293b;--text-secondary:#64748b;--bg-light:#f1f5f9;--border-color:#e2e8f0}.result-page{display:flex;flex-direction:column;align-items:center;min-height:100vh;background-color:var(--bg-light);padding:40px 20px;font-family:sans-serif}.result-card{background:#fff;border-radius:16px;padding:32px 40px;width:100%;max-width:560px;text-align:center;box-shadow:0 10px 15px -3px #0000001a,0 4px 6px -2px #0000000d;border-top:5px solid;transition:border-color .3s ease;margin-bottom:30px}.result-card.status-success{border-color:var(--success-color)}.result-card.status-warning{border-color:var(--warning-color)}.result-card.status-danger{border-color:var(--danger-color)}.icon-wrapper{margin:0 auto 16px;color:var(--text-secondary)}.status-success .icon-wrapper{color:var(--success-color)}.status-warning .icon-wrapper{color:var(--warning-color)}.status-danger .icon-wrapper{color:var(--danger-color)}h1{font-size:28px;font-weight:700;color:var(--text-primary);margin-bottom:8px}.lead{color:var(--text-secondary);font-size:16px;margin-bottom:24px}.score-display{margin-bottom:4px}.score-value{font-size:60px;font-weight:800;color:var(--text-primary);line-height:1}.score-total{font-size:24px;font-weight:600;color:var(--text-secondary)}.percentage{font-size:20px;font-weight:600;margin-bottom:16px}.message{font-size:16px;color:var(--text-secondary);min-height:40px;margin-bottom:32px}.actions{display:flex;gap:12px;justify-content:center}.btn{padding:12px 20px;border-radius:10px;font-weight:700;text-decoration:none;border:2px solid transparent;transition:all .2s ease-in-out;cursor:pointer}.btn.ghost{background-color:#fff;color:var(--text-secondary);border-color:var(--border-color)}.btn.ghost:hover{border-color:var(--text-primary);color:var(--text-primary);transform:translateY(-2px);box-shadow:0 4px 10px #00000014}.btn.primary{color:#fff}.status-success .btn.primary{background-color:var(--success-color)}.status-warning .btn.primary{background-color:var(--warning-color)}.status-danger .btn.primary{background-color:var(--danger-color)}.btn.primary:hover{transform:translateY(-2px);filter:brightness(1.1);box-shadow:0 4px 10px #0000001a}.review-section{background:#fff;border-radius:16px;padding:24px 32px;width:100%;max-width:800px;box-shadow:0 10px 15px -3px #0000001a,0 4px 6px -2px #0000000d}.review-header{text-align:center;margin-bottom:24px;border-bottom:1px solid var(--border-color);padding-bottom:16px}.review-header h2{font-size:24px;font-weight:700;color:var(--text-primary);margin-bottom:4px}.review-header p{color:var(--text-secondary);font-size:14px;margin:0}.question-review{padding:16px;border-radius:8px;margin-bottom:16px;border:1px solid var(--border-color);border-left-width:5px}.question-review.correct{border-left-color:var(--success-color);background-color:#f0fdf4}.question-review.incorrect{border-left-color:var(--danger-color);background-color:#fef2f2}.question-header{margin-bottom:12px;color:var(--text-primary);display:flex;gap:8px}.q-text{flex:1}.answer-details p{margin:4px 0;font-size:15px}.user-answer{font-weight:600;color:#475569}.incorrect .user-answer{color:var(--danger-color);text-decoration:line-through}.correct-answer{font-weight:600;color:var(--success-color)}.explanation{margin-top:12px;padding:10px;background-color:#fffbeb;border-radius:6px;font-size:14px;color:#78350f}

/* --- Style cho Phân trang và Transition --- */
.pagination-controls{display:flex;justify-content:space-between;align-items:center;padding-top:20px;margin-top:20px;border-top:1px solid var(--border-color)}.page-info{font-size:14px;font-weight:600;color:var(--text-secondary)}.btn-page{background-color:#fff;border:1px solid var(--border-color);color:var(--text-primary);padding:8px 16px;border-radius:8px;font-weight:600;cursor:pointer;transition:all .2s ease}.btn-page:hover:not(:disabled){background-color:#f8fafc;border-color:#cbd5e1}.btn-page:disabled{opacity:.5;cursor:not-allowed}
.fade-enter-active,.fade-leave-active{transition:opacity .3s ease,transform .3s ease}.fade-enter-from,.fade-leave-to{opacity:0;transform:translateY(20px)}
</style>