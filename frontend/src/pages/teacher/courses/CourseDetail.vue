<template>
  <div class="min-h-screen w-full bg-slate-50">
    <main class="mx-auto w-full max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10 md:py-8">
      <!-- Header -->
      <div
        class="mb-5 flex flex-col items-stretch justify-between gap-3 sm:flex-row sm:items-center"
      >
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            @click="goBack"
          >
            ‹
          </button>
          <div>
            <p class="text-xs uppercase tracking-wide text-slate-400">Chi tiết khoá học</p>
            <h1 class="text-xl font-semibold sm:text-2xl">
              <!-- course title states -->
              <span v-if="loading" class="block mt-1">
                <div class="w-28 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div class="h-full bg-emerald-400 animate-loading-bar origin-right"></div>
                </div>
              </span>
              <span v-else-if="error">Lỗi tải khoá học</span>
              <span v-else>{{ course?.title || 'Không có tiêu đề' }}</span>
            </h1>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            @click="goToList"
          >
            Quay lại danh sách
          </button>
          <button
            v-if="course"
            type="button"
            class="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700"
            @click="editCourse"
          >
            Sửa khoá học
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-4">
        <div class="h-40 w-full rounded-2xl bg-slate-200 animate-pulse" />
        <div class="h-4 w-1/2 rounded bg-slate-200 animate-pulse" />
        <div class="h-4 w-1/3 rounded bg-slate-200 animate-pulse" />
        <div class="h-32 w-full rounded-2xl bg-slate-200 animate-pulse" />
      </div>

      <!-- Error -->
      <div
        v-else-if="error"
        class="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700"
      >
        {{ error }}
      </div>

      <!-- Content -->
      <div v-else-if="course" class="space-y-6">
        <!-- Top info -->
        <section class="grid grid-cols-1 gap-4 lg:grid-cols-[280px,1fr]">
          <!-- Thumbnail -->
          <div
            class="h-48 w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 sm:h-56"
          >
            <!-- Có image_url -->
            <template v-if="course.image_url">
              <div
                v-if="coverLoading"
                class="flex h-full w-full items-center justify-center text-xs text-slate-400"
              >
                Đang tải ảnh bìa…
              </div>
              <div
                v-else-if="coverError"
                class="flex h-full w-full items-center justify-center px-3 text-center text-xs text-rose-600"
              >
                {{ coverError }}
              </div>
              <img
                v-else-if="coverBlobUrl"
                :src="coverBlobUrl"
                :alt="course.title"
                class="h-full w-full object-cover"
              />
              <div
                v-else
                class="flex h-full w-full items-center justify-center text-5xl text-slate-300"
              >
                🎓
              </div>
            </template>

            <!-- Không có image_url -->
            <template v-else>
              <div class="flex h-full w-full items-center justify-center text-5xl text-slate-300">
                🎓
              </div>
            </template>
          </div>

          <!-- Meta -->
          <div class="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
            <h2 class="mb-2 text-lg font-semibold">Thông tin chung</h2>

            <p class="text-sm text-slate-600">
              {{ course.description || 'Chưa có mô tả cho khoá học này.' }}
            </p>

            <div class="mt-4 flex flex-wrap items-center gap-2 text-xs">
              <span
                v-if="course.grade"
                class="rounded-full bg-sky-50 px-2.5 py-1 font-medium text-sky-700"
              >
                Lớp {{ course.grade }}
              </span>

              <span
                v-for="cat in course.categories"
                :key="cat"
                class="rounded-full bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700"
              >
                {{ cat }}
              </span>

              <span
                v-for="tag in course.tags"
                :key="tag"
                class="rounded-full bg-slate-100 px-2 py-1 text-slate-700"
              >
                #{{ tag }}
              </span>
            </div>

            <p class="mt-3 text-xs text-slate-500">{{ course.modules?.length || 0 }} chương học</p>
          </div>
        </section>

        <!-- Modules & lessons -->
        <section class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 lg:p-6">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-lg font-semibold text-slate-800">Nội dung khoá học</h2>
          </div>

          <div v-if="!course.modules || course.modules.length === 0" class="text-sm text-slate-500">
            Chưa có chương học nào trong khoá học này.
          </div>

          <div v-else class="space-y-4">
            <!-- Module -->
            <div
              v-for="(m, mIndex) in course.modules"
              :key="m.id || mIndex"
              class="rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <span
                    class="flex h-7 w-7 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700"
                  >
                    {{ mIndex + 1 }}
                  </span>
                  <div>
                    <p class="text-sm font-semibold text-slate-800">
                      {{ m.title || `Chương ${mIndex + 1}` }}
                    </p>
                    <p class="text-xs text-slate-500">{{ m.lessons?.length || 0 }} bài học</p>
                  </div>
                </div>
              </div>

              <!-- Lessons -->
              <div class="space-y-3">
                <div
                  v-for="(lesson, lIndex) in m.lessons"
                  :key="lesson.id || lIndex"
                  class="rounded-lg border border-slate-200 bg-white p-3"
                >
                  <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                      <span
                        class="inline-flex h-6 min-w-[1.5rem] items-center justify-center rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700"
                      >
                        B{{ lIndex + 1 }}
                      </span>
                      <p class="text-sm font-medium text-slate-800">
                        {{ lesson.title || `Bài ${lIndex + 1}` }}
                      </p>
                    </div>
                  </div>

                  <!-- Content blocks -->
                  <div
                    v-if="lesson.content_blocks && lesson.content_blocks.length"
                    class="space-y-3"
                  >
                    <div
                      v-for="(b, bIndex) in lesson.content_blocks"
                      :key="b.id || bIndex"
                      class="rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm"
                    >
                      <div class="mb-2 flex items-center justify-between">
                        <div class="flex items-center gap-2 text-[11px] uppercase tracking-wide">
                          <span class="font-semibold text-slate-500">Phần {{ bIndex + 1 }}</span>
                          <span class="text-slate-400">•</span>
                          <span class="font-medium text-slate-500">{{
                            blockTypeLabel(b.type)
                          }}</span>
                        </div>
                      </div>

                      <!-- TEXT -->
                      <div v-if="b.type === 'text'">
                        <p class="whitespace-pre-wrap text-sm text-slate-700">
                          {{ b.payload?.text }}
                        </p>
                      </div>

                      <!-- IMAGE -->
                      <div v-else-if="b.type === 'image'" class="space-y-2">
                        <div
                          class="flex max-h-72 w-full items-center justify-center overflow-hidden rounded-lg bg-slate-100"
                        >
                          <!-- Loading -->
                          <div
                            v-if="b._loading"
                            class="flex h-32 w-full items-center justify-center text-xs text-slate-400"
                          >
                            Đang tải hình ảnh…
                          </div>

                          <!-- Error -->
                          <div
                            v-else-if="b._error"
                            class="flex h-32 w-full items-center justify-center px-3 text-center text-xs text-rose-600"
                          >
                            {{ b._error }}
                          </div>

                          <!-- Loaded -->
                          <img
                            v-else-if="b.payload?._image_blob_url"
                            :src="b.payload._image_blob_url"
                            :alt="b.payload?.caption || 'Hình ảnh bài học'"
                            class="h-full w-full object-contain"
                          />
                          <div
                            v-else
                            class="flex h-32 w-full items-center justify-center text-slate-400"
                          >
                            Không có ảnh
                          </div>
                        </div>
                        <p v-if="b.payload?.caption" class="text-xs text-slate-500">
                          {{ b.payload.caption }}
                        </p>
                      </div>

                      <!-- VIDEO -->
                      <div v-else-if="b.type === 'video'" class="space-y-2">
                        <div
                          class="w-full max-h-72 rounded-lg bg-black flex items-center justify-center"
                        >
                          <!-- Loading -->
                          <p v-if="b._loading" class="text-xs text-slate-300">Đang tải video…</p>

                          <!-- Error -->
                          <p v-else-if="b._error" class="px-3 text-center text-xs text-rose-300">
                            {{ b._error }}
                          </p>

                          <!-- Loaded -->
                          <video
                            v-else-if="b.payload?._video_blob_url"
                            :src="b.payload._video_blob_url"
                            controls
                            class="w-full max-h-72 rounded-lg bg-black"
                          ></video>

                          <p v-else class="text-xs text-slate-300">Không tìm thấy video.</p>
                        </div>
                      </div>

                      <!-- PDF / DOCX -->
                      <div v-else-if="b.type === 'pdf' || b.type === 'docx'" class="space-y-2">
                        <div
                          class="flex items-center justify-between gap-2 rounded-md bg-white px-3 py-2 text-xs"
                        >
                          <div class="flex items-center gap-2">
                            <span class="text-lg">{{ b.type === 'pdf' ? '📄' : '📘' }}</span>
                            <div>
                              <p class="font-medium text-slate-800">
                                {{ b.payload?.filename || 'Tài liệu' }}
                              </p>
                              <p class="text-[11px] text-slate-500">{{ b.type.toUpperCase() }}</p>

                              <!-- Loading / Error trạng thái file -->
                              <p v-if="b._loading" class="mt-1 text-[11px] text-slate-400">
                                Đang tải file…
                              </p>
                              <p v-else-if="b._error" class="mt-1 text-[11px] text-rose-600">
                                {{ b._error }}
                              </p>
                            </div>
                          </div>

                          <div class="flex items-center gap-2">
                            <button
                              v-if="
                                (b.payload?._file_blob_url || b.payload?.file_url) &&
                                !b._loading &&
                                !b._error
                              "
                              type="button"
                              class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                              @click="openDocViewer(b)"
                            >
                              Xem trực tiếp
                            </button>

                            <span v-else-if="b._loading" class="text-[11px] text-slate-400">
                              Đang chuẩn bị file…
                            </span>

                            <span v-else-if="b._error" class="text-[11px] text-rose-500">
                              Lỗi tải file
                            </span>

                            <span v-else class="text-[11px] text-slate-400">Không có file</span>
                          </div>
                        </div>
                      </div>

                      <!-- QUIZ (dùng quiz_id) -->
                      <div v-else-if="b.type === 'quiz'" class="space-y-2">
                        <p class="text-sm font-semibold text-slate-800">Bài kiểm tra</p>
                        <p class="text-xs text-slate-500">
                          Mã bài kiểm tra:
                          <span class="font-mono text-slate-700">{{
                            b.payload?.quiz_id || '(không có)'
                          }}</span>
                        </p>
                        <button
                          type="button"
                          class="rounded-lg bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-700"
                          @click="openQuiz(b.payload?.quiz_id)"
                        >
                          Xem bài kiểm tra
                        </button>
                      </div>

                      <!-- OTHER / UNKNOWN -->
                      <div v-else class="text-xs text-slate-500">
                        Kiểu nội dung: {{ b.type }} (chưa hỗ trợ hiển thị chi tiết).
                      </div>
                    </div>
                  </div>

                  <p v-else class="text-xs text-slate-500">Bài học này chưa có nội dung.</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Không có course mà cũng không loading & không lỗi -->
      <div v-else class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
        Không tìm thấy dữ liệu khoá học.
      </div>

      <!-- ========= DOC VIEWER MODAL ========= -->
      <div
        v-if="docViewerOpen && docViewerUrl"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-3"
      >
        <div class="flex h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white">
          <div class="flex items-center justify-between border-b border-slate-200 px-4 py-2">
            <p class="text-sm font-semibold text-slate-800">
              Xem tài liệu {{ docViewerType?.toUpperCase() }}
            </p>
            <button
              type="button"
              class="rounded-full p-1 text-slate-500 hover:bg-slate-100"
              @click="closeDocViewer"
              aria-label="Đóng"
              title="Đóng"
            >
              ✕
            </button>
          </div>

          <div class="flex-1 bg-slate-100">
            <!-- PDF: iframe hiển thị trực tiếp -->
            <iframe
              v-if="docViewerType === 'pdf'"
              :src="docViewerUrl"
              class="h-full w-full"
            ></iframe>

            <!-- DOCX: thông báo + nút tải -->
            <div
              v-else-if="docViewerType === 'docx'"
              class="flex h-full flex-col items-center justify-center gap-3 px-4 text-center text-sm text-slate-600"
            >
              <p>Trình duyệt không hỗ trợ xem DOCX trực tiếp.</p>
              <p>Bạn có thể tải file về để mở bằng Word/Office.</p>
              <a
                :href="docViewerUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1 rounded-md bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-700"
              >
                Tải tài liệu
              </a>
            </div>
          </div>
        </div>
      </div>
      <!-- ========= END DOC VIEWER MODAL ========= -->

      <!-- ========= QUIZ MODAL ========= -->
      <transition
        enter-active-class="transition-opacity duration-150 ease-out"
        leave-active-class="transition-opacity duration-150 ease-in"
        enter-from-class="opacity-0"
        leave-to-class="opacity-0"
      >
        <div
          v-if="quizModal.open"
          class="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4"
          role="dialog"
          aria-modal="true"
          @click.self="closeQuiz"
        >
          <div
            class="max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl"
          >
            <!-- Header -->
            <div class="flex items-center justify-between border-b border-slate-200 px-5 py-3">
              <div class="flex flex-col gap-1">
                <p class="text-xs uppercase tracking-wide text-slate-400">Bài kiểm tra</p>

                <!-- Title: view / edit -->
                <div v-if="quizEditMode">
                  <input
                    v-model="quizModal.data!.title"
                    type="text"
                    class="w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                    placeholder="Tiêu đề bài kiểm tra"
                  />
                </div>
                <h3 v-else class="text-lg font-semibold text-slate-800">
                  <span v-if="quizModal.loading">Đang tải…</span>
                  <span v-else>{{ quizModal.data?.title || 'Đang tải…' }}</span>
                </h3>
              </div>

              <div class="flex items-center gap-3">
                <div v-if="quizModal.data" class="text-right">
                  <p class="text-[11px] text-slate-500">
                    Thời gian:
                    <span v-if="quizEditMode">
                      <input
                        v-model.number="quizTimeLimitMinutes"
                        type="number"
                        min="0"
                        class="w-16 rounded border border-slate-300 px-1 py-0.5 text-[11px] outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                      />
                      <span class="ml-1 text-slate-500">phút</span>
                    </span>
                    <span v-else class="font-medium text-slate-700">
                      {{ formatTimeLimit(quizModal.data.time_limit) }}
                    </span>
                  </p>
                </div>

                <button
                  type="button"
                  class="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                  @click="closeQuiz"
                  aria-label="Đóng"
                  title="Đóng"
                >
                  ✕
                </button>
              </div>
            </div>

            <!-- Body -->
            <div class="max-h-[70vh] overflow-y-auto px-5 py-4 text-sm">
              <!-- Loading -->
              <div v-if="quizModal.loading" class="space-y-3">
                <div class="h-4 w-2/3 rounded bg-slate-200 animate-pulse" />
                <div class="h-4 w-1/2 rounded bg-slate-200 animate-pulse" />
                <div class="mt-3 space-y-2">
                  <div class="h-3 w-full rounded bg-slate-200 animate-pulse" />
                  <div class="h-3 w-5/6 rounded bg-slate-200 animate-pulse" />
                  <div class="h-3 w-3/4 rounded bg-slate-200 animate-pulse" />
                </div>
              </div>

              <!-- Error -->
              <div
                v-else-if="quizModal.error"
                class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700"
              >
                {{ quizModal.error }}
              </div>

              <!-- Questions -->
              <div v-else-if="quizModal.data" class="space-y-4">
                <p class="text-xs text-slate-500">
                  Tổng số câu hỏi:
                  <span class="font-semibold text-slate-700">{{
                    quizModal.data.questions.length
                  }}</span>
                </p>

                <div
                  v-for="(q, qIndex) in quizModal.data.questions"
                  :key="q.id || qIndex"
                  class="rounded-lg border border-slate-200 bg-slate-50 p-3"
                >
                  <div class="mb-2 flex items-start justify-between gap-2">
                    <div class="flex-1">
                      <p class="text-xs font-semibold text-slate-500">Câu {{ qIndex + 1 }}</p>

                      <!-- prompt: view / edit -->
                      <div v-if="quizEditMode">
                        <textarea
                          v-model="q.prompt.text"
                          rows="2"
                          class="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                          placeholder="Nội dung câu hỏi..."
                        ></textarea>
                      </div>
                      <p v-else class="text-sm font-medium text-slate-800">
                        {{ q.prompt?.text }}
                      </p>
                    </div>

                    <span
                      class="rounded-full bg-sky-50 px-2 py-0.5 text-[11px] font-medium text-sky-700"
                    >
                      {{ questionTypeLabel(q.type) }}
                    </span>
                  </div>

                  <!-- multiple choice -->
                  <div
                    v-if="q.type === 'multiple_choice_single' || q.type === 'multiple_choice_multi'"
                    class="space-y-1.5 text-xs"
                  >
                    <!-- EDIT MODE -->
                    <template v-if="quizEditMode">
                      <div
                        v-for="(choice, cIndex) in q.answer_payload?.choices || []"
                        :key="choice.id || cIndex"
                        class="flex items-center gap-2 rounded-md bg-white px-2 py-1"
                      >
                        <!-- ID cố định a/b/c/d... -->
                        <div
                          class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700"
                        >
                          {{ String.fromCharCode(65 + cIndex) }}
                        </div>

                        <!-- Nội dung đáp án -->
                        <input
                          v-model="choice.text"
                          class="input-field flex-1 !px-2 !py-1 text-xs"
                          placeholder="Nội dung lựa chọn"
                        />

                        <!-- Đánh dấu đúng -->
                        <label class="flex items-center gap-1 text-[11px] text-slate-700">
                          <!-- single: chỉ 1 đúng -->
                          <input
                            v-if="q.type === 'multiple_choice_single'"
                            type="radio"
                            :name="`quiz-q-${qIndex}`"
                            :checked="choice.is_correct"
                            @change="setQuizSingleCorrect(q, cIndex)"
                          />
                          <!-- multi: nhiều đúng -->
                          <input
                            v-else
                            type="checkbox"
                            :checked="choice.is_correct"
                            @change="toggleQuizMultiCorrect(choice)"
                          />
                          <span>Đúng</span>
                        </label>

                        <!-- Xoá lựa chọn -->
                        <button
                          type="button"
                          class="px-1 text-sm text-rose-600 hover:text-rose-700"
                          @click="removeQuizChoice(q, cIndex)"
                        >
                          ✕
                        </button>
                      </div>

                      <button
                        type="button"
                        class="btn-secondary text-xs mt-1"
                        @click="addQuizChoice(q)"
                      >
                        + Thêm lựa chọn
                      </button>
                    </template>

                    <!-- VIEW MODE -->
                    <template v-else>
                      <div
                        v-for="choice in q.answer_payload?.choices || []"
                        :key="choice.id"
                        class="flex items-start gap-2 rounded-md px-2 py-1"
                        :class="
                          choice.is_correct ? 'bg-emerald-50 text-emerald-800' : 'text-slate-700'
                        "
                      >
                        <span class="mt-0.5 min-w-[1.5rem] font-mono">{{ choice.id }}</span>
                        <div class="flex-1">
                          <p>{{ choice.text || '(Không có nội dung)' }}</p>
                          <p
                            v-if="choice.is_correct"
                            class="text-[10px] font-semibold uppercase tracking-wide"
                          >
                            Đáp án đúng
                          </p>
                        </div>
                      </div>
                    </template>
                  </div>

                  <!-- true/false -->
                  <div v-else-if="q.type === 'true_false'" class="space-y-1 text-xs">
                    <template v-if="quizEditMode">
                      <p class="font-medium text-slate-700 mb-1">Chọn đáp án đúng:</p>
                      <label class="flex items-center gap-2">
                        <input type="radio" :value="true" v-model="q.answer_payload.answer" />
                        <span>Đúng</span>
                      </label>
                      <label class="flex items-center gap-2">
                        <input type="radio" :value="false" v-model="q.answer_payload.answer" />
                        <span>Sai</span>
                      </label>
                    </template>

                    <template v-else>
                      <p class="font-medium text-slate-700">Đáp án đúng:</p>
                      <p
                        class="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700"
                      >
                        {{ q.answer_payload?.answer ? 'Đúng' : 'Sai' }}
                      </p>
                    </template>
                  </div>

                  <!-- fill in the blank -->
                  <div v-else-if="q.type === 'fill_in_the_blank'" class="space-y-1 text-xs">
                    <template v-if="quizEditMode">
                      <p class="font-medium text-slate-700 mb-1">Đáp án cho các chỗ trống:</p>
                      <div
                        v-for="(blank, bIndex) in q.answer_payload?.blanks || []"
                        :key="blank.id || bIndex"
                        class="flex items-center gap-2 mb-1"
                      >
                        <input
                          v-model="blank.id"
                          class="input-field w-28 !px-2 !py-1 text-[11px]"
                          placeholder="BLANK_1"
                        />
                        <input
                          v-model="blank.answer"
                          class="input-field flex-1 !px-2 !py-1 text-[11px]"
                          placeholder="Đáp án"
                        />
                        <button
                          type="button"
                          class="px-1 text-xs text-rose-600 hover:text-rose-700"
                          @click="removeQuizBlank(q, bIndex)"
                        >
                          ✕
                        </button>
                      </div>
                      <button
                        type="button"
                        class="btn-secondary text-xs mt-1"
                        @click="addQuizBlank(q)"
                      >
                        + Thêm chỗ trống
                      </button>
                    </template>

                    <template v-else>
                      <p class="font-medium text-slate-700">Đáp án đúng:</p>
                      <ul class="list-disc pl-5">
                        <li
                          v-for="blank in q.answer_payload?.blanks || []"
                          :key="blank.id"
                          class="text-slate-700"
                        >
                          <span class="font-mono text-[11px]">{{ blank.id }}:</span>
                          <span class="ml-1 font-semibold">{{ blank.answer }}</span>
                        </li>
                      </ul>
                    </template>
                  </div>

                  <!-- fallback -->
                  <div v-else class="text-xs text-slate-500">
                    Chưa hỗ trợ hiển thị chi tiết cho loại câu hỏi này.
                  </div>

                  <!-- Hint -->
                  <div class="mt-2">
                    <label v-if="quizEditMode" class="block text-[11px] text-slate-600">
                      Gợi ý (tuỳ chọn)
                      <input
                        v-model="q.hint.text"
                        class="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 text-[11px] outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                        placeholder="Gợi ý cho học sinh..."
                      />
                    </label>
                    <p v-else-if="q.hint?.text" class="text-[11px] text-slate-500">
                      Gợi ý: {{ q.hint.text }}
                    </p>
                  </div>
                </div>
              </div>

              <div v-else class="text-xs text-slate-500">Không có dữ liệu bài kiểm tra.</div>
            </div>

            <!-- Footer -->
            <div
              class="flex items-center justify-between gap-2 border-t border-slate-200 px-5 py-3 text-xs"
            >
              <p v-if="quizSaveError" class="text-rose-600">
                {{ quizSaveError }}
              </p>
              <span v-else />

              <div class="flex items-center gap-2">
                <button
                  v-if="quizModal.data && !quizEditMode"
                  type="button"
                  class="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  @click="enterQuizEditMode"
                >
                  Sửa bài kiểm tra
                </button>

                <button
                  v-if="quizEditMode"
                  type="button"
                  class="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                  @click="cancelQuizEdit"
                  :disabled="quizSaving"
                >
                  Hủy
                </button>

                <button
                  v-if="quizEditMode"
                  type="button"
                  class="rounded-xl bg-sky-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-sky-700 disabled:opacity-60"
                  @click="saveQuiz"
                  :disabled="quizSaving"
                >
                  {{ quizSaving ? 'Đang lưu…' : 'Lưu thay đổi' }}
                </button>

                <button
                  type="button"
                  class="rounded-xl bg-slate-800 px-4 py-1.5 text-xs font-semibold text-white hover:bg-slate-900"
                  @click="closeQuiz"
                  :disabled="quizSaving"
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>
      <!-- ========= END QUIZ MODAL ========= -->
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

