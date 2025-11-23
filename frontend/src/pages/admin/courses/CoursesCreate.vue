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
            <p class="text-xs uppercase tracking-wide text-slate-400">Tạo khoá học (Admin)</p>
            <h1 class="text-xl font-semibold sm:text-2xl">Khoá học mới</h1>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            @click="goToList"
          >
            Về danh sách khoá học
          </button>
        </div>
      </div>

      <!-- Content -->
      <form class="grid grid-cols-1 gap-6 lg:grid-cols-[280px,1fr]" @submit.prevent="submit">
        <!-- Thumbnail & info ngắn -->
        <section class="space-y-4">
          <!-- Thumbnail -->
          <div
            class="h-48 w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 sm:h-56"
          >
            <img
              v-if="coverBlobUrl"
              :src="coverBlobUrl"
              :alt="f.title || 'Ảnh khoá học'"
              class="h-full w-full object-cover"
            />
            <div
              v-else
              class="flex h-full w-full items-center justify-center text-5xl text-slate-300"
            >
              🎓
            </div>
          </div>

          <!-- Upload ảnh bìa -->
          <div class="rounded-2xl border border-slate-200 bg-white p-4">
            <h2 class="mb-2 text-sm font-semibold text-slate-800">Ảnh khoá học</h2>
            <p class="mb-3 text-xs text-slate-500">
              Ảnh bìa hiển thị trong danh sách và trang chi tiết khoá học (tuỳ chọn).
            </p>

            <input
              ref="coverInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="onPickCover"
            />

            <div class="flex items-center gap-3">
              <button
                type="button"
                class="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                @click="coverInput?.click()"
              >
                Chọn ảnh bìa
              </button>

              <span v-if="coverFileName" class="text-xs text-slate-600">
                {{ coverFileName }}
              </span>
              <span v-else class="text-xs text-slate-400"> Chưa chọn ảnh. </span>
            </div>

            <p class="mt-2 text-[11px] text-slate-400">Hỗ trợ JPG/PNG, tối đa 2MB.</p>
            <p v-if="coverErr" class="mt-2 text-xs font-medium text-rose-600">
              {{ coverErr }}
            </p>
          </div>

          <!-- Thông tin nhanh -->
          <div class="rounded-2xl border border-slate-200 bg-white p-4 text-xs">
            <p class="font-semibold text-slate-700">Tóm tắt</p>
            <p class="mt-1 text-slate-500">
              Lớp:
              <span class="font-medium text-slate-700">
                {{ f.grade || 'Chưa chọn' }}
              </span>
            </p>
            <p class="mt-1 text-slate-500">
              Môn:
              <span class="font-medium text-slate-700">
                {{ f.subject || 'Chưa chọn' }}
              </span>
            </p>
            <p class="mt-1 text-slate-500">
              Số chương:
              <span class="font-medium text-slate-700">
                {{ f.modules.length }}
              </span>
            </p>
            <p class="mt-1 text-slate-500">
              Xuất bản:
              <span
                class="font-medium"
                :class="f.published ? 'text-emerald-600' : 'text-slate-600'"
              >
                {{ f.published ? 'Có' : 'Không' }}
              </span>
            </p>
          </div>
        </section>

        <!-- Form chi tiết -->
        <section class="space-y-5 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
          <!-- Tên khoá học -->
          <div>
            <label class="mb-1 block text-sm font-semibold text-slate-800">
              Tên khoá học <span class="text-rose-600">*</span>
            </label>
            <input
              v-model.trim="f.title"
              type="text"
              class="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              :class="titleErr ? 'border-rose-500 ring-rose-500' : 'border-slate-300'"
              placeholder="Ví dụ: Toán 5 - cơ bản"
              @input="titleErr = ''"
            />
            <p v-if="titleErr" class="mt-1 text-xs font-medium text-rose-600">
              {{ titleErr }}
            </p>
          </div>

          <!-- Môn & khối + xuất bản -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label class="mb-1 block text-sm font-semibold text-slate-800"> Môn học </label>
              <select
                v-model="f.subject"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              >
                <option value="">Chọn môn</option>
                <option value="Toán">Toán</option>
                <option value="Tiếng Việt">Tiếng Việt</option>
                <option value="Tiếng Anh">Tiếng Anh</option>
                <option value="Khoa học">Khoa học</option>
                <option value="Lịch sử">Lịch sử</option>
              </select>
            </div>

            <div>
              <label class="mb-1 block text-sm font-semibold text-slate-800"> Khối lớp </label>
              <select
                v-model="f.grade"
                class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              >
                <option value="1">Lớp 1</option>
                <option value="2">Lớp 2</option>
                <option value="3">Lớp 3</option>
                <option value="4">Lớp 4</option>
                <option value="5">Lớp 5</option>
              </select>
            </div>

            <div class="flex items-center gap-2 pt-5 sm:pt-7">
              <input
                id="published"
                v-model="f.published"
                type="checkbox"
                class="h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
              />
              <label for="published" class="text-sm text-slate-700">Xuất bản ngay</label>
            </div>
          </div>

          <!-- Mô tả -->
          <div>
            <label class="mb-1 block text-sm font-semibold text-slate-800"> Mô tả </label>
            <textarea
              v-model.trim="f.description"
              rows="4"
              class="w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              placeholder="Mô tả chi tiết về khoá học..."
            ></textarea>
          </div>

          <!-- Tags -->
          <div>
            <label class="mb-1 block text-sm font-semibold text-slate-800">
              Tags
              <span class="text-xs font-normal text-slate-500">(phân cách bằng dấu phẩy)</span>
            </label>
            <input
              v-model="tagsInput"
              type="text"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              placeholder="Ví dụ: toan, lop 5, canh dieu"
              @input="updateTags"
            />
            <p class="mt-1 text-[11px] text-slate-500">
              Tags giúp học sinh tìm kiếm khoá học dễ hơn.
            </p>
          </div>

          <!-- CHƯƠNG / BÀI HỌC + NỘI DUNG -->
          <div class="form-field md:col-span-2">
            <div class="mb-4 flex items-center justify-between">
              <span class="label-text">Cấu trúc khoá học (Chương / Bài / Nội dung)</span>
              <button type="button" class="btn-secondary" @click="addModule">+ Thêm chương</button>
            </div>

            <!-- Không có module -->
            <div v-if="!f.modules.length" class="module-card-empty">
              Chưa có chương nào. Nhấn
              <span class="font-semibold text-slate-700">“Thêm chương”</span>
              để bắt đầu xây dựng nội dung khoá học.
            </div>

            <!-- Danh sách module -->
            <div v-else>
              <div
                v-for="(module, moduleIndex) in f.modules"
                :key="moduleIndex"
                class="module-card"
              >
                <!-- Header module -->
                <div class="module-header">
                  <div class="flex items-start gap-2">
                    <span
                      class="inline-flex h-7 w-7 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700"
                    >
                      {{ moduleIndex + 1 }}
                    </span>

                    <div class="flex-1">
                      <label class="mb-1 block">
                        <span class="label-text">Tên chương</span>
                        <input
                          v-model.trim="module.title"
                          class="input-field"
                          :placeholder="`Chương ${moduleIndex + 1}`"
                        />
                      </label>
                      <p class="text-[11px] text-slate-500">
                        {{ module.lessons.length }} bài học • vị trí: {{ module.position }}
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    class="text-xs font-medium text-rose-600 hover:text-rose-700 hover:underline"
                    @click="removeModule(moduleIndex)"
                  >
                    Xoá chương
                  </button>
                </div>

                <!-- LESSONS -->
                <div class="lessons-section">
                  <div class="mb-3 flex items-center justify-between">
                    <span class="label-text">Bài học ({{ module.lessons.length }})</span>
                    <button
                      type="button"
                      class="btn-secondary text-xs"
                      @click="addLesson(moduleIndex)"
                    >
                      + Thêm bài học
                    </button>
                  </div>

                  <!-- Không có bài -->
                  <div v-if="!module.lessons.length" class="lesson-card-empty">
                    Chưa có bài học nào trong chương này.
                  </div>

                  <!-- Danh sách bài -->
                  <div v-else class="space-y-3">
                    <div
                      v-for="(lesson, lessonIndex) in module.lessons"
                      :key="lessonIndex"
                      class="lesson-card"
                    >
                      <div class="lesson-header">
                        <div class="flex items-start gap-2">
                          <span
                            class="inline-flex h-5 min-w-[1.4rem] items-center justify-center rounded-full bg-slate-200 text-[10px] font-semibold text-slate-700"
                          >
                            B{{ lessonIndex + 1 }}
                          </span>

                          <div class="flex-1">
                            <label class="mb-1 block">
                              <span class="label-text">Tiêu đề bài học</span>
                              <input
                                v-model.trim="lesson.title"
                                class="input-field"
                                :placeholder="`Bài ${lessonIndex + 1}`"
                              />
                            </label>
                            <p class="text-[10px] text-slate-500">
                              {{ lesson.content_blocks?.length || 0 }} nội dung (text / hình / video
                              / file / quiz ...)
                            </p>
                          </div>
                        </div>

                        <button
                          type="button"
                          class="text-[11px] font-medium text-rose-600 hover:text-rose-700 hover:underline"
                          @click="removeLesson(moduleIndex, lessonIndex)"
                        >
                          Xoá
                        </button>
                      </div>

                      <!-- NỘI DUNG BÀI HỌC (content_blocks) -->
                      <div class="lesson-content">
                        <div class="content-blocks-section">
                          <div class="mb-3 flex items-center justify-between">
                            <span class="label-text">Nội dung bài học</span>
                            <button
                              type="button"
                              class="btn-secondary text-sm"
                              @click="addContentBlock(moduleIndex, lessonIndex)"
                            >
                              + Thêm nội dung
                            </button>
                          </div>

                          <div
                            v-for="(block, blockIndex) in lesson.content_blocks"
                            :key="blockIndex"
                            class="content-block-card"
                          >
                            <div class="content-block-header">
                              <div class="flex items-center gap-2">
                                <span class="text-sm font-medium text-slate-800">
                                  Phần {{ blockIndex + 1 }}
                                </span>
                                <span class="text-[11px] uppercase tracking-wide text-slate-400">
                                  •
                                  {{
                                    block.type === 'text'
                                      ? 'Văn bản'
                                      : block.type === 'image'
                                        ? 'Hình ảnh'
                                        : block.type === 'video'
                                          ? 'Video'
                                          : block.type === 'pdf'
                                            ? 'PDF'
                                            : block.type === 'docx'
                                              ? 'DOCX'
                                              : block.type === 'quiz'
                                                ? 'Bài kiểm tra'
                                                : block.type
                                  }}
                                </span>
                              </div>

                              <button
                                type="button"
                                class="text-rose-600 hover:text-rose-700"
                                @click="removeContentBlock(moduleIndex, lessonIndex, blockIndex)"
                              >
                                ✕
                              </button>
                            </div>

                            <div class="content-block-body">
                              <!-- Loại nội dung -->
                              <label class="mb-3 block">
                                <span class="label-text">Loại nội dung</span>
                                <select
                                  v-model="block.type"
                                  class="input-field"
                                  @change="resetBlockPayload(block)"
                                >
                                  <option value="text">Văn bản</option>
                                  <option value="image">Hình ảnh</option>
                                  <option value="video">Video</option>
                                  <option value="pdf">PDF</option>
                                  <option value="docx">DOCX</option>
                                  <option value="quiz">Bài kiểm tra</option>
                                </select>
                              </label>

                              <!-- TEXT -->
                              <div v-if="block.type === 'text'" class="space-y-3">
                                <label class="block">
                                  <span class="label-text">Nội dung văn bản</span>
                                  <textarea
                                    v-model="block.payload.text"
                                    rows="3"
                                    class="input-field resize-y"
                                    placeholder="Nhập nội dung văn bản..."
                                  ></textarea>
                                </label>
                              </div>

                              <!-- IMAGE -->
                              <div v-else-if="block.type === 'image'" class="space-y-3">
                                <div class="file-upload-area">
                                  <input
                                    :ref="
                                      (el) =>
                                        setFileInputRef(
                                          el,
                                          'image',
                                          moduleIndex,
                                          lessonIndex,
                                          blockIndex,
                                        )
                                    "
                                    type="file"
                                    accept="image/*"
                                    class="hidden"
                                    @change="
                                      (e) =>
                                        handleFileUpload(
                                          e,
                                          'image',
                                          moduleIndex,
                                          lessonIndex,
                                          blockIndex,
                                        )
                                    "
                                  />
                                  <button
                                    type="button"
                                    class="btn-secondary"
                                    @click="
                                      triggerFileInput(
                                        'image',
                                        moduleIndex,
                                        lessonIndex,
                                        blockIndex,
                                      )
                                    "
                                  >
                                    Chọn hình ảnh
                                  </button>
                                  <span v-if="block.payload.image_file" class="file-info">
                                    {{ block.payload.image_file.name }} —
                                    {{ Math.round(block.payload.image_file.size / 1024) }} KB
                                  </span>
                                  <span v-else class="file-info text-gray-500">
                                    Chưa có ảnh nào được chọn
                                  </span>
                                </div>

                                <img
                                  v-if="block.payload.image_preview"
                                  :src="block.payload.image_preview"
                                  alt="Xem trước ảnh"
                                  class="image-preview-small"
                                />

                                <label class="block">
                                  <span class="label-text">Chú thích</span>
                                  <input
                                    v-model="block.payload.caption"
                                    class="input-field"
                                    placeholder="Hình ảnh minh họa"
                                  />
                                </label>
                                <p class="hint-text">Hỗ trợ: JPG/PNG. Tối đa 5MB.</p>
                              </div>

                              <!-- VIDEO -->
                              <!-- VIDEO -->
                              <div v-else-if="block.type === 'video'" class="space-y-3">
                                <div class="file-upload-area">
                                  <input
                                    :ref="
                                      (el) =>
                                        setFileInputRef(
                                          el,
                                          'video',
                                          moduleIndex,
                                          lessonIndex,
                                          blockIndex,
                                        )
                                    "
                                    type="file"
                                    accept="video/*"
                                    class="hidden"
                                    @change="
                                      (e) =>
                                        handleFileUpload(
                                          e,
                                          'video',
                                          moduleIndex,
                                          lessonIndex,
                                          blockIndex,
                                        )
                                    "
                                  />
                                  <button
                                    type="button"
                                    class="btn-secondary"
                                    @click="
                                      triggerFileInput(
                                        'video',
                                        moduleIndex,
                                        lessonIndex,
                                        blockIndex,
                                      )
                                    "
                                  >
                                    Chọn video
                                  </button>

                                  <span v-if="block.payload.video_file" class="file-info">
                                    {{ block.payload.video_file.name }} —
                                    {{ (block.payload.video_file.size / 1024 / 1024).toFixed(1) }}
                                    MB
                                  </span>
                                  <span v-else class="file-info text-gray-500"
                                    >Chưa có video nào được chọn</span
                                  >
                                </div>

                                <video
                                  v-if="block.payload.video_preview"
                                  :src="block.payload.video_preview"
                                  controls
                                  class="video-preview-small"
                                ></video>

                                <!-- NEW PROGRESS BAR -->
                                <div v-if="block.payload.uploading" class="mt-2 space-y-1">
                                  <p class="text-xs text-gray-600">
                                    Upload video... {{ block.payload.progress }}%
                                  </p>

                                  <div class="w-full h-2 rounded bg-gray-200 overflow-hidden">
                                    <div
                                      class="h-full bg-blue-500 transition-all duration-200"
                                      :style="{ width: block.payload.progress + '%' }"
                                    ></div>
                                  </div>
                                </div>

                                <p class="hint-text">Hỗ trợ: MP4, WebM, MOV. Tối đa 200MB.</p>
                              </div>

                              <!-- PDF / DOCX -->
                              <div
                                v-else-if="['pdf', 'docx'].includes(block.type)"
                                class="space-y-3"
                              >
                                <div class="file-upload-area">
                                  <input
                                    :ref="
                                      (el) =>
                                        setFileInputRef(
                                          el,
                                          'file',
                                          moduleIndex,
                                          lessonIndex,
                                          blockIndex,
                                        )
                                    "
                                    type="file"
                                    :accept="block.type === 'pdf' ? '.pdf' : '.docx,.doc'"
                                    class="hidden"
                                    @change="
                                      (e) =>
                                        handleFileUpload(
                                          e,
                                          'file',
                                          moduleIndex,
                                          lessonIndex,
                                          blockIndex,
                                        )
                                    "
                                  />
                                  <button
                                    type="button"
                                    class="btn-secondary"
                                    @click="
                                      triggerFileInput('file', moduleIndex, lessonIndex, blockIndex)
                                    "
                                  >
                                    Chọn file {{ block.type.toUpperCase() }}
                                  </button>
                                  <span v-if="block.payload.file" class="file-info">
                                    {{ block.payload.file.name }} —
                                    {{ Math.round(block.payload.file.size / 1024) }} KB
                                  </span>
                                  <span v-else class="file-info text-gray-500">
                                    Chưa có file nào được chọn
                                  </span>
                                </div>

                                <label v-if="block.type === 'pdf'" class="block">
                                  <span class="label-text">Tên file (tuỳ chọn)</span>
                                  <input
                                    v-model="block.payload.filename"
                                    class="input-field"
                                    placeholder="Tóm tắt lý thuyết.pdf"
                                  />
                                </label>

                                <p class="hint-text">
                                  {{
                                    block.type === 'pdf'
                                      ? 'Hỗ trợ: PDF. Tối đa 10MB.'
                                      : 'Hỗ trợ: DOCX, DOC. Tối đa 5MB.'
                                  }}
                                </p>
                              </div>

                              <!-- QUIZ (giữ payload tự do) -->
                              <!-- QUIZ -->
                              <div v-else-if="block.type === 'quiz'" class="space-y-3 text-xs">
                                <!-- Tiêu đề quiz -->
                                <label class="block">
                                  <span class="label-text">Tiêu đề bài kiểm tra</span>
                                  <input
                                    v-model="block.payload.title"
                                    class="input-field"
                                    placeholder="Ví dụ: Bài tập tổng hợp chương 2"
                                  />
                                </label>

                                <!-- Thời gian -->
                                <label class="block">
                                  <span class="label-text">Thời gian (HH:MM:SS)</span>
                                  <input
                                    v-model="block.payload.time_limit"
                                    class="input-field"
                                    placeholder="00:30:00"
                                  />
                                </label>

                                <!-- CÂU HỎI -->
                                <div class="mt-3">
                                  <div class="flex items-center justify-between mb-2">
                                    <span class="label-text">Danh sách câu hỏi</span>
                                    <button
                                      type="button"
                                      class="btn-secondary"
                                      @click="addQuestion(block)"
                                    >
                                      + Thêm câu hỏi
                                    </button>
                                  </div>

                                  <div
                                    v-for="(question, qIndex) in block.payload.questions"
                                    :key="qIndex"
                                    class="rounded border border-gray-200 p-3 mt-2 bg-white"
                                  >
                                    <div class="flex justify-between mb-2">
                                      <span class="font-medium text-gray-700 text-sm"
                                        >Câu {{ qIndex + 1 }}</span
                                      >
                                      <button
                                        type="button"
                                        class="text-rose-600 text-xs"
                                        @click="removeQuestion(block, qIndex)"
                                      >
                                        ✕
                                      </button>
                                    </div>

                                    <!-- Loại câu hỏi -->
                                    <label class="block mb-2">
                                      <span class="label-text">Loại câu hỏi</span>
                                      <select
                                        v-model="question.type"
                                        class="input-field"
                                        @change="resetQuestionPayload(question)"
                                      >
                                        <option value="multiple_choice_single">
                                          Chọn 1 đáp án
                                        </option>
                                        <option value="multiple_choice_multi">
                                          Chọn nhiều đáp án
                                        </option>
                                        <option value="true_false">Đúng / Sai</option>
                                        <option value="short_answer">Tự luận ngắn</option>
                                      </select>
                                    </label>

                                    <!-- Nội dung câu hỏi -->
                                    <label class="block mb-2">
                                      <span class="label-text">Nội dung câu hỏi</span>
                                      <textarea
                                        v-model="question.prompt.text"
                                        rows="2"
                                        class="input-field resize-y"
                                        placeholder="Nhập nội dung câu hỏi..."
                                      ></textarea>
                                    </label>

                                    <!-- Multiple choice -->
                                    <div
                                      v-if="
                                        question.type === 'multiple_choice_single' ||
                                        question.type === 'multiple_choice_multi'
                                      "
                                      class="space-y-2"
                                    >
                                      <span class="label-text">Các lựa chọn</span>

                                      <div
                                        v-for="(choice, cIndex) in question.answer_payload.choices"
                                        :key="cIndex"
                                        class="flex items-center gap-2"
                                      >
                                        <div
                                          class="flex h-6 w-6 items-center justify-center rounded-full bg-gray-200 text-xs font-semibold text-gray-700"
                                        >
                                          {{ String.fromCharCode(65 + cIndex) }}
                                        </div>

                                        <input
                                          v-model="choice.text"
                                          class="input-field flex-1"
                                          placeholder="Nội dung lựa chọn"
                                        />

                                        <label
                                          class="flex items-center gap-1 text-xs text-gray-600"
                                        >
                                          <input
                                            v-if="question.type === 'multiple_choice_single'"
                                            type="radio"
                                            :name="'q-' + qIndex"
                                            :checked="choice.is_correct"
                                            @change="setCorrectChoice(question, cIndex)"
                                          />

                                          <input
                                            v-else
                                            type="checkbox"
                                            :checked="choice.is_correct"
                                            @change="toggleMultiCorrect(choice)"
                                          />
                                          <span>Đúng</span>
                                        </label>

                                        <button
                                          class="text-rose-600 text-xs"
                                          @click="removeChoice(question, cIndex)"
                                        >
                                          ✕
                                        </button>
                                      </div>

                                      <button
                                        class="btn-secondary text-xs"
                                        type="button"
                                        @click="addChoice(question)"
                                      >
                                        + Thêm lựa chọn
                                      </button>
                                    </div>

                                    <!-- TRUE FALSE -->
                                    <div
                                      v-if="question.type === 'true_false'"
                                      class="space-y-1 mt-2"
                                    >
                                      <label class="flex items-center gap-2">
                                        <input
                                          type="radio"
                                          :value="true"
                                          v-model="question.answer_payload.answer"
                                        />
                                        Đúng
                                      </label>

                                      <label class="flex items-center gap-2">
                                        <input
                                          type="radio"
                                          :value="false"
                                          v-model="question.answer_payload.answer"
                                        />
                                        Sai
                                      </label>
                                    </div>

                                    <!-- Tự luận ngắn -->
                                    <div
                                      v-if="question.type === 'short_answer'"
                                      class="space-y-2 mt-2"
                                    >
                                      <span class="label-text">Các đáp án hợp lệ</span>

                                      <div
                                        v-for="(ans, aIndex) in question.answer_payload
                                          .valid_answers"
                                        :key="aIndex"
                                        class="flex items-center gap-2"
                                      >
                                        <input
                                          v-model="ans.answer"
                                          class="input-field flex-1"
                                          placeholder="Đáp án"
                                        />

                                        <label class="flex items-center gap-1 text-xs">
                                          <input type="checkbox" v-model="ans.case_sensitive" />
                                          <span>Phân biệt hoa thường</span>
                                        </label>

                                        <button
                                          class="text-rose-600 text-xs"
                                          @click="removeShortAnswer(question, aIndex)"
                                        >
                                          ✕
                                        </button>
                                      </div>

                                      <button
                                        class="btn-secondary text-xs"
                                        type="button"
                                        @click="addShortAnswer(question)"
                                      >
                                        + Thêm đáp án
                                      </button>
                                    </div>

                                    <!-- Gợi ý -->
                                    <label class="block mt-2">
                                      <span class="label-text">Gợi ý (tuỳ chọn)</span>
                                      <input
                                        v-model="question.hint.text"
                                        class="input-field"
                                        placeholder="Gợi ý cho học sinh..."
                                      />
                                    </label>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      <!-- END NỘI DUNG BÀI -->
                    </div>
                  </div>
                </div>
                <!-- END LESSONS -->
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div
            class="mt-4 flex flex-wrap items-center justify-end gap-3 border-t border-slate-100 pt-4"
          >
            <button
              type="button"
              class="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              @click="goBack"
            >
              Huỷ
            </button>
            <button
              type="submit"
              class="rounded-xl bg-sky-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="submitting"
            >
              {{ submitting ? 'Đang lưu…' : 'Tạo khoá học' }}
            </button>
          </div>
        </section>
      </form>

      <!-- Notification modal -->
      <transition
        enter-active-class="transition-opacity duration-150 ease-out"
        leave-active-class="transition-opacity duration-150 ease-in"
        enter-from-class="opacity-0"
        leave-to-class="opacity-0"
      >
        <div
          v-if="notification.open"
          class="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4"
          role="dialog"
          aria-modal="true"
          @click.self="notification.open = false"
        >
          <div
            class="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl outline-none"
          >
            <div class="mb-4 flex items-center gap-3">
              <div
                :class="[
                  'rounded-full p-2',
                  notification.type === 'success'
                    ? 'bg-green-100 text-green-600'
                    : 'bg-amber-100 text-amber-600',
                ]"
              >
                <span v-if="notification.type === 'success'">✓</span>
                <span v-else>⚠</span>
              </div>
              <h3 class="text-lg font-bold text-slate-800">
                {{ notification.title }}
              </h3>
            </div>

            <div class="mb-6">
              <p class="text-slate-700">{{ notification.message }}</p>
            </div>

            <div class="flex justify-end">
              <button
                type="button"
                class="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700"
                @click="notification.open = false"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      </transition>

      <!-- Notification modal (giống file mẫu) -->
      <transition
        enter-active-class="transition-opacity duration-150 ease-out"
        leave-active-class="transition-opacity duration-150 ease-in"
        enter-from-class="opacity-0"
        leave-to-class="opacity-0"
      >
        <div
          v-if="notificationModal.open"
          class="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4"
          role="dialog"
          aria-modal="true"
          @click.self="notificationModal.open = false"
        >
          <div
            class="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl outline-none"
          >
            <div class="mb-4 flex items-center gap-3">
              <div
                :class="[
                  'p-2 rounded-full',
                  notificationModal.type === 'success'
                    ? 'bg-green-100 text-green-600'
                    : 'bg-amber-100 text-amber-600',
                ]"
              >
                <span v-if="notificationModal.type === 'success'">✓</span>
                <span v-else>⚠</span>
              </div>

              <h3 class="text-lg font-bold text-slate-800">
                {{ notificationModal.title }}
              </h3>
            </div>

            <p class="mb-6 text-slate-700">
              {{ notificationModal.message }}
            </p>

            <div class="flex justify-end">
              <button
                type="button"
                class="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700"
                @click="notificationModal.open = false"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      </transition>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const MAX_IMAGE = 5 * 1024 * 1024 // 5MB
