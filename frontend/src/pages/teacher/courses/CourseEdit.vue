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
                            @blur="updateModuleTitle(module)"
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
                                  @blur="updateLessonTitle(lesson)"
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
                            <div class="mb-3 flex items-center gap-2 justify-between">
                              <span class="label-text">Nội dung bài học</span>

                              <div class="flex items-center gap-2">
                                <select
                                  v-model="lesson.newBlockType"
                                  class="input-field w-40 text-sm"
                                >
                                  <option value="rich_text">Văn bản</option>
                                  <!-- <option value="image">Hình ảnh</option> -->
                                  <option value="video">Video</option>
                                  <option value="pdf">PDF</option>
                                  <option value="docx">DOCX</option>
                                  <option value="file">File</option>
                                  <option value="quiz">Bài kiểm tra</option>
                                </select>

                                <button
                                  type="button"
                                  class="btn-secondary text-sm"
                                  @click="addContentBlock(moduleIndex, lessonIndex)"
                                >
                                  + Thêm nội dung
                                </button>
                              </div>
                            </div>
                            <div
                              v-for="(block, blockIndex) in lesson.content_blocks"
                              :key="block.id || blockIndex"
                              class="content-block-card"
                              @mouseenter="hydrateBlock(block)"
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
                                <!-- TEXT -->
                                <div v-if="block.type === 'rich_text'" class="space-y-3">
                                  <label class="block">
                                    <span class="label-text">Nội dung văn bản</span>
                                    <textarea
                                      v-model="block.payload.html_content"
                                      class="input-field"
                                      rows="4"
                                      placeholder="Nhập nội dung..."
                                      @blur="saveBlock(block)"
                                    />
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
                                      @blur="saveBlock(block)"
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
                                      {{
                                        block.payload.uploading ? 'Đang upload...' : 'Chọn video'
                                      }}
                                    </button>

                                    <span v-if="block.payload.video_file" class="file-info">
                                      {{ block.payload.video_file.name }} —
                                      {{ (block.payload.video_file.size / 1024 / 1024).toFixed(1) }}
                                      MB
                                    </span>
                                    <span v-else class="file-info text-gray-500">
                                      Chưa chọn video nào
                                    </span>
                                  </div>

                                  <div v-if="block.payload.uploading" class="hint-text">
                                    Đang upload video...
                                  </div>
                                  <p
                                    v-if="block.payload.uploadError"
                                    class="text-xs font-medium text-rose-600"
                                  >
                                    {{ block.payload.uploadError }}
                                  </p>

                                  <video
                                    v-if="block.payload.video_url"
                                    :src="block.payload.video_url"
                                    controls
                                    class="video-preview-small"
                                  />
                                  <p v-else class="text-xs text-gray-500">
                                    <span
                                      v-if="!block.payload.uploading && !block.payload.video_url"
                                    >
                                      🎥 Chưa có video nào được tải lên. Chọn file để bắt đầu.
                                    </span>
                                    <span v-else-if="block.payload.uploading">
                                      Video đang được xử lý hoặc tải lên...
                                    </span>
                                  </p>
                                </div>

                                <!-- PDF / DOCX -->
                                <!-- PDF / DOCX -->
                                <div
                                  v-else-if="['pdf', 'docx'].includes(block.type)"
                                  class="space-y-3"
                                >
                                  <!-- Upload area -->
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
                                      :accept="block.type === 'pdf' ? '.pdf' : '.doc,.docx'"
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
                                      {{
                                        block.payload.uploading
                                          ? 'Đang upload...'
                                          : 'Chọn file ' + block.type.toUpperCase()
                                      }}
                                    </button>

                                    <span v-if="block.payload.file" class="file-info">
                                      {{ block.payload.file.name }} —
                                      {{ Math.round(block.payload.file.size / 1024) }} KB
                                    </span>
                                    <span v-else class="file-info text-gray-500"
                                      >Chưa chọn file nào</span
                                    >
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

                                  <!-- Nếu có file -->
                                  <template v-if="block.payload.file_url">
                                    <iframe
                                      v-if="block.type === 'pdf'"
                                      :src="block.payload.file_url"
                                      width="100%"
                                      height="600"
                                      style="border: 1px solid #ccc; border-radius: 12px"
                                    ></iframe>

                                    <div
                                      v-else-if="block.type === 'docx'"
                                      class="text-sm text-slate-700"
                                    >
                                      File Word không thể xem trực tiếp. Tải về để mở:
                                      <a
                                        :href="block.payload.file_url"
                                        target="_blank"
                                        class="text-sky-600 underline hover:text-sky-700"
                                      >
                                        📥 Xem/Tải tài liệu DOCX
                                      </a>
                                    </div>
                                  </template>

                                  <!-- Nếu chưa có file -->
                                  <p v-else class="text-xs text-gray-500">
                                    📄 Chưa có file {{ block.type.toUpperCase() }} nào được tải lên.
                                  </p>
                                </div>

                                <!-- QUIZ -->
                                <div v-else-if="block.type === 'quiz'" class="space-y-3">
                                  <div class="rounded-lg border border-slate-200 bg-slate-50 p-4">
                                    <div class="flex items-center justify-between">
                                      <div>
                                        <p class="text-sm font-medium text-slate-800">
                                          📘 Bài kiểm tra
                                        </p>
                                        <p class="text-xs text-slate-500">
                                          Soạn thảo câu hỏi và đáp án cho bài kiểm tra
                                        </p>
                                      </div>

                                      <button
                                        type="button"
                                        class="btn-secondary text-sm"
                                        @click="openQuizEditor(block)"
                                      >
                                        ✏️ Chỉnh sửa
                                      </button>
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
      <transition>
        <div
          v-if="quizEditor.open"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          @click.self="quizEditor.open = false"
        >
          <div class="w-full max-w-3xl bg-white p-5 max-h-[90vh] overflow-y-auto">
            <!-- Header -->
            <div class="mb-4 flex items-center justify-between">
              <h2 class="text-lg font-semibold">✏️ Chỉnh sửa bài kiểm tra</h2>
              <button @click="quizEditor.open = false">✕</button>
            </div>

            <!-- Loading -->
            <p v-if="quizEditor.loading" class="text-sm text-slate-500">Đang tải câu hỏi…</p>

            <!-- Error -->
            <p v-else-if="quizEditor.error" class="text-sm text-rose-600">
              {{ quizEditor.error }}
            </p>

            <!-- Questions -->
            <div v-else class="space-y-4">
              <div
                v-for="(q, index) in quizEditor.questions"
                :key="q.id"
                class="rounded-lg border p-4"
              >
                <!-- Question header -->
                <div class="mb-2 flex items-center justify-between">
                  <p class="text-sm font-medium">
                    Câu {{ index + 1 }}
                    <span class="ml-2 text-xs text-slate-500">({{ q.type }})</span>
                  </p>
                  <button class="text-xs text-rose-600" @click="deleteQuestion(q.id, index)">
                    Xoá
                  </button>
                </div>

                <!-- Question text -->
                <textarea
                  v-model="q.prompt.text"
                  class="input-field"
                  rows="2"
                  placeholder="Nội dung câu hỏi"
                  @blur="saveQuestion(q)"
                />

                <!-- ===== MULTIPLE CHOICE SINGLE ===== -->
                <div v-if="q.type === 'multiple_choice_single'" class="mt-3 space-y-2">
                  <div
                    v-for="(choice, i) in q.answer_payload.choices"
                    :key="i"
                    class="flex items-center gap-2"
                  >
                    <input
                      type="radio"
                      :name="`correct-${q.id}`"
                      :checked="choice.is_correct"
                      @change="setCorrectChoice(q, i)"
                    />
                    <input
                      v-model="choice.text"
                      class="input-field flex-1"
                      placeholder="Nhập đáp án"
                      @blur="saveQuestion(q)"
                    />
                    <button class="text-xs text-rose-600" @click="removeChoice(q, i)">✕</button>
                  </div>

                  <button class="btn-secondary text-xs" @click="addChoice(q)">+ Thêm đáp án</button>
                </div>

                <!-- ===== MULTIPLE CHOICE MULTI ===== -->
                <div v-else-if="q.type === 'multiple_choice_multi'" class="mt-3 space-y-2">
                  <div
                    v-for="(choice, i) in q.answer_payload.choices"
                    :key="i"
                    class="flex items-center gap-2"
                  >
                    <input type="checkbox" v-model="choice.is_correct" @change="saveQuestion(q)" />
                    <input
                      v-model="choice.text"
                      class="input-field flex-1"
                      placeholder="Nhập đáp án"
                      @blur="saveQuestion(q)"
                    />
                    <button class="text-xs text-rose-600" @click="removeChoice(q, i)">✕</button>
                  </div>

                  <button class="btn-secondary text-xs" @click="addChoice(q)">+ Thêm đáp án</button>
                </div>

                <!-- ===== TRUE / FALSE ===== -->
                <div v-else-if="q.type === 'true_false'" class="mt-3 flex gap-6">
                  <input
                    type="radio"
                    :checked="q.answer_payload.answer === true"
                    @change="setTrueFalse(q, true)"
                  />

                  <input
                    type="radio"
                    :checked="q.answer_payload.answer === false"
                    @change="setTrueFalse(q, false)"
                  />
                </div>

                <!-- ===== SHORT ANSWER ===== -->
                <div v-else-if="q.type === 'short_answer'" class="mt-3 space-y-2">
                  <div
                    v-for="(ans, i) in q.answer_payload.valid_answers"
                    :key="i"
                    class="flex items-center gap-2"
                  >
                    <input
                      v-model="ans.answer"
                      class="input-field flex-1"
                      placeholder="Đáp án hợp lệ"
                      @blur="saveQuestion(q)"
                    />
                    <label class="flex items-center gap-1 text-xs">
                      <input type="checkbox" v-model="ans.case_sensitive" />
                      Phân biệt hoa/thường
                    </label>
                    <button class="text-xs text-rose-600" @click="removeShortAnswer(q, i)">
                      ✕
                    </button>
                  </div>

                  <button class="btn-secondary text-xs" @click="addShortAnswer(q)">
                    + Thêm đáp án
                  </button>
                </div>
              </div>

              <!-- Add question -->

              <div class="flex items-center gap-3 mt-4">
                <select v-model="newQuestionType" class="input-field w-64 text-sm">
                  <option value="multiple_choice_single">Trắc nghiệm – 1 đáp án đúng</option>
                  <option value="multiple_choice_multi">Trắc nghiệm – nhiều đáp án đúng</option>
                  <option value="true_false">Đúng / Sai</option>
                  <option value="short_answer">Tự luận ngắn</option>
                </select>

                <button type="button" class="btn-secondary text-sm" @click="addQuestionToQuiz">
                  + Thêm câu hỏi
                </button>
              </div>
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