/* ========== AUTH HEADER ========== */
const getAuthHeaders = () => {
  const token = localStorage.getItem('access')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/* ========== TYPES ========== */
interface ContentBlock {
  id?: string
  type: string
  position: number
  payload: any
  // trạng thái media (thêm dynamic)
  _loading?: boolean
  _error?: string
}

interface Lesson {
  id?: string
  title: string
  position: number
  content_type: string
  published?: boolean
  content_blocks: ContentBlock[]
}
interface Module {
  id?: string
  title: string
  position: number
  lessons: Lesson[]
}
interface CourseDetail {
  id: string
  title: string
  description: string
  grade: string | null
  image_url: string | null
  subject: string | null
  slug: string
  categories: string[]
  tags: string[]
  modules: Module[]
}

/* Quiz types */
interface QuizChoice {
  id: string
  text: string
  is_correct: boolean
}
interface QuizQuestion {
  id: string
  position: number
  type: string
  prompt: { text: string }
  answer_payload: any
  hint: { text: string }
}
interface QuizDetail {
  id: string
  title: string
  time_limit: number | string | null
  time_open: string | null
  time_close: string | null
  questions: QuizQuestion[]
}

/* ========== STATE ========== */
const course = ref<CourseDetail | null>(null)
const loading = ref(false)
const error = ref('')

const coverBlobUrl = ref<string | null>(null)
const coverLoading = ref(false)
const coverError = ref('')

const blobUrls = new Set<string>() // track blob URLs to revoke

/* Doc viewer */
const docViewerOpen = ref(false)
const docViewerUrl = ref<string | null>(null)
const docViewerType = ref<'pdf' | 'docx' | null>(null)

/* Quiz modal */
const quizModal = ref<{
  open: boolean
  loading: boolean
  error: string
  data: QuizDetail | null
}>({
  open: false,
  loading: false,
  error: '',
  data: null,
})

/* Quiz edit state */
const quizEditMode = ref(false)
const quizSaving = ref(false)
const quizSaveError = ref('')
const quizTimeLimitMinutes = ref<number | null>(null)
let quizSnapshot: QuizDetail | null = null // dùng để rollback khi Hủy

/* ========== HELPERS ========== */
function blockTypeLabel(type: string) {
  switch (type) {
    case 'text':
      return 'Văn bản'
    case 'image':
      return 'Hình ảnh'
    case 'video':
      return 'Video'
    case 'pdf':
      return 'PDF'
    case 'docx':
      return 'DOCX'
    case 'quiz':
      return 'Bài kiểm tra'
    default:
      return type
  }
}
function questionTypeLabel(type: string) {
  switch (type) {
    case 'multiple_choice_single':
      return 'Chọn một đáp án'
    case 'multiple_choice_multi':
      return 'Chọn nhiều đáp án'
    case 'true_false':
      return 'Đúng / Sai'
    case 'fill_in_the_blank':
      return 'Điền vào chỗ trống'
    default:
      return type
  }
}

/** time_limit có thể là số giây (GET) hoặc chuỗi HH:MM:SS (PATCH response) */
function toSecondsFromTimeLimit(val: number | string | null | undefined): number | null {
  if (val == null) return null
  if (typeof val === 'number') return val
  const parts = val.split(':').map((p) => parseInt(p, 10))
  if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) return null
  const [h, m, s] = parts
  return h * 3600 + m * 60 + s
}