const MAX_VIDEO = 200 * 1024 * 1024 // 200MB
const MAX_DOCX = 5 * 1024 * 1024 // 5MB
const MAX_PDF = 10 * 1024 * 1024 // 10MB

// ================== AUTH HEADER ==================
const getAuthHeaders = () => {
  const token = localStorage.getItem('access')
  return token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {}
}

// ================== TYPES ==================
interface ContentBlock {
  type: string
  position: number
  payload: any
}

interface Lesson {
  title: string
  position: number
  content_type: string
  published?: boolean
  content_blocks: ContentBlock[]
}

interface Module {
  title: string
  position: number
  lessons: Lesson[]
}

// ================== STATE ==================
const submitting = ref(false)

const f = reactive<{
  title: string
  description: string
  grade: string
  subject: string
  tags: string[]
  modules: Module[]
  published: boolean
}>({
  title: '',
  description: '',
  grade: '5',
  subject: '',
  tags: [],
  modules: [],
  published: true,
})

const titleErr = ref('')

// cover
const coverInput = ref<HTMLInputElement | null>(null)
const coverFileName = ref('')
const coverErr = ref('')
const coverBlobUrl = ref<string | null>(null)
const coverImageId = ref<string | null>(null)

// tags input
const tagsInput = ref('')

// notification
const notification = reactive({
  open: false,
  type: 'success' as 'success' | 'error',
  title: '',
  message: '',
})
// Notification modal
const notificationModal = reactive({
  open: false,
  type: 'success' as 'success' | 'error',
  title: '',
  message: '',
})

