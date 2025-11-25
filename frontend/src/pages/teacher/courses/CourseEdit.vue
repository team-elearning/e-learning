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
            <p class="text-xs uppercase tracking-wide text-slate-400">Sửa khoá học</p>
            <h1 class="text-xl font-semibold sm:text-2xl">
              {{ course?.title || 'Đang tải…' }}
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
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-4">
        <div class="h-40 w-full animate-pulse rounded-2xl bg-slate-200" />
        <div class="h-4 w-1/2 animate-pulse rounded bg-slate-200" />
        <div class="h-4 w-1/3 animate-pulse rounded bg-slate-200" />
        <div class="h-32 w-full animate-pulse rounded-2xl bg-slate-200" />
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
        <!-- Form chỉnh sửa -->
        <form class="grid grid-cols-1 gap-6 lg:grid-cols-[280px,1fr]" @submit.prevent="submit">
          <!-- Thumbnail & info ngắn -->
          <section class="space-y-4">
            <!-- Thumbnail -->
            <div
              class="relative h-48 w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 sm:h-56"
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

              <!-- overlay loading ảnh bìa -->
              <div
                v-if="coverLoading || coverUploading"
                class="absolute inset-0 flex items-center justify-center bg-black/30"
              >
                <div class="rounded-full bg-white/90 px-4 py-1 text-xs font-medium text-slate-700">
                  {{ coverUploading ? 'Đang upload ảnh bìa…' : 'Đang tải ảnh bìa…' }}
                </div>
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

              <div class="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  class="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                  :disabled="coverUploading"
                  @click="coverInput?.click()"
                >
                  Chọn ảnh bìa
                </button>

                <span v-if="coverFileName" class="text-xs text-slate-600">
                  {{ coverFileName }}
                </span>
                <span v-else class="text-xs text-slate-400">
                  Chưa chọn ảnh mới (giữ nguyên ảnh hiện tại).
                </span>
              </div>

              <p class="mt-2 text-[11px] text-slate-400">Hỗ trợ JPG/PNG, tối đa 2MB.</p>

              <p v-if="coverErr" class="mt-2 text-xs font-medium text-rose-600">
                {{ coverErr }}
              </p>
              <p v-if="coverLoadErr" class="mt-1 text-xs font-medium text-amber-600">
                {{ coverLoadErr }}
              </p>
            </div>

            <!-- Thông tin nhanh -->
            <div class="rounded-2xl border border-slate-200 bg-white p-4 text-xs">
              <p class="font-semibold text-slate-700">Tóm tắt</p>
              <p class="mt-1 text-slate-500">
                Lớp:
                <span class="font-medium text-slate-700">
                  {{ f.grade || 'Chưa rõ' }}
                </span>
              </p>
              <p class="mt-1 text-slate-500">
                Môn:
                <span class="font-medium text-slate-700">
                  {{
                    f.subject ||
                    (course.categories[0] && (course.categories[0] as any).name) ||
                    'Chưa rõ'
                  }}
                </span>
              </p>
              <p class="mt-1 text-slate-500">
                Số chương:
                <span class="font-medium text-slate-700">
                  {{ f.modules.length }}
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
                placeholder="Ví dụ: Toán 5 (Hỗ trợ học bộ Cánh diều)"
                @input="titleErr = ''"
              />
              <p v-if="titleErr" class="mt-1 text-xs font-medium text-rose-600">
                {{ titleErr }}
              </p>
            </div>

            <!-- Môn & khối -->
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
                Tags sẽ giúp học sinh tìm kiếm khoá học dễ dàng hơn.
              </p>
            </div>

            <!-- CHƯƠNG / BÀI HỌC + NỘI DUNG -->
            <div class="form-field md:col-span-2">
              <div class="mb-4 flex items-center justify-between">
                <span class="label-text">Chương học (Modules)</span>
                <button type="button" class="btn-secondary" @click="addModule">
                  + Thêm chương
                </button>
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
                  :key="module.id || moduleIndex"
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
                            :placeholder="`Chương ${moduleIndex + 1}: Ôn tập và bổ sung về số tự nhiên`"
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
                        :key="lesson.id || lessonIndex"
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
                                  :placeholder="`Bài ${lessonIndex + 1}: Ôn tập về số tự nhiên`"
                                />
                              </label>
                              <p class="text-[10px] text-slate-500">
                                {{ lesson.content_blocks?.length || 0 }} nội dung (text / hình /
                                video / file / quiz ...)
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
                              :key="block.id || blockIndex"
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
                                <label class="block mb-3">
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
                                      :disabled="block.payload.uploading"
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

                                  <div v-if="block.payload.uploading" class="hint-text">
                                    Đang upload ảnh...
                                  </div>
                                  <p
                                    v-if="block.payload.uploadError"
                                    class="text-xs font-medium text-rose-600"
                                  >
                                    {{ block.payload.uploadError }}
                                  </p>

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
                                      :disabled="block.payload.uploading"
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
                                    <span v-else class="file-info text-gray-500">
                                      Chưa có video nào được chọn
                                    </span>
                                  </div>

                                  <div v-if="block.payload.uploading" class="hint-text">
                                    Đang upload video... {{ block.payload.progress || 0 }}%
                                  </div>
                                  <p
                                    v-if="block.payload.uploadError"
                                    class="text-xs font-medium text-rose-600"
                                  >
                                    {{ block.payload.uploadError }}
                                  </p>

                                  <video
                                    v-if="block.payload.video_preview"
                                    :src="block.payload.video_preview"
                                    controls
                                    class="video-preview-small"
                                  ></video>
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
                                      :disabled="block.payload.uploading"
                                      @click="
                                        triggerFileInput(
                                          'file',
                                          moduleIndex,
                                          lessonIndex,
                                          blockIndex,
                                        )
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

                                  <div v-if="block.payload.uploading" class="hint-text">
                                    Đang upload file...
                                  </div>
                                  <p
                                    v-if="block.payload.uploadError"
                                    class="text-xs font-medium text-rose-600"
                                  >
                                    {{ block.payload.uploadError }}
                                  </p>

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

                                <!-- QUIZ -->
                                <div v-else-if="block.type === 'quiz'" class="space-y-3">
                                  <!-- Quiz meta -->
                                  <div class="grid gap-3 sm:grid-cols-[2fr,1fr]">
                                    <label class="block">
                                      <span class="label-text">Tiêu đề bài kiểm tra</span>
                                      <input
                                        v-model="block.payload.title"
                                        class="input-field"
                                        placeholder="Ví dụ: Bài tập tổng hợp Chương 2"
                                      />
                                    </label>
                                    <label class="block">
                                      <span class="label-text">Thời gian làm bài</span>
                                      <input
                                        v-model="block.payload.time_limit"
                                        class="input-field"
                                        placeholder="Ví dụ: 00:45:00"
                                      />
                                    </label>
                                  </div>

                                  <!-- Questions -->
                                  <div class="mt-3">
                                    <div class="mb-2 flex items-center justify-between">
                                      <span class="label-text">
                                        Câu hỏi ({{ block.payload.questions?.length || 0 }})
                                      </span>
                                      <button
                                        type="button"
                                        class="btn-secondary text-xs"
                                        @click="addQuestion(block)"
                                      >
                                        + Thêm câu hỏi
                                      </button>
                                    </div>

                                    <div
                                      v-if="
                                        !block.payload.questions ||
                                        block.payload.questions.length === 0
                                      "
                                      class="lesson-card-empty"
                                    >
                                      Chưa có câu hỏi nào. Nhấn
                                      <span class="font-semibold text-slate-700"
                                        >“Thêm câu hỏi”</span
                                      >
                                      để tạo bài kiểm tra.
                                    </div>

                                    <div v-else class="space-y-3">
                                      <div
                                        v-for="(question, qIndex) in block.payload.questions"
                                        :key="qIndex"
                                        class="rounded-lg border border-slate-200 bg-slate-50 p-3"
                                      >
                                        <div
                                          class="mb-2 flex flex-wrap items-center justify-between gap-2"
                                        >
                                          <div class="flex items-center gap-2">
                                            <span
                                              class="inline-flex h-6 min-w-[1.6rem] items-center justify-center rounded-full bg-sky-100 text-[11px] font-semibold text-sky-700"
                                            >
                                              C{{ qIndex + 1 }}
                                            </span>
                                            <select
                                              v-model="question.type"
                                              class="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 outline-none"
                                              @change="resetQuestionPayload(question)"
                                            >
                                              <option value="multiple_choice_single">
                                                Trắc nghiệm 1 đáp án
                                              </option>
                                              <option value="multiple_choice_multi">
                                                Trắc nghiệm nhiều đáp án
                                              </option>
                                              <option value="true_false">Đúng / Sai</option>
                                              <!-- <option value="fill_in_the_blank">
                                                Điền vào chỗ trống
                                              </option> -->
                                              <option value="short_answer">Trả lời ngắn</option>
                                              <!-- <option value="matching">Nối cặp</option> -->
                                              <!-- <option value="essay">Tự luận</option> -->
                                            </select>
                                          </div>

                                          <button
                                            type="button"
                                            class="text-[11px] font-medium text-rose-600 hover:text-rose-700 hover:underline"
                                            @click="removeQuestion(block, qIndex)"
                                          >
                                            Xoá câu hỏi
                                          </button>
                                        </div>

                                        <!-- Prompt -->
                                        <label class="mb-2 block">
                                          <span class="label-text text-xs">Nội dung câu hỏi</span>
                                          <textarea
                                            v-model="question.prompt.text"
                                            rows="2"
                                            class="input-field resize-y text-xs"
                                            placeholder="Nhập nội dung câu hỏi..."
                                          ></textarea>
                                        </label>

                                        <!-- MULTIPLE CHOICE (SINGLE / MULTI) -->
                                        <div
                                          v-if="
                                            question.type === 'multiple_choice_single' ||
                                            question.type === 'multiple_choice_multi'
                                          "
                                          class="space-y-2"
                                        >
                                          <div class="flex items-center justify-between">
                                            <span class="label-text text-xs">Các lựa chọn</span>
                                            <button
                                              type="button"
                                              class="btn-secondary text-[11px]"
                                              @click="addChoice(question)"
                                            >
                                              + Thêm lựa chọn
                                            </button>
                                          </div>

                                          <div
                                            v-for="(choice, cIndex) in question.answer_payload
                                              .choices"
                                            :key="cIndex"
                                            class="flex items-center gap-2"
                                          >
                                            <span
                                              class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-slate-200 text-[11px] font-semibold text-slate-700"
                                            >
                                              {{ choice.id }}
                                            </span>

                                            <input
                                              v-model="choice.text"
                                              class="input-field text-xs"
                                              placeholder="Nội dung lựa chọn"
                                            />

                                            <!-- single / multi correct -->
                                            <label
                                              class="flex items-center gap-1 text-[11px] text-slate-600"
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
                                              type="button"
                                              class="text-[11px] text-rose-600 hover:text-rose-700"
                                              @click="removeChoice(question, cIndex)"
                                            >
                                              ✕
                                            </button>
                                          </div>
                                        </div>

                                        <!-- TRUE / FALSE -->
                                        <div v-else-if="question.type === 'true_false'">
                                          <label class="label-text text-xs">Đáp án đúng</label>
                                          <div class="mt-1 flex gap-4 text-xs text-slate-700">
                                            <label class="flex items-center gap-1">
                                              <input
                                                type="radio"
                                                :checked="question.answer_payload.answer === true"
                                                @change="question.answer_payload.answer = true"
                                              />
                                              <span>Đúng</span>
                                            </label>
                                            <label class="flex items-center gap-1">
                                              <input
                                                type="radio"
                                                :checked="question.answer_payload.answer === false"
                                                @change="question.answer_payload.answer = false"
                                              />
                                              <span>Sai</span>
                                            </label>
                                          </div>
                                        </div>

                                        <!-- FILL IN THE BLANK -->
                                        <div v-else-if="question.type === 'fill_in_the_blank'">
                                          <div
                                            class="mb-1 flex items-center justify-between text-xs"
                                          >
                                            <span class="label-text text-xs"
                                              >Các chỗ trống &amp; đáp án</span
                                            >
                                            <button
                                              type="button"
                                              class="btn-secondary text-[11px]"
                                              @click="addBlank(question)"
                                            >
                                              + Thêm chỗ trống
                                            </button>
                                          </div>

                                          <div
                                            v-for="(blank, bIndex) in question.answer_payload
                                              .blanks"
                                            :key="bIndex"
                                            class="mb-1 flex items-center gap-2"
                                          >
                                            <span
                                              class="inline-flex min-w-[3.5rem] items-center justify-center rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-700"
                                            >
                                              {{ blank.id || `BLANK_${bIndex + 1}` }}
                                            </span>
                                            <input
                                              v-model="blank.answer"
                                              class="input-field text-xs"
                                              placeholder="Đáp án cho chỗ trống này"
                                            />
                                            <button
                                              type="button"
                                              class="text-[11px] text-rose-600 hover:text-rose-700"
                                              @click="removeBlank(question, bIndex)"
                                            >
                                              ✕
                                            </button>
                                          </div>
                                          <p class="hint-text">
                                            Gợi ý: dùng ký hiệu [BLANK_1], [BLANK_2]... trong câu
                                            hỏi để đánh dấu chỗ trống.
                                          </p>
                                        </div>

                                        <!-- SHORT ANSWER -->
                                        <div v-else-if="question.type === 'short_answer'">
                                          <div
                                            class="mb-1 flex items-center justify-between text-xs"
                                          >
                                            <span class="label-text text-xs"
                                              >Các đáp án được chấp nhận</span
                                            >
                                            <button
                                              type="button"
                                              class="btn-secondary text-[11px]"
                                              @click="addShortAnswer(question)"
                                            >
                                              + Thêm đáp án
                                            </button>
                                          </div>

                                          <div
                                            v-for="(ans, aIndex) in question.answer_payload
                                              .valid_answers"
                                            :key="aIndex"
                                            class="mb-1 flex items-center gap-2"
                                          >
                                            <input
                                              v-model="ans.answer"
                                              class="input-field text-xs"
                                              placeholder="Đáp án hợp lệ"
                                            />
                                            <label
                                              class="flex items-center gap-1 text-[11px] text-slate-600"
                                            >
                                              <input type="checkbox" v-model="ans.case_sensitive" />
                                              <span>Phân biệt HOA/thường</span>
                                            </label>
                                            <button
                                              type="button"
                                              class="text-[11px] text-rose-600 hover:text-rose-700"
                                              @click="removeShortAnswer(question, aIndex)"
                                            >
                                              ✕
                                            </button>
                                          </div>
                                        </div>

                                        <!-- MATCHING -->
                                        <div v-else-if="question.type === 'matching'">
                                          <div class="grid gap-3 sm:grid-cols-2">
                                            <div>
                                              <div
                                                class="mb-1 flex items-center justify-between text-xs"
                                              >
                                                <span class="label-text text-xs">Cột A</span>
                                                <button
                                                  type="button"
                                                  class="btn-secondary text-[11px]"
                                                  @click="addMatchItem(question, 'column_a')"
                                                >
                                                  + Thêm
                                                </button>
                                              </div>
                                              <div
                                                v-for="(aItem, aIdx) in question.answer_payload
                                                  .column_a"
                                                :key="'a-' + aIdx"
                                                class="mb-1 flex items-center gap-2"
                                              >
                                                <span
                                                  class="inline-flex min-w-[2.2rem] items-center justify-center rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-700"
                                                >
                                                  {{ aItem.id }}
                                                </span>
                                                <input
                                                  v-model="aItem.text"
                                                  class="input-field text-xs"
                                                  placeholder="Nội dung A"
                                                />
                                                <button
                                                  type="button"
                                                  class="text-[11px] text-rose-600 hover:text-rose-700"
                                                  @click="
                                                    removeMatchItem(question, 'column_a', aIdx)
                                                  "
                                                >
                                                  ✕
                                                </button>
                                              </div>
                                            </div>

                                            <div>
                                              <div
                                                class="mb-1 flex items-center justify-between text-xs"
                                              >
                                                <span class="label-text text-xs">Cột B</span>
                                                <button
                                                  type="button"
                                                  class="btn-secondary text-[11px]"
                                                  @click="addMatchItem(question, 'column_b')"
                                                >
                                                  + Thêm
                                                </button>
                                              </div>
                                              <div
                                                v-for="(bItem, bIdx) in question.answer_payload
                                                  .column_b"
                                                :key="'b-' + bIdx"
                                                class="mb-1 flex items-center gap-2"
                                              >
                                                <span
                                                  class="inline-flex min-w-[2.2rem] items-center justify-center rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-700"
                                                >
                                                  {{ bItem.id }}
                                                </span>
                                                <input
                                                  v-model="bItem.text"
                                                  class="input-field text-xs"
                                                  placeholder="Nội dung B"
                                                />
                                                <button
                                                  type="button"
                                                  class="text-[11px] text-rose-600 hover:text-rose-700"
                                                  @click="
                                                    removeMatchItem(question, 'column_b', bIdx)
                                                  "
                                                >
                                                  ✕
                                                </button>
                                              </div>
                                            </div>
                                          </div>

                                          <div class="mt-2">
                                            <div
                                              class="mb-1 flex items-center justify-between text-xs"
                                            >
                                              <span class="label-text text-xs">
                                                Cặp ghép đúng
                                              </span>
                                              <button
                                                type="button"
                                                class="btn-secondary text-[11px]"
                                                @click="addMatchRow(question)"
                                              >
                                                + Thêm cặp
                                              </button>
                                            </div>

                                            <div
                                              v-for="(pair, pIdx) in question.answer_payload
                                                .correct_matches"
                                              :key="pIdx"
                                              class="mb-1 flex flex-wrap items-center gap-2 text-xs"
                                            >
                                              <span class="text-slate-600">A:</span>
                                              <select
                                                v-model="pair.a_id"
                                                class="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 outline-none"
                                              >
                                                <option value="">--</option>
                                                <option
                                                  v-for="aItem in question.answer_payload.column_a"
                                                  :key="aItem.id"
                                                  :value="aItem.id"
                                                >
                                                  {{ aItem.id }}
                                                </option>
                                              </select>

                                              <span class="text-slate-600">B:</span>
                                              <select
                                                v-model="pair.b_id"
                                                class="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 outline-none"
                                              >
                                                <option value="">--</option>
                                                <option
                                                  v-for="bItem in question.answer_payload.column_b"
                                                  :key="bItem.id"
                                                  :value="bItem.id"
                                                >
                                                  {{ bItem.id }}
                                                </option>
                                              </select>

                                              <button
                                                type="button"
                                                class="text-[11px] text-rose-600 hover:text-rose-700"
                                                @click="removeMatchRow(question, pIdx)"
                                              >
                                                ✕
                                              </button>
                                            </div>
                                          </div>
                                        </div>

                                        <!-- ESSAY -->
                                        <div v-else-if="question.type === 'essay'">
                                          <label class="block">
                                            <span class="label-text text-xs">
                                              Gợi ý / tiêu chí chấm điểm
                                            </span>
                                            <textarea
                                              v-model="question.answer_payload.grading_instructions"
                                              rows="2"
                                              class="input-field resize-y text-xs"
                                              placeholder="Hướng dẫn chấm, các ý chính cần có..."
                                            ></textarea>
                                          </label>
                                        </div>

                                        <!-- Hint -->
                                        <label class="mt-2 block">
                                          <span class="label-text text-xs">Gợi ý (tuỳ chọn)</span>
                                          <input
                                            v-model="question.hint.text"
                                            class="input-field text-xs"
                                            placeholder="Gợi ý dành cho học sinh (nếu có)"
                                          />
                                        </label>
                                      </div>
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
                {{ submitting ? 'Đang lưu…' : 'Lưu thay đổi' }}
              </button>
            </div>
          </section>
        </form>
      </div>

      <!-- Không có course mà cũng không loading & không lỗi -->
      <div v-else class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
        Không tìm thấy dữ liệu khoá học.
      </div>

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
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