function formatTimeLimit(val: number | string | null | undefined) {
  const total = toSecondsFromTimeLimit(val)
  if (!total || total <= 0) return 'Không giới hạn'
  const m = Math.floor(total / 60)
  const s = total % 60
  if (m >= 60) {
    const h = Math.floor(m / 60)
    const mm = m % 60
    return `${h}h ${mm}m`
  }
  return `${m} phút${s ? ` ${s} giây` : ''}`
}

function minutesToHHMMSS(minutes: number | null): string | null {
  if (minutes == null || minutes < 0) return null
  const total = minutes * 60
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(h)}:${pad(m)}:${pad(s)}`
}

/* blob fetch with auth (image/video/file) */
async function fetchBlobUrl(path: string): Promise<string | null> {
  try {
    const res = await axios.get(path, {
      responseType: 'blob',
      headers: { ...getAuthHeaders() },
    })
    const url = URL.createObjectURL(res.data)
    blobUrls.add(url)
    return url
  } catch (e) {
    console.error('❌ Lỗi tải file blob:', path, e)
    return null
  }
}

/* Doc viewer */
function openDocViewer(block: ContentBlock) {
  const blobUrl = block.payload?._file_blob_url
  const rawUrl = block.payload?.file_url
  docViewerUrl.value = blobUrl || rawUrl || null
  docViewerType.value = (block.type === 'pdf' || block.type === 'docx' ? block.type : null) as
    | 'pdf'
    | 'docx'
    | null
  if (docViewerUrl.value && docViewerType.value) docViewerOpen.value = true
}
function closeDocViewer() {
  docViewerOpen.value = false
  docViewerUrl.value = null
  docViewerType.value = null
}

/* Quiz */
async function openQuiz(quizId?: string) {
  quizModal.value.open = true
  quizModal.value.loading = true
  quizModal.value.error = ''
  quizModal.value.data = null
  quizEditMode.value = false
  quizSaveError.value = ''
  quizTimeLimitMinutes.value = null
  quizSnapshot = null

  if (!quizId) {
    quizModal.value.loading = false
    quizModal.value.error = 'Không tìm thấy quiz_id trong payload.'
    return
  }

  try {
    const { data } = await axios.get<QuizDetail>(`/api/content/instructor/quizzes/${quizId}/`, {
      headers: { ...getAuthHeaders() },
    })
    quizModal.value.data = data

    const secs = toSecondsFromTimeLimit(data.time_limit)
    quizTimeLimitMinutes.value = secs != null ? Math.floor(secs / 60) : null
  } catch (e: any) {
    console.error('❌ Lỗi tải bài kiểm tra:', e)
    quizModal.value.error =
      e?.response?.data?.detail || e?.message || 'Không thể tải bài kiểm tra. Vui lòng thử lại.'
  } finally {
    quizModal.value.loading = false
  }
}
function closeQuiz() {
  if (quizSaving.value) return
  quizModal.value.open = false
  quizEditMode.value = false
  quizSaveError.value = ''
}

/* Quiz edit mode */
function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

function enterQuizEditMode() {
  if (!quizModal.value.data) return
  quizEditMode.value = true
  quizSaveError.value = ''
  quizSnapshot = deepClone(quizModal.value.data)
}

function cancelQuizEdit() {
  if (!quizModal.value.data || !quizSnapshot) {
    quizEditMode.value = false
    quizSaveError.value = ''
    return
  }
  quizModal.value.data = deepClone(quizSnapshot)
  const secs = toSecondsFromTimeLimit(quizModal.value.data.time_limit)
  quizTimeLimitMinutes.value = secs != null ? Math.floor(secs / 60) : null
  quizEditMode.value = false
  quizSaveError.value = ''
}

/* PATCH quiz */
async function saveQuiz() {
  if (!quizModal.value.data) return
  quizSaveError.value = ''
  quizSaving.value = true

  try {
    const qz = quizModal.value.data
    const timeStr = minutesToHHMMSS(quizTimeLimitMinutes.value)

    const payload: any = {
      title: qz.title,
      // nếu muốn giữ nguyên time_limit khi input null, có thể bỏ trường này đi:
      time_limit: timeStr,
      questions: qz.questions.map((q, idx) => ({
        id: q.id,
        position: idx,
        type: q.type,
        prompt: { text: q.prompt?.text || '' },
        answer_payload: q.answer_payload,
        hint: q.hint,
      })),
    }

    const { data } = await axios.patch(`/api/content/instructor/quizzes/${qz.id}/`, payload, {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    })

    // data.time_limit có thể là chuỗi "HH:MM:SS"
    const merged: QuizDetail = {
      ...qz,
      ...data,
      questions: data.questions ?? qz.questions,
    }
    quizModal.value.data = merged

    const secs = toSecondsFromTimeLimit(merged.time_limit)
    quizTimeLimitMinutes.value = secs != null ? Math.floor(secs / 60) : null

    quizEditMode.value = false
    quizSnapshot = deepClone(merged)
  } catch (e: any) {
    console.error('❌ Lỗi khi cập nhật bài kiểm tra:', e)
    quizSaveError.value =
      e?.response?.data?.detail ||
      e?.message ||
      'Có lỗi xảy ra khi lưu bài kiểm tra. Vui lòng thử lại.'
  } finally {
    quizSaving.value = false
  }
}

/* ========== FETCH COURSE ========== */
async function fetchCourse() {
  const id = route.params.id
  if (!id) {
    error.value = 'Không tìm thấy ID khoá học trên URL.'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const { data } = await axios.get<CourseDetail>(`/api/content/instructor/courses/${id}/`, {
      headers: { ...getAuthHeaders() },
    })
    course.value = data

    /* Cover image */
    if (course.value.image_url) {
      coverLoading.value = true
      coverError.value = ''
      fetchBlobUrl(course.value.image_url)
        .then((url) => {
          if (url) coverBlobUrl.value = url
          else coverError.value = 'Không thể tải ảnh bìa.'
        })
        .finally(() => {
          coverLoading.value = false
        })
    }

    // fetch blobs cho content blocks
    course.value.modules.forEach((m) => {
      m.lessons.forEach((lesson) => {
        lesson.content_blocks.forEach((b) => {
          const block = b as ContentBlock

          if (block.type === 'image' && block.payload?.image_url) {
            block._loading = true
            block._error = ''
            fetchBlobUrl(block.payload.image_url)
              .then((url) => {
                if (url) {
                  block.payload._image_blob_url = url
                } else {
                  block._error = 'Không thể tải hình ảnh.'
                }
              })
              .finally(() => {
                block._loading = false
              })
          }

          if (block.type === 'video' && block.payload?.video_url) {
            block._loading = true
            block._error = ''
            fetchBlobUrl(block.payload.video_url)
              .then((url) => {
                if (url) {
                  block.payload._video_blob_url = url
                } else {
                  block._error = 'Không thể tải video.'
                }
              })
              .finally(() => {
                block._loading = false
              })
          }

          if ((block.type === 'pdf' || block.type === 'docx') && block.payload?.file_url) {
            block._loading = true
            block._error = ''
            fetchBlobUrl(block.payload.file_url)
              .then((url) => {
                if (url) {
                  block.payload._file_blob_url = url
                } else {
                  block._error = 'Không thể tải file tài liệu.'
                }
              })
              .finally(() => {
                block._loading = false
              })
          }
        })
      })
    })
  } catch (e: any) {
    console.error('❌ Lỗi tải chi tiết khoá học:', e)
    error.value =
      e?.response?.data?.detail ||
      e?.message ||
      'Không thể tải chi tiết khoá học. Vui lòng thử lại.'
  } finally {
    loading.value = false
  }
}

/* ========== NAV ========== */
function goBack() {
  router.back()
}
function goToList() {
  router.push({ path: '/teacher/courses' })
}
function editCourse() {
  if (!course.value) return
  router.push({ path: `/teacher/courses/${course.value.id}/edit` })
}

/* ========== INIT & CLEANUP ========== */
onMounted(() => {
  fetchCourse()
})
onBeforeUnmount(() => {
  blobUrls.forEach((u) => URL.revokeObjectURL(u))
  blobUrls.clear()
})

/* ===== Helper chỉnh đáp án trong modal quiz ===== */

function ensureChoicesArray(q: QuizQuestion) {
  if (!q.answer_payload) q.answer_payload = {}
  if (!Array.isArray(q.answer_payload.choices)) {
    q.answer_payload.choices = []
  }
}

function addQuizChoice(q: QuizQuestion) {
  ensureChoicesArray(q)
  const idx = q.answer_payload.choices.length
  const id = String.fromCharCode(97 + idx) // a, b, c, ...
  q.answer_payload.choices.push({
    id,
    text: '',
    is_correct: false,
  } as QuizChoice)
}

function removeQuizChoice(q: QuizQuestion, index: number) {
  if (!q.answer_payload?.choices) return
  q.answer_payload.choices.splice(index, 1)
  // đánh lại id a, b, c,...
  q.answer_payload.choices.forEach((choice: QuizChoice, i: number) => {
    choice.id = String.fromCharCode(97 + i)
  })
}

function setQuizSingleCorrect(q: QuizQuestion, index: number) {
  if (!q.answer_payload?.choices) return
  q.answer_payload.choices.forEach((choice: QuizChoice, i: number) => {
    choice.is_correct = i === index
  })
}

function toggleQuizMultiCorrect(choice: QuizChoice) {
  choice.is_correct = !choice.is_correct
}

function ensureBlanksArray(q: QuizQuestion) {
  if (!q.answer_payload) q.answer_payload = {}
  if (!Array.isArray(q.answer_payload.blanks)) {
    q.answer_payload.blanks = []
  }
}

function addQuizBlank(q: QuizQuestion) {
  ensureBlanksArray(q)
  const idx = q.answer_payload.blanks.length
  q.answer_payload.blanks.push({
    id: `BLANK_${idx + 1}`,
    answer: '',
  })
}

function removeQuizBlank(q: QuizQuestion, index: number) {
  if (!q.answer_payload?.blanks) return
  q.answer_payload.blanks.splice(index, 1)
}
</script>

<style scoped>
h1 {
  word-break: break-word;
}
@keyframes loading-bar {
  0% {
    transform: translateX(0%);
  }
  100% {
    transform: translateX(-100%);
  }
}
</style>