const showModal = (type: 'success' | 'error', title: string, message: string) => {
  notificationModal.type = type
  notificationModal.title = title
  notificationModal.message = message
  notificationModal.open = true
}

// lưu blob url để revoke
const blobUrls = new Set<string>()

// refs cho input file của content_blocks
const fileInputRefs = ref<Record<string, HTMLInputElement | null>>({})

// ================== HELPERS ==================
const showNotification = (type: 'success' | 'error', title: string, message: string) => {
  notification.type = type
  notification.title = title
  notification.message = message
  notification.open = true
}

const updateTags = () => {
  f.tags = tagsInput.value
    .split(',')
    .map((t) => t.trim())
    .filter((t) => t.length > 0)
}

// upload ảnh/file/video chung
type MediaComponent = 'lesson_material' | 'course_thumbnail'

interface UploadMediaResponse {
  id: string
  original_filename: string
  uploaded_at: string
  status: string
  component: string
  url: string
}

async function uploadMedia(
  file: File,
  component: MediaComponent,
  contentTypeStr: string,
): Promise<UploadMediaResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('component', component)
  formData.append('content_type_str', contentTypeStr)

  const { data } = await axios.post<UploadMediaResponse>('/api/media/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...getAuthHeaders(),
    },
  })

  return data
}