// ================== AUTH HEADER ==================
const getAuthHeaders = () => {
  const token = localStorage.getItem('access')
  return token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {}
}

// form gốc để so sánh thay đổi
const originalForm = ref<{
  title: string
  description: string
  grade: string
  subject: string
  tags: string[]
  modules: Module[]
} | null>(null)

// ================== TYPES ==================
interface ContentBlock {
  id?: string
  type: string
  position: number
  payload: any
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
  categories: any[]
  tags: any[]
  modules: Module[]
}

// ================== STATE ==================
const course = ref<CourseDetail | null>(null)
const loading = ref(false)
const error = ref('')

const submitting = ref(false)

// form state
const f = reactive<{
  title: string
  description: string
  grade: string
  subject: string
  tags: string[]
  modules: Module[]
}>({
  title: '',
  description: '',
  grade: '5',
  subject: '',
  tags: [],
  modules: [],
})

const titleErr = ref('')

// cover
const coverInput = ref<HTMLInputElement | null>(null)
const coverFileName = ref('')
const coverErr = ref('')
const coverBlobUrl = ref<string | null>(null)
const coverImageId = ref<string | null>(null)
const coverLoading = ref(false)
const coverLoadErr = ref('')
const coverUploading = ref(false)

// tags input
const tagsInput = ref('')

