# E-Learning Frontend

## Giới thiệu
Đây là dự án frontend cho hệ thống e-learning, sử dụng Vue 3 + Vite. Dự án hỗ trợ nhiều vai trò: học sinh, phụ huynh, admin.

## Cài đặt
```bash
npm install
```

## Chạy dự án
```bash
npm run dev
```

## Cấu trúc thư mục
```
src/
├─ router/                # Quản lý định tuyến
│  ├─ index.ts            # Khởi tạo router
│  └─ guards.ts           # Định nghĩa các guard cho route
├─ stores/                # Quản lý trạng thái
│  ├─ index.ts            # Store chính
│  ├─ user.ts             # Store người dùng
│  └─ progress.ts         # Store tiến trình học tập
├─ views/                 # Các trang giao diện
│  ├─ auth/               # Trang xác thực
│  │  ├─ LoginPage.vue
│  │  └─ RegisterPage.vue
│  ├─ student/            # Trang học sinh
│  │  ├─ Dashboard.vue
│  │  └─ LessonDetail.vue
│  ├─ parent/             # Trang phụ huynh
│  │  └─ Reports.vue
│  └─ admin/              # Trang admin
│     ├─ ContentManager.vue
│     └─ Users.vue
├─ components/            # Các component dùng chung
│  ├─ common/
│  ├─ student/
│  └─ charts/
├─ services/              # Các service dùng chung
│  ├─ http.ts
│  └─ storage.ts
├─ api/                   # Định nghĩa các API
│  ├─ auth.api.ts
│  ├─ lessons.api.ts
│  └─ reports.api.ts
├─ plugins/               # Các plugin
│  ├─ element-plus.ts
│  └─ i18n.ts
├─ locales/               # Đa ngôn ngữ
│  ├─ vi.json
│  └─ en.json
├─ styles/                # Style chung
│  ├─ index.scss
│  └─ variables.scss
└─ directives/            # Directive tuỳ chỉnh
   └─ permission.ts
```

## Ghi chú
- Sử dụng Vite để phát triển, build nhanh.
- Sử dụng Vue Router cho điều hướng.
- Sử dụng Pinia/Vuex cho quản lý trạng thái.
- Đa ngôn ngữ qua plugin i18n.
- UI sử dụng Element Plus.

## Liên hệ
Nếu có vấn đề hoặc cần hỗ trợ, vui lòng liên hệ nhóm phát triển.