// ================== COVER HANDLER ==================
const MAX_AVATAR_SIZE = 2 * 1024 * 1024
const OVER_LIMIT_MSG = 'File ảnh vượt quá dung lượng cho phép (2MB)'

const onPickCover = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (file.size > MAX_AVATAR_SIZE) {
    coverErr.value = OVER_LIMIT_MSG
    coverFileName.value = ''
    return
  }

  coverErr.value = ''
  coverFileName.value = file.name

  // preview local
  if (coverBlobUrl.value) {
    URL.revokeObjectURL(coverBlobUrl.value)
  }
  const localUrl = URL.createObjectURL(file)
  coverBlobUrl.value = localUrl
  blobUrls.add(localUrl)

  try {
    const res = await uploadMedia(file, 'course_thumbnail', 'image')
    coverImageId.value = res.id
    showModal('success', 'Hoàn tất', 'Upload ảnh bìa thành công!')
  } catch (err) {
    console.error('❌ Lỗi upload ảnh bìa:', err)
    coverImageId.value = null
    showModal('error', 'Lỗi', 'Upload ảnh bìa thất bại. Vui lòng thử lại.')
  }
}

// ================== EDIT MODULES / LESSONS ==================
function addModule() {
  f.modules.push({
    title: '',
    position: f.modules.length,
    lessons: [],
  })
}