// notification
const notification = reactive({
  open: false,
  type: 'success' as 'success' | 'error',
  title: '',
  message: '',
})

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

async function fetchBlobUrl(path: string): Promise<string | null> {
  try {
    const res = await axios.get(path, {
      responseType: 'blob',
      headers: {
        ...getAuthHeaders(),
      },
    })
    const url = URL.createObjectURL(res.data)
    blobUrls.add(url)
    return url
  } catch (e) {
    console.error('❌ Lỗi tải file blob:', path, e)
    return null
  }
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
      headers: {
        ...getAuthHeaders(),
      },
    })

    course.value = data

    // map data -> form
    f.title = data.title || ''
    f.description = data.description || ''
    f.grade = data.grade || '5'

    const firstCategoryName =
      Array.isArray(data.categories) && data.categories.length
        ? data.categories[0].name || data.categories[0]
        : ''

    f.subject = data.subject || firstCategoryName || ''
    f.tags = (data.tags || []).map((t: any) => (typeof t === 'string' ? t : t.name || ''))

    tagsInput.value = f.tags.join(', ')

    // clone sâu modules → lessons → blocks
    f.modules = (data.modules || []).map((m, mIndex) => ({
      id: m.id,
      title: m.title,
      position: (m as any).position ?? mIndex,
      lessons: (m.lessons || []).map((l, lIndex) => {
        const lesson = {
          id: l.id,
          title: l.title,
          position: (l as any).position ?? lIndex,
          content_type: (l as any).content_type || 'lesson',
          published: (l as any).published,
          content_blocks: (l as any).content_blocks
            ? (JSON.parse(JSON.stringify((l as any).content_blocks)) as ContentBlock[])
            : [],
        }

        // 🟦 FIX: Load preview cho media trong content_blocks
        for (const block of lesson.content_blocks) {
          // IMAGE
          if (block.type === 'image' && block.payload?.image_url) {
            fetchBlobUrl(block.payload.image_url).then((url) => {
              if (url) block.payload.image_preview = url
            })
          }

          // VIDEO
          if (block.type === 'video' && block.payload?.video_url) {
            fetchBlobUrl(block.payload.video_url).then((url) => {
              if (url) block.payload.video_preview = url
            })
          }

          // PDF / DOCX
          if ((block.type === 'pdf' || block.type === 'docx') && block.payload?.file_url) {
            fetchBlobUrl(block.payload.file_url).then((url) => {
              if (url) block.payload.file_preview = url // nếu muốn xem trước
            })
          }
        }

        return lesson
      }),
    }))
    originalForm.value = {
      title: f.title,
      description: f.description,
      grade: f.grade,
      subject: f.subject,
      tags: [...f.tags],
      // clone sâu modules để tránh tham chiếu chung
      modules: JSON.parse(JSON.stringify(f.modules)),
    }

    // cover blob
    if (data.image_url) {
      coverLoading.value = true
      coverLoadErr.value = ''
      const url = await fetchBlobUrl(data.image_url)
      if (url) {
        coverBlobUrl.value = url
      } else {
        coverLoadErr.value = 'Không tải được ảnh bìa.'
      }
      coverLoading.value = false
    }
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
    coverUploading.value = true
    const res = await uploadMedia(file, 'course_thumbnail', 'image')
    coverImageId.value = res.id
  } catch (err) {
    console.error('❌ Lỗi upload ảnh bìa:', err)
    coverImageId.value = null
    showNotification('error', 'Lỗi', 'Upload ảnh bìa thất bại. Vui lòng thử lại.')
  } finally {
    coverUploading.value = false
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
        image_url: null,
        uploading: false,
        uploadError: '',
      }
    case 'video':
      return {
        video_file: null,
        video_preview: null,
        video_id: null,
        video_url: null,
        uploading: false,
        progress: 0,
        uploadError: '',
      }
    case 'pdf':
    case 'docx':
      return {
        file: null,
        filename: '',
        file_id: null,
        file_url: null,
        uploading: false,
        uploadError: '',
      }
    case 'quiz':
      return {
        title: '',
        time_limit: '',
        time_open: null,
        time_close: null,
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
  block.payload.uploadError = ''

  if (kind === 'image') {
    block.payload.image_file = file
    if (block.payload.image_preview) {
      URL.revokeObjectURL(block.payload.image_preview)
    }
    const url = URL.createObjectURL(file)
    block.payload.image_preview = url
    blobUrls.add(url)

    try {
      block.payload.uploading = true
      const res = await uploadMedia(file, 'lesson_material', 'image')
      block.payload.image_id = res.id
      block.payload.image_url = res.url
    } catch (e) {
      console.error('❌ Lỗi upload image block:', e)
      block.payload.uploadError = 'Upload ảnh thất bại. Vui lòng thử lại.'
    } finally {
      block.payload.uploading = false
    }
  } else if (kind === 'video') {
    block.payload.video_file = file
    if (block.payload.video_preview) {
      URL.revokeObjectURL(block.payload.video_preview)
    }
    const url = URL.createObjectURL(file)
    block.payload.video_preview = url
    blobUrls.add(url)

    block.payload.uploading = true
    block.payload.progress = 0
    try {
      const res = await uploadMedia(file, 'lesson_material', 'video')
      block.payload.video_id = res.id
      block.payload.video_url = res.url
      block.payload.progress = 100
    } catch (e) {
      console.error('❌ Lỗi upload video block:', e)
      block.payload.uploadError = 'Upload video thất bại. Vui lòng thử lại.'
    } finally {
      block.payload.uploading = false
    }
  } else if (kind === 'file') {
    block.payload.file = file
    try {
      block.payload.uploading = true
      const res = await uploadMedia(file, 'lesson_material', 'file')
      block.payload.file_id = res.id
      block.payload.file_url = res.url
    } catch (e) {
      console.error('❌ Lỗi upload file block:', e)
      block.payload.uploadError = 'Upload file thất bại. Vui lòng thử lại.'
    } finally {
      block.payload.uploading = false
    }
  }
}