// form gốc để so sánh metadata
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
  title?: string
  quiz_id?: string // 👈 BẮT BUỘC
  position: number
  payload: any
  _hydrated?: boolean
}

interface Lesson {
  id?: string
  title: string
  position: number
  content_type: string
  published?: boolean
  content_blocks: ContentBlock[]
  newBlockType?: string // Added newBlockType property
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
const newQuestionType = ref<
  'multiple_choice_single' | 'multiple_choice_multi' | 'true_false' | 'short_answer'
>('multiple_choice_single')

// lưu blob url để revoke
const blobUrls = new Set<string>()
const newBlockType = ref('rich_text')

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

const quizEditor = reactive({
  open: false,
  quizId: null as string | null,
  loading: false,
  questions: [] as any[],
  error: '',
})
async function openQuizEditor(block: any) {
  // nếu chưa hydrate → hydrate trước
  if (!block._hydrated) {
    await hydrateBlock(block)
  }

  const quizId = block.quiz_id || block.payload?.quiz_id

  if (!quizId) {
    showNotification('error', 'Lỗi', 'Quiz chưa được khởi tạo')
    return
  }

  quizEditor.open = true
  quizEditor.quizId = quizId
  loadQuizQuestions(quizId)
}

async function loadQuizQuestions(quizId: string) {
  quizEditor.loading = true
  quizEditor.error = ''

  try {
    const { data } = await axios.get(`/api/quiz/instructor/quizzes/${quizId}/questions/`, {
      headers: getAuthHeaders(),
    })
    quizEditor.questions = data
  } catch (e: any) {
    quizEditor.error = 'Không tải được danh sách câu hỏi'
  } finally {
    quizEditor.loading = false
  }
}
// async function addQuestionToQuiz(type = 'multiple_choice') {
//   if (!quizEditor.quizId) return

//   const { data } = await axios.post(
//     `/api/quiz/instructor/quizzes/${quizEditor.quizId}/questions/`,
//     { type },
//     { headers: getAuthHeaders() },
//   )

//   quizEditor.questions.push(data)
// }
async function addQuestionToQuiz() {
  if (!quizEditor.quizId) return

  const { data } = await axios.post(
    `/api/quiz/instructor/quizzes/${quizEditor.quizId}/questions/`,
    { type: newQuestionType.value },
    { headers: getAuthHeaders() },
  )

  resetQuestionPayload(data)
  quizEditor.questions.push(data)
}

async function saveQuestion(question: any) {
  await axios.patch(
    `/api/quiz/instructor/questions/${question.id}/`,
    {
      type: question.type,
      prompt: question.prompt,
      answer_payload: question.answer_payload,
      hint: question.hint,
    },
    { headers: getAuthHeaders() },
  )
}
async function deleteQuestion(questionId: string, index: number) {
  if (!confirm('Xoá câu hỏi này?')) return

  await axios.delete(`/api/quiz/instructor/questions/${questionId}/`, { headers: getAuthHeaders() })

  quizEditor.questions.splice(index, 1)
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
function setTrueFalse(q: any, value: boolean) {
  q.answer_payload.answer = value
  saveQuestion(q)
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

// ================== PAYLOAD HELPERS ==================
function makeDefaultPayloadForType(type: string) {
  switch (type) {
    case 'rich_text':
      return {
        html_content: '',
      }
    case 'image':
      return {
        caption: '',
        image_id: null,
        image_url: null,
        image_file: null,
        image_preview: null,
        uploading: false,
        uploadError: '',
      }
    case 'video':
      return {
        video_id: null,
        video_url: null,
        video_file: null,
        video_preview: null,
        uploading: false,
        progress: 0,
        uploadError: '',
      }
    case 'pdf':
    case 'docx':
      return {
        file_id: null,
        file_url: null,
        filename: '',
        file: null,
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

// xoá field UI trước khi gửi lên BE
function cleanBlockPayload(payload: any) {
  const cloned = { ...(payload || {}) }
  delete cloned.image_file
  delete cloned.video_file
  delete cloned.file
  delete cloned.image_preview
  delete cloned.video_preview
  delete cloned.file_preview
  delete cloned.uploading
  delete cloned.uploadError
  delete cloned.progress
  return cloned
}

// ================== FETCH COURSE ==================
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
        ? (data.categories[0] as any).name || data.categories[0]
        : ''

    f.subject = data.subject || firstCategoryName || ''
    f.tags = (data.tags || []).map((t: any) => (typeof t === 'string' ? t : t.name || ''))

    tagsInput.value = f.tags.join(', ')

    // clone modules → lessons → blocks + hydrate payload
    f.modules = (data.modules || []).map((m: any, mIndex: number) => ({
      id: m.id,
      title: m.title,
      position: m.position ?? mIndex,
      lessons: (m.lessons || []).map((l: any, lIndex: number) => {
        const lesson: Lesson = {
          id: l.id,
          title: l.title,
          position: l.position ?? lIndex,
          content_type: l.content_type || 'lesson',
          published: l.published,
          content_blocks: [],
          newBlockType: 'rich_text', // ★ thêm vào đây
        }

        const rawBlocks: any[] = l.content_blocks || []
        lesson.content_blocks = rawBlocks.map((b: any, bIndex: number) => {
          const block: ContentBlock = {
            id: b.id,
            type: b.type,
            quiz_id: b.quiz_id, // 👈 CỰC KỲ QUAN TRỌNG
            position: b.position ?? bIndex,
            payload: {
              ...makeDefaultPayloadForType(b.type),
              ...(b.payload || {}),
            },
          }

          // preview media
          if (block.type === 'image' && block.payload?.image_url) {
            fetchBlobUrl(block.payload.image_url).then((url) => {
              if (url) block.payload.image_preview = url
            })
          }

          if (block.type === 'video' && block.payload?.video_url) {
            fetchBlobUrl(block.payload.video_url).then((url) => {
              if (url) block.payload.video_preview = url
            })
          }

          if ((block.type === 'pdf' || block.type === 'docx') && block.payload?.file_url) {
            fetchBlobUrl(block.payload.file_url).then((url) => {
              if (url) block.payload.file_preview = url
            })
          }

          return block
        })

        return lesson
      }),
    }))

    originalForm.value = {
      title: f.title,
      description: f.description,
      grade: f.grade,
      subject: f.subject,
      tags: [...f.tags],
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
  if (coverBlobUrl.value) URL.revokeObjectURL(coverBlobUrl.value)
  const localUrl = URL.createObjectURL(file)
  coverBlobUrl.value = localUrl
  blobUrls.add(localUrl)

  try {
    coverUploading.value = true
    const result = await uploadPresigned(file, 'course_thumbnail')

    coverImageId.value = result.id // ← QUAN TRỌNG
  } catch (err) {
    console.error('❌ Upload cover failed:', err)
    showNotification('error', 'Lỗi', 'Upload ảnh bìa thất bại.')
    coverImageId.value = null
  } finally {
    coverUploading.value = false
  }
}

// ================== UPDATE MODULE / LESSON ==================
async function updateModuleTitle(module: Module) {
  if (!module.id) return
  try {
    await axios.patch(
      `/api/content/instructor/modules/${module.id}/`,
      { title: module.title, position: module.position },
      { headers: getAuthHeaders() },
    )
  } catch (e) {
    console.error('❌ Lỗi cập nhật tên chương:', e)
    showNotification('error', 'Lỗi', 'Không cập nhật được tên chương.')
  }
}

async function updateLessonTitle(lesson: Lesson) {
  if (!lesson.id) return
  try {
    await axios.patch(
      `/api/content/instructor/lessons/${lesson.id}/`,
      { title: lesson.title, position: lesson.position },
      { headers: getAuthHeaders() },
    )
  } catch (e) {
    console.error('❌ Lỗi cập nhật tên bài:', e)
    showNotification('error', 'Lỗi', 'Không cập nhật được tên bài.')
  }
}

// ================== EDIT MODULES / LESSONS ==================
async function addModule() {
  if (!course.value) return

  try {
    const position = f.modules.length

    const { data } = await axios.post(
      `/api/content/instructor/courses/${course.value.id}/modules/`,
      {
        title: `Chương ${position + 1}`,
        position,
      },
      { headers: getAuthHeaders() },
    )

    f.modules.push({
      id: data.id,
      title: data.title,
      position: data.position,
      lessons: [],
    })
  } catch (e) {
    console.error('❌ Lỗi tạo chương:', e)
    showNotification('error', 'Lỗi', 'Không tạo được chương mới. Vui lòng thử lại.')
  }
}

async function handleBlockTypeChange(block: ContentBlock) {
  if (!block.id) {
    // block local chưa sync → chỉ đổi local
    block.payload = makeDefaultPayloadForType(block.type)
    return
  }

  block.payload = makeDefaultPayloadForType(block.type)

  try {
    await axios.patch(
      `/api/content/instructor/blocks/${block.id}/`,
      { type: block.type },
      { headers: getAuthHeaders() },
    )
  } catch (e) {
    console.error('❌ Lỗi đổi loại block:', e)
    showNotification('error', 'Lỗi', 'Không cập nhật được loại nội dung.')
  }
}
async function onBlockTypeChange(
  block: ContentBlock,
  mIndex: number,
  lIndex: number,
  bIndex: number,
) {
  if (!block.id) {
    // local block → chỉ đổi payload FE
    block.payload = makeDefaultPayloadForType(block.type)
    return
  }

  try {
    // Gửi PATCH cập nhật type theo đúng API BE
    await axios.patch(
      `/api/content/instructor/blocks/${block.id}/`,
      {
        type: block.type,
        payload: makeDefaultPayloadForType(block.type), // BE sẽ override lại
      },
      { headers: getAuthHeaders() },
    )

    // Update FE payload theo loại block
    block.payload = makeDefaultPayloadForType(block.type)
  } catch (e: any) {
    console.error('❌ change block type failed:', e)
    showNotification('error', 'Lỗi', 'Không đổi được loại nội dung.')
  }
}

async function removeModule(mIndex: number) {
  const mod = f.modules[mIndex]
  if (!mod?.id) {
    // module chưa sync lên BE → xoá local
    f.modules.splice(mIndex, 1)
    f.modules.forEach((m, idx) => (m.position = idx))
    return
  }

  if (!confirm('Xoá chương này và toàn bộ bài học bên trong?')) return

  try {
    await axios.delete(`/api/content/instructor/modules/${mod.id}/`, {
      headers: getAuthHeaders(),
    })

    f.modules.splice(mIndex, 1)
    f.modules.forEach((m, idx) => (m.position = idx))
  } catch (e) {
    console.error('❌ Lỗi xoá chương:', e)
    showNotification('error', 'Lỗi', 'Không xoá được chương. Vui lòng thử lại.')
  }
}

async function addLesson(mIndex: number) {
  const mod = f.modules[mIndex]
  if (!mod?.id) {
    showNotification('error', 'Lỗi', 'Chương chưa sync lên server, không tạo bài được.')
    return
  }

  try {
    const position = mod.lessons.length
    const { data } = await axios.post(
      `/api/content/instructor/modules/${mod.id}/lessons/`,
      {
        title: `Bài ${position + 1}`,
        position,
        content_type: 'lesson',
      },
      { headers: getAuthHeaders() },
    )

    const lesson: Lesson = {
      id: data.id,
      title: data.title,
      position: data.position,
      content_type: data.content_type || 'lesson',
      published: data.published ?? false,
      content_blocks: [],
    }

    mod.lessons.push(lesson)
  } catch (e) {
    console.error('❌ Lỗi tạo bài học:', e)
    showNotification('error', 'Lỗi', 'Không tạo được bài học mới.')
  }
}

// async function saveBlock(block: any) {
//   if (!block.id) return

//   await axios.patch(
//     `/api/content/instructor/blocks/${block.id}/`,
//     {
//       type: block.type,
//       payload: cleanBlockPayload(block.payload),
//       position: block.position,
//     },
//     { headers: getAuthHeaders() },
//   )
// }

async function removeLesson(mIndex: number, lIndex: number) {
  const lesson = f.modules[mIndex].lessons[lIndex]
  if (!lesson?.id) {
    f.modules[mIndex].lessons.splice(lIndex, 1)
    f.modules[mIndex].lessons.forEach((l, idx) => (l.position = idx))
    return
  }

  if (!confirm('Xoá bài học này và toàn bộ nội dung bên trong?')) return

  try {
    await axios.delete(`/api/content/instructor/lessons/${lesson.id}/`, {
      headers: getAuthHeaders(),
    })

    f.modules[mIndex].lessons.splice(lIndex, 1)
    f.modules[mIndex].lessons.forEach((l, idx) => (l.position = idx))
  } catch (e) {
    console.error('❌ Lỗi xoá bài:', e)
    showNotification('error', 'Lỗi', 'Không xoá được bài học.')
  }
}

// ================== CONTENT BLOCKS ==================
async function addContentBlock(mIndex: number, lIndex: number) {
  const lesson = f.modules[mIndex].lessons[lIndex]
  const type = lesson.newBlockType || 'rich_text'

  const body: any = { type }

  if (type === 'quiz') {
    body.title = 'Bài kiểm tra mới' // 👈 BẮT BUỘC
    body.payload = {} // 👈 payload để trống OK
  }

  const { data } = await axios.post(`/api/content/instructor/lessons/${lesson.id}/blocks/`, body, {
    headers: getAuthHeaders(),
  })

  lesson.content_blocks.push({
    id: data.id,
    type: data.type,
    title: data.title,
    quiz_id: data.quiz_id, // 👈 CỰC KỲ QUAN TRỌNG
    position: data.position,
    payload: data.payload || {},
    _hydrated: true,
  })
}

async function hydrateBlock(block: any) {
  if (!block?.id) return
  if (block._hydrated) return

  const { data } = await axios.get(`/api/content/instructor/blocks/${block.id}/`, {
    headers: getAuthHeaders(),
  })

  block.type = data.type
  block.title = data.title

  block.quiz_id = data.quiz_id || data.payload?.quiz_id

  block.payload = {
    ...makeDefaultPayloadForType(data.type),
    ...(data.payload || {}),
  }

  // ===== MEDIA PREVIEW =====
  if (data.payload?.image_url) {
    block.payload.image_preview = await fetchBlobUrl(data.payload.image_url)
  }

  if (data.type === 'video' && !data.payload?.video_url && data.payload?.processing) {
    block.payload.uploading = false
    block.payload.uploadError = ''
    showNotification(
      'success',
      'Đang xử lý',
      'Video đang được xử lý, vui lòng tải lại trang sau ít phút.',
    )
  }

  if (data.payload?.file_url) {
    block.payload.file_preview = await fetchBlobUrl(data.payload.file_url)
  }

  block._hydrated = true
}

async function removeContentBlock(mIndex: number, lIndex: number, bIndex: number) {
  const lesson = f.modules[mIndex].lessons[lIndex]
  const block = lesson.content_blocks[bIndex]

  // block local chưa sync
  if (!block?.id) {
    lesson.content_blocks.splice(bIndex, 1)
    lesson.content_blocks.forEach((b, idx) => (b.position = idx))
    return
  }

  if (!confirm('Xoá nội dung này?')) return

  try {
    await axios.delete(`/api/content/instructor/blocks/${block.id}/`, {
      headers: getAuthHeaders(),
    })

    lesson.content_blocks.splice(bIndex, 1)
    lesson.content_blocks.forEach((b, idx) => (b.position = idx))
  } catch (e) {
    console.error('❌ Lỗi xoá block:', e)
    showNotification('error', 'Lỗi', 'Không xoá được nội dung.')
  }
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
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  const block = f.modules[mIndex].lessons[lIndex].content_blocks[bIndex]
  block.payload.uploading = true
  block.payload.uploadError = ''

  // preview local
  const preview = URL.createObjectURL(file)
  blobUrls.add(preview)

  if (kind === 'image') block.payload.image_preview = preview
  if (kind === 'video') block.payload.video_preview = preview

  try {
    const result = await uploadPresigned(file, 'lesson_material')

    if (kind === 'image') {
      block.payload.image_id = result.id
      block.payload.image_url = result.url
    }

    if (kind === 'video') {
      block.payload.video_id = result.id
      block.payload.video_url = result.url
    }

    if (kind === 'file') {
      block.payload.file_id = result.id
      block.payload.file_url = result.url
    }

    await saveBlock(block)
    await hydrateBlock(block) // 👈 QUAN TRỌNG
  } catch (e) {
    block.payload.uploadError = 'Upload thất bại'
  } finally {
    block.payload.uploading = false
  }
}

// ================== QUIZ HELPERS ==================
function ensureQuizPayload(block: any) {
  if (!block.payload) block.payload = {}
  if (!block.payload.questions) block.payload.questions = []
  if (!block.payload.title) block.payload.title = ''
  if (!block.payload.time_limit) block.payload.time_limit = ''
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
    case 'short_answer':
      question.answer_payload = { valid_answers: [] }
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

function addShortAnswer(question: any) {
  if (!question.answer_payload.valid_answers) question.answer_payload.valid_answers = []
  question.answer_payload.valid_answers.push({ answer: '', case_sensitive: false })
}

function removeShortAnswer(question: any, idx: number) {
  question.answer_payload.valid_answers.splice(idx, 1)
}

async function uploadPresigned(file: File, component: string) {
  // 1) INIT
  const initRes = await axios.post(
    '/api/media/upload/init/',
    {
      filename: file.name,
      file_type: file.type,
      file_size: file.size,
      component,
    },
    { headers: getAuthHeaders() },
  )

  const { file_id, upload_url, upload_fields } = initRes.data

  if (!file_id || !upload_url || !upload_fields) throw new Error('Presigned info is invalid')

  // 2) UPLOAD S3
  const formData = new FormData()
  Object.entries(upload_fields).forEach(([k, v]) => formData.append(k, v))
  formData.append('file', file)

  await axios.post(upload_url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  // 3) CONFIRM
  const confirm = await axios.post(
    `/api/media/upload/confirm/${file_id}/`,
    {},
    { headers: getAuthHeaders() },
  )

  return confirm.data // { id, url, ... }
}

// ================== UTILS ==================
function shallowEqualJSON(a: any, b: any): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

// ================== SUBMIT (PATCH metadata) ==================
async function submit() {
  titleErr.value = ''
  if (!f.title || !f.title.trim()) {
    titleErr.value = 'Vui lòng nhập tên khoá học.'
    return
  }

  if (!course.value) return

  const payload: any = {}

  if (!originalForm.value || f.title !== originalForm.value.title) {
    payload.title = f.title
  }
  if (!originalForm.value || f.description !== originalForm.value.description) {
    payload.description = f.description
  }
  if (!originalForm.value || String(f.grade) !== String(originalForm.value.grade)) {
    payload.grade = String(f.grade)
  }
  if (!originalForm.value || f.subject !== originalForm.value.subject) {
    payload.subject = f.subject || null
    payload.categories = f.subject ? [f.subject] : []
  }
  if (!originalForm.value || !shallowEqualJSON(f.tags, originalForm.value.tags)) {
    payload.tags = f.tags
  }
  if (coverImageId.value) {
    payload.image_id = coverImageId.value
  }

  if (Object.keys(payload).length === 0) {
    showNotification('success', 'Không có thay đổi', 'Không có metadata nào cần lưu.')
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

    showNotification('success', 'Thành công', 'Đã lưu thông tin khoá học.')

    originalForm.value = {
      title: f.title,
      description: f.description,
      grade: f.grade,
      subject: f.subject,
      tags: [...f.tags],
      modules: originalForm.value?.modules || [],
    }
  } catch (e: any) {
    console.error('❌ Lỗi khi cập nhật metadata khoá học:', e)
    showNotification(
      'error',
      'Lỗi',
      e?.response?.data?.detail ||
        e?.message ||
        'Có lỗi xảy ra khi lưu thông tin khoá học. Vui lòng thử lại.',
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