function removeModule(mIndex: number) {
  f.modules.splice(mIndex, 1)
  f.modules.forEach((m, idx) => {
    m.position = idx
  })
}

function addLesson(mIndex: number) {
  const mod = f.modules[mIndex]
  mod.lessons.push({
    title: '',
    position: mod.lessons.length,
    content_type: 'lesson',
    published: false,
    content_blocks: [],
  })
}

function removeLesson(mIndex: number, lIndex: number) {
  const mod = f.modules[mIndex]
  mod.lessons.splice(lIndex, 1)
  mod.lessons.forEach((l, idx) => {
    l.position = idx
  })
}

// ================== CONTENT BLOCKS ==================
function makeDefaultPayloadForType(type: string) {
  switch (type) {
    case 'text':
      return { text: '' }
    case 'image':
      return {
        caption: '',
        image_file: null,
        image_preview: null,
        image_id: null,
        file_url: null,
      }
    case 'video':
      return {
        video_file: null,
        video_preview: null,
        video_id: null,
        file_url: null,
        uploading: false,
        progress: 0,
      }
    case 'pdf':
    case 'docx':
      return { file: null, filename: '', file_id: null, file_url: null }
    case 'quiz':
      return {
        title: '',
        time_limit: '',
        questions: [],
      }
    default:
      return {}
  }
}