// ================== QUIZ HELPERS ==================
function ensureQuizPayload(block: any) {
  if (!block.payload) block.payload = {}
  if (!block.payload.questions) block.payload.questions = []
  if (!block.payload.title) block.payload.title = ''
  if (!block.payload.time_limit) block.payload.time_limit = ''
}

function addQuestion(block: any) {
  ensureQuizPayload(block)
  if (!block.payload.questions) block.payload.questions = []
  block.payload.questions.push({
    position: block.payload.questions.length,
    type: 'multiple_choice_single',
    prompt: { text: '' },
    answer_payload: {
      choices: [
        { id: 'A', text: '', is_correct: false },
        { id: 'B', text: '', is_correct: false },
      ],
    },
    hint: { text: '' },
  })
}

function removeQuestion(block: any, qIndex: number) {
  if (!block.payload?.questions) return
  block.payload.questions.splice(qIndex, 1)
  block.payload.questions.forEach((q: any, idx: number) => {
    q.position = idx
  })
}

function resetQuestionPayload(question: any) {
  switch (question.type) {
    case 'multiple_choice_single':
    case 'multiple_choice_multi':
      question.answer_payload = {
        choices: [
          { id: 'A', text: '', is_correct: false },
          { id: 'B', text: '', is_correct: false },
        ],
      }
      break
    case 'true_false':
      question.answer_payload = { answer: true }
      break
    case 'fill_in_the_blank':
      question.answer_payload = { blanks: [] }
      break
    case 'short_answer':
      question.answer_payload = { valid_answers: [] }
      break
    case 'matching':
      question.answer_payload = {
        column_a: [],
        column_b: [],
        correct_matches: [],
      }
      break
    case 'essay':
      question.answer_payload = { grading_instructions: '' }
      break
    default:
      question.answer_payload = {}
  }
}