function addContentBlock(mIndex: number, lIndex: number) {
  const lesson = f.modules[mIndex].lessons[lIndex]
  const position = lesson.content_blocks.length
  const block: ContentBlock = {
    type: 'text',
    position,
    payload: makeDefaultPayloadForType('text'),
  }
  lesson.content_blocks.push(block)
}

function removeContentBlock(mIndex: number, lIndex: number, bIndex: number) {
  const lesson = f.modules[mIndex].lessons[lIndex]
  lesson.content_blocks.splice(bIndex, 1)
  lesson.content_blocks.forEach((b, idx) => {
    b.position = idx
  })
}

function resetBlockPayload(block: ContentBlock) {
  if (block.type === 'quiz') {
    block.payload = {
      title: '',
      time_limit: '',
      questions: [],
    }
  }

  block.payload = makeDefaultPayloadForType(block.type)
}

// ========== File input helpers ==========
function makeFileKey(kind: string, m: number, l: number, b: number) {
  return `${kind}-${m}-${l}-${b}`
}

function setFileInputRef(
  el: HTMLInputElement | null,
  kind: string,
  mIndex: number,
  lIndex: number,
  bIndex: number,
) {
  const key = makeFileKey(kind, mIndex, lIndex, bIndex)
  if (el) {
    fileInputRefs.value[key] = el
  } else {
    delete fileInputRefs.value[key]
  }
}

function triggerFileInput(kind: string, mIndex: number, lIndex: number, bIndex: number) {
  const key = makeFileKey(kind, mIndex, lIndex, bIndex)
  const input = fileInputRefs.value[key]
  if (input) input.click()
}