function renumberChoices(question: any) {
  if (!question.answer_payload?.choices) return
  question.answer_payload.choices.forEach((c: any, idx: number) => {
    c.id = String.fromCharCode(65 + idx)
  })
}

function setCorrectChoice(question: any, choiceIndex: number) {
  question.answer_payload.choices.forEach((c: any, idx: number) => {
    c.is_correct = idx === choiceIndex
  })
}

function toggleMultiCorrect(choice: any) {
  choice.is_correct = !choice.is_correct
}

function addChoice(question: any) {
  if (!question.answer_payload.choices) question.answer_payload.choices = []
  const idx = question.answer_payload.choices.length
  question.answer_payload.choices.push({
    id: String.fromCharCode(65 + idx),
    text: '',
    is_correct: false,
  })
}

function removeChoice(question: any, idx: number) {
  question.answer_payload.choices.splice(idx, 1)
  renumberChoices(question)
}

function addBlank(question: any) {
  if (!question.answer_payload.blanks) question.answer_payload.blanks = []
  const id = `BLANK_${question.answer_payload.blanks.length + 1}`
  question.answer_payload.blanks.push({ id, answer: '' })
}

function removeBlank(question: any, idx: number) {
  question.answer_payload.blanks.splice(idx, 1)
}

function addShortAnswer(question: any) {
  if (!question.answer_payload.valid_answers) question.answer_payload.valid_answers = []
  question.answer_payload.valid_answers.push({ answer: '', case_sensitive: false })
}

function removeShortAnswer(question: any, idx: number) {
  question.answer_payload.valid_answers.splice(idx, 1)
}

function addMatchItem(question: any, column: 'column_a' | 'column_b') {
  if (!question.answer_payload[column]) question.answer_payload[column] = []
  const prefix = column === 'column_a' ? 'a' : 'b'
  const id = `${prefix}${question.answer_payload[column].length + 1}`
  question.answer_payload[column].push({ id, text: '' })
}

function removeMatchItem(question: any, column: 'column_a' | 'column_b', idx: number) {
  question.answer_payload[column].splice(idx, 1)
}

function addMatchRow(question: any) {
  if (!question.answer_payload.correct_matches) question.answer_payload.correct_matches = []
  question.answer_payload.correct_matches.push({ a_id: '', b_id: '' })
}

function removeMatchRow(question: any, idx: number) {
  question.answer_payload.correct_matches.splice(idx, 1)
}

// Chuẩn hoá position cho modules/lessons/blocks/questions trước khi gửi
function normalizePositions() {
  f.modules.forEach((m, mIndex) => {
    m.position = mIndex
    m.lessons.forEach((l, lIndex) => {
      l.position = lIndex
      if (Array.isArray(l.content_blocks)) {
        l.content_blocks.forEach((b, bIndex) => {
          b.position = bIndex
          if (b.type === 'quiz' && b.payload?.questions) {
            b.payload.questions.forEach((q: any, qIndex: number) => {
              q.position = qIndex
            })
          }
        })
      }
    })
  })
}
function cleanModules(modules: Module[]): Module[] {
  return modules.map((m) => ({
    id: m.id,
    title: m.title,
    position: m.position,
    lessons: m.lessons.map((l) => ({
      id: l.id,
      title: l.title,
      position: l.position,
      content_type: l.content_type,
      published: l.published,
      content_blocks: l.content_blocks.map((b: any) => {
        const payload = { ...(b.payload || {}) }

        // xoá các field dùng cho UI, không cần gửi lên backend
        delete payload.image_preview
        delete payload.video_preview
        delete payload.file_preview
        delete payload.uploading
        delete payload.uploadError
        delete payload.image_file
        delete payload.video_file
        delete payload.file
        delete payload.progress

        return {
          id: b.id,
          type: b.type,
          position: b.position,
          payload,
        }
      }),
    })),
  }))
}