async function handleFileUpload(
  event: Event,
  kind: 'image' | 'video' | 'file',
  mIndex: number,
  lIndex: number,
  bIndex: number,
) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const block = f.modules[mIndex].lessons[lIndex].content_blocks[bIndex]
  /** -------------------------
   *  GIỚI HẠN DUNG LƯỢNG CHUẨN
   * ------------------------- */
  if (kind === 'image' && file.size > MAX_IMAGE) {
    showModal('error', 'File quá lớn', 'Ảnh phải nhỏ hơn 5MB!')
    input.value = ''
    return
  }

  if (kind === 'video' && file.size > MAX_VIDEO) {
    showModal('error', 'File quá lớn', 'Video phải nhỏ hơn 200MB!')
    input.value = ''
    return
  }

  if (kind === 'file') {
    if (block.type === 'pdf' && file.size > MAX_PDF) {
      showModal('error', 'File quá lớn', 'PDF phải nhỏ hơn 10MB!')
      input.value = ''
      return
    }

    if (block.type === 'docx' && file.size > MAX_DOCX) {
      showModal('error', 'File quá lớn', 'DOCX phải nhỏ hơn 5MB!')
      input.value = ''
      return
    }
  }

  /** -------------------------
   *  GIỚI HẠN DUNG LƯỢNG
   * -------------------------
   */
  if (kind === 'image' && file.size > MAX_IMAGE) {
    showModal('error', 'File quá lớn', 'Ảnh phải nhỏ hơn 5MB!')
    input.value = ''
    return
  }

  if (kind === 'video' && file.size > MAX_VIDEO) {
    showModal('error', 'File quá lớn', 'Video phải nhỏ hơn 200MB!')
    input.value = ''
    return
  }

  // PDF / DOCX
  if (kind === 'file') {
    const blockType = block.type

    if (blockType === 'pdf' && file.size > MAX_PDF) {
      showModal('error', 'File quá lớn', 'PDF phải nhỏ hơn 10MB!')
      input.value = ''
      return
    }

    if (blockType === 'docx' && file.size > MAX_DOCX) {
      showModal('error', 'File quá lớn', 'DOCX phải nhỏ hơn 5MB!')
      input.value = ''
      return
    }
  }

  /** -------------------------
   *  TIẾP TỤC XỬ LÝ FILE
   * -------------------------
   */
  if (kind === 'image') {
    block.payload.image_file = file

    if (block.payload.image_preview) URL.revokeObjectURL(block.payload.image_preview)

    const url = URL.createObjectURL(file)
    block.payload.image_preview = url
    blobUrls.add(url)

    try {
      const res = await uploadMedia(file, 'lesson_material', 'image')
      block.payload.image_id = res.id
      block.payload.file_url = res.url

      showModal('success', 'Thành công', 'Upload hình ảnh thành công!')
    } catch (err) {
      showModal('error', 'Lỗi', 'Upload hình ảnh thất bại, vui lòng thử lại!')
    }
  } else if (kind === 'video') {
    block.payload.video_file = file

    if (block.payload.video_preview) URL.revokeObjectURL(block.payload.video_preview)

    const localUrl = URL.createObjectURL(file)
    block.payload.video_preview = localUrl
    blobUrls.add(localUrl)

    block.payload.uploading = true
    block.payload.progress = 0

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('component', 'lesson_material')
      formData.append('content_type_str', 'video')

      const res = await axios.post('/api/media/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...getAuthHeaders(),
        },
        onUploadProgress: (e) => {
          if (e.total) {
            block.payload.progress = Math.round((e.loaded * 100) / e.total)
          }
        },
      })

      block.payload.video_id = res.data.id
      block.payload.video_preview = res.data.url
      block.payload.progress = 100

      showModal('success', 'Thành công', 'Upload video hoàn tất!')
    } catch (err) {
      showModal('error', 'Lỗi', 'Upload video thất bại!')
    } finally {
      block.payload.uploading = false
    }
  } else if (kind === 'file') {
    block.payload.file = file

    try {
      const res = await uploadMedia(file, 'lesson_material', block.type)
      block.payload.file_id = res.id
      block.payload.file_url = res.url

      showModal('success', 'Thành công', 'Upload file thành công!')
    } catch (err) {
      showModal('error', 'Lỗi', 'Upload file thất bại!')
    }
  }
}

// Chuẩn hoá position cho modules/lessons/blocks trước khi gửi
function normalizePositions() {
  f.modules.forEach((m, mIndex) => {
    m.position = mIndex
    m.lessons.forEach((l, lIndex) => {
      l.position = lIndex
      if (Array.isArray(l.content_blocks)) {
        l.content_blocks.forEach((b, bIndex) => {
          b.position = bIndex
        })
      }
    })
  })
}

// Sanitize content_blocks payload theo format backend
function buildSanitizedModules() {
  return f.modules.map((m) => ({
    title: m.title,
    position: m.position,
    lessons: m.lessons.map((l) => ({
      title: l.title,
      position: l.position,
      content_type: l.content_type,
      published: l.published ?? false,
      content_blocks: l.content_blocks.map((b) => {
        let payload: any = {}

        if (b.type === 'text') {
          payload = { text: b.payload.text || '' }
        } else if (b.type === 'image') {
          payload = {
            image_id: b.payload.image_id,
            caption: b.payload.caption || '',
          }
        } else if (b.type === 'video') {
          payload = {
            video_id: b.payload.video_id,
          }
        } else if (b.type === 'pdf' || b.type === 'docx') {
          payload = {
            file_id: b.payload.file_id,
          }
          if (b.type === 'pdf' && b.payload.filename) {
            payload.filename = b.payload.filename
          }
        } else if (b.type === 'quiz') {
          // giữ nguyên payload quiz (đã đúng format backend)
          payload = b.payload
        } else {
          payload = b.payload || {}
        }

        return {
          type: b.type,
          position: b.position,
          payload,
        }
      }),
    })),
  }))
}

function addChoice(question) {
  if (!question.answer_payload.choices) question.answer_payload.choices = []

  const index = question.answer_payload.choices.length
  const id = String.fromCharCode(97 + index) // a, b, c...

  question.answer_payload.choices.push({
    id,
    text: '',
    is_correct: false,
  })
}

function removeChoice(question, choiceIndex) {
  question.answer_payload.choices.splice(choiceIndex, 1)

  // đánh lại id a,b,c,...
  question.answer_payload.choices.forEach((c, i) => {
    c.id = String.fromCharCode(97 + i)
  })
}

function setCorrectChoice(question, index) {
  question.answer_payload.choices.forEach((c, i) => {
    c.is_correct = i === index
  })
}

function toggleMultiCorrect(choice: { is_correct: boolean }) {
  choice.is_correct = !choice.is_correct
}
function addShortAnswer(question: {
  answer_payload: { valid_answers: { answer: string; case_sensitive: boolean }[] }
}) {
  question.answer_payload.valid_answers.push({
    answer: '',
    case_sensitive: false,
  })
}

function removeShortAnswer(
  question: { answer_payload: { valid_answers: { answer: string; case_sensitive: boolean }[] } },
  index: number,
) {
  question.answer_payload.valid_answers.splice(index, 1)
}

// ================== QUIZ HELPERS ==================

function addQuestion(block: ContentBlock) {
  if (!block.payload.questions) block.payload.questions = []

  block.payload.questions.push({
    type: 'multiple_choice_single',
    prompt: { text: '' },
    answer_payload: { choices: [] },
    hint: { text: '' },
    position: block.payload.questions.length,
  })
}

function removeQuestion(block, qIndex) {
  block.payload.questions.splice(qIndex, 1)
  block.payload.questions.forEach((q, i) => (q.position = i))
}

function resetQuestionPayload(question) {
  switch (question.type) {
    case 'multiple_choice_single':
    case 'multiple_choice_multi':
      question.answer_payload = { choices: [] }
      break

    case 'true_false':
      question.answer_payload = { answer: true }
      break

    case 'short_answer':
      question.answer_payload = {
        valid_answers: [{ answer: '', case_sensitive: false }],
      }
      break

    default:
      question.answer_payload = {}
  }
}

// ================== SUBMIT (CREATE) ==================
async function submit() {
  titleErr.value = ''
  if (!f.title || !f.title.trim()) {
    titleErr.value = 'Vui lòng nhập tên khoá học.'
    return
  }

  // chuẩn hoá position để backend xử lý
  normalizePositions()

  submitting.value = true
  try {
    const payload: any = {
      title: f.title,
      description: f.description,
      grade: f.grade, // backend sample dùng string "5"
      subject: f.subject || null,
      categories: f.subject ? [f.subject] : [],
      tags: f.tags,
      published: f.published,
      modules: buildSanitizedModules(),
    }

    if (coverImageId.value) {
      payload.image_id = coverImageId.value
    }

    await axios.post('/api/content/instructor/courses/', payload, {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    })

    showNotification('success', 'Thành công', 'Đã tạo khoá học mới.')

    // chuyển về /admin/courses sau một nhịp nhỏ
    setTimeout(() => {
      notification.open = false
      router.push('/admin/courses')
    }, 800)
  } catch (e: any) {
    console.error('❌ Lỗi khi tạo khoá học:', e)
    showNotification(
      'error',
      'Lỗi',
      e?.response?.data?.detail ||
        e?.message ||
        'Có lỗi xảy ra khi tạo khoá học. Vui lòng thử lại.',
    )
  } finally {
    submitting.value = false
  }
}

// ================== NAV ==================
function goBack() {
  router.back()
}

function goToList() {
  router.push({ path: '/admin/courses' })
}

// ================== CLEANUP ==================
onBeforeUnmount(() => {
  blobUrls.forEach((u) => URL.revokeObjectURL(u))
  blobUrls.clear()
})
</script>

<style scoped>
h1 {
  word-break: break-word;
}

.module-card {
  @apply mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5;
}

.module-card-empty {
  @apply mb-4 rounded-2xl border border-dashed border-slate-300 bg-white p-4 text-xs text-slate-500;
}

.module-header {
  @apply mb-3 flex items-start justify-between gap-3 border-b border-slate-200 pb-3;
}

.lessons-section {
  @apply mt-2;
}

.lesson-card {
  @apply rounded-xl border border-slate-200 bg-white p-3 sm:p-4;
}

.lesson-card-empty {
  @apply mb-3 rounded-xl border border-dashed border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-500;
}

.lesson-header {
  @apply flex items-start justify-between gap-3;
}

.lesson-content {
  @apply mt-3;
}

.content-block-card {
  @apply mb-3 rounded-lg border border-slate-200 bg-white p-3;
}

.content-block-header {
  @apply mb-2 flex items-center justify-between gap-2;
}

.content-block-body {
  @apply space-y-3;
}

.file-upload-area {
  @apply flex flex-wrap items-center gap-2 text-xs;
}

.file-info {
  @apply text-xs text-slate-700;
}

.image-preview-small {
  @apply mt-2 max-h-40 rounded-md border border-slate-200 object-contain;
}

.video-preview-small {
  @apply mt-2 max-h-56 w-full rounded-md border border-slate-200 bg-black;
}

.hint-text {
  @apply text-[11px] text-slate-500;
}

/* Dùng lại style chung */
.label-text {
  @apply mb-1 block text-sm font-semibold text-gray-700;
}

.input-field {
  @apply w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-800 placeholder-gray-400 outline-none transition focus:border-blue-500 focus:ring-1 focus:ring-blue-500;
}

.btn-secondary {
  @apply rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
}
</style>