function shallowEqualJSON(a: any, b: any): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

// ================== SUBMIT (PATCH FULL STRUCTURE) ==================
async function submit() {
  titleErr.value = ''
  if (!f.title || !f.title.trim()) {
    titleErr.value = 'Vui lòng nhập tên khoá học.'
    return
  }

  if (!course.value) return

  // chuẩn hóa position trước khi so sánh / gửi
  normalizePositions()

  const payload: any = {}
  const base = originalForm.value

  // Nếu không có snapshot (trường hợp hiếm), fallback gửi full như cũ
  if (!base) {
    const fullModules = cleanModules(f.modules)
    payload.title = f.title
    payload.description = f.description
    payload.grade = f.grade ? String(f.grade) : null
    payload.subject = f.subject || null
    payload.categories = f.subject ? [f.subject] : []
    payload.tags = f.tags
    payload.modules = fullModules

    if (coverImageId.value) {
      payload.image_id = coverImageId.value
    }
  } else {
    // ===== So sánh từng field =====
    if (f.title !== base.title) {
      payload.title = f.title
    }

    if (f.description !== base.description) {
      payload.description = f.description
    }

    if (String(f.grade) !== String(base.grade)) {
      payload.grade = String(f.grade)
    }

    if ((f.subject || '') !== (base.subject || '')) {
      payload.subject = f.subject || null
      payload.categories = f.subject ? [f.subject] : []
    }

    if (!shallowEqualJSON(f.tags, base.tags)) {
      payload.tags = f.tags
    }

    // modules: chỉ gửi nếu khác
    const currentModulesClean = cleanModules(f.modules)
    const originalModulesClean = cleanModules(base.modules)

    if (!shallowEqualJSON(currentModulesClean, originalModulesClean)) {
      payload.modules = currentModulesClean
    }

    // cover: nếu có image_id mới thì gửi (coi như đã đổi ảnh)
    if (coverImageId.value) {
      payload.image_id = coverImageId.value
    }
  }

  // Nếu không có field nào thay đổi thì thôi, không gọi API
  if (Object.keys(payload).length === 0) {
    showNotification('success', 'Không có thay đổi', 'Không có cập nhật nào để lưu.')
    return
  }

  submitting.value = true
  try {
    await axios.patch(`/api/content/instructor/courses/${course.value.id}/`, payload, {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    })

    showNotification('success', 'Thành công', 'Đã lưu thay đổi khoá học.')

    // Cập nhật lại snapshot gốc theo trạng thái mới
    const newModulesForSnapshot = payload.modules ?? cleanModules(f.modules) // nếu không gửi modules thì dùng modules hiện tại

    originalForm.value = {
      title: payload.title ?? f.title,
      description: payload.description ?? f.description,
      grade: payload.grade ?? f.grade,
      subject: payload.subject ?? f.subject,
      tags: payload.tags ?? [...f.tags],
      modules: JSON.parse(JSON.stringify(newModulesForSnapshot)),
    }

    // Cập nhật course local (chỉ những phần có trong payload hoặc lấy từ f)
    course.value = {
      ...course.value,
      title: payload.title ?? course.value.title,
      description: payload.description ?? course.value.description,
      grade: payload.grade ?? course.value.grade,
      subject: payload.subject ?? course.value.subject,
      categories: payload.categories ?? course.value.categories,
      tags: payload.tags ?? course.value.tags,
      modules: newModulesForSnapshot,
    }

    setTimeout(() => {
      notification.open = false
      router.push('/teacher/courses')
    }, 800)
  } catch (e: any) {
    console.error('❌ Lỗi khi cập nhật khoá học:', e)
    showNotification(
      'error',
      'Lỗi',
      e?.response?.data?.detail ||
        e?.message ||
        'Có lỗi xảy ra khi lưu khoá học. Vui lòng thử lại.',
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
  router.push({ path: '/teacher/courses' })
}

// ================== INIT & CLEANUP ==================
onMounted(() => {
  fetchCourse()
})

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
