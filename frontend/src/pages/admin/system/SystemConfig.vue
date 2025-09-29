<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div class="text-lg font-semibold">Cấu hình hệ thống</div>
          <div class="text-xs text-gray-500">
            Phiên bản: v{{ form.version }} • cập nhật bởi {{ form.updatedBy }} •
            {{ fmt(form.updatedAt) }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <el-button @click="load">Tải lại</el-button>
          <el-button type="primary" :loading="saving" @click="save">Lưu nháp</el-button>
          <el-button type="success" :loading="saving" @click="apply">Áp dụng</el-button>
        </div>
      </div>
    </div>

    <div class="rounded-lg bg-white p-0 ring-1 ring-black/5 overflow-hidden">
      <el-tabs v-model="tab" class="px-4 pt-2">
        <!-- Brand -->
        <el-tab-pane label="Tổng quan" name="brand">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <el-form label-position="top">
              <el-form-item label="Tên hệ thống">
                <el-input v-model="form.brand.siteName" />
              </el-form-item>
              <el-form-item label="Ngôn ngữ mặc định">
                <el-select v-model="form.brand.language">
                  <el-option label="Tiếng Việt" value="vi" />
                  <el-option label="English" value="en" />
                </el-select>
              </el-form-item>
              <el-form-item label="Múi giờ">
                <el-input v-model="form.brand.timezone" />
              </el-form-item>
              <el-form-item label="Tiền tệ">
                <el-input v-model="form.brand.currency" disabled />
              </el-form-item>
            </el-form>
            <div>
              <div class="text-sm font-medium mb-2">Logo</div>
              <div class="flex items-center gap-3">
                <img
                  v-if="form.brand.logoUrl"
                  :src="form.brand.logoUrl"
                  class="h-12 w-12 rounded object-contain ring-1 ring-black/10"
                />
                <div class="text-xs text-gray-500">Dán URL logo vào:</div>
              </div>
              <el-input v-model="form.brand.logoUrl" placeholder="https://..." class="mt-2" />
            </div>
          </div>
        </el-tab-pane>

        <!-- Domain & Email -->
        <el-tab-pane label="Domain & Email" name="email">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <el-form label-position="top">
              <el-form-item label="Domain">
                <el-input v-model="form.domainEmail.domain" />
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="form.domainEmail.forceHttps">Bắt buộc HTTPS</el-checkbox>
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="form.domainEmail.hsts">Bật HSTS</el-checkbox>
              </el-form-item>
              <div class="text-xs text-gray-600">
                SPF/DKIM/DMARC:
                <el-tag size="small" :type="badge(form.domainEmail.spf?.status)">{{
                  form.domainEmail.spf?.status || 'unknown'
                }}</el-tag>
                <el-tag size="small" :type="badge(form.domainEmail.dkim?.status)">{{
                  form.domainEmail.dkim?.status || 'unknown'
                }}</el-tag>
                <el-tag size="small" :type="badge(form.domainEmail.dmarc?.status)">{{
                  form.domainEmail.dmarc?.status || 'unknown'
                }}</el-tag>
              </div>
            </el-form>

            <el-form label-position="top">
              <div class="text-sm font-medium mb-1">SMTP</div>
              <div class="grid grid-cols-2 gap-3">
                <el-form-item label="Host"
                  ><el-input v-model="form.domainEmail.smtp.host"
                /></el-form-item>
                <el-form-item label="Port"
                  ><el-input-number
                    v-model="form.domainEmail.smtp.port"
                    :min="1"
                    :max="65535"
                    class="w-full"
                /></el-form-item>
              </div>
              <el-form-item label="Username"
                ><el-input v-model="form.domainEmail.smtp.username"
              /></el-form-item>
              <el-form-item label="Sender name"
                ><el-input v-model="form.domainEmail.smtp.senderName"
              /></el-form-item>
              <el-form-item label="From email"
                ><el-input v-model="form.domainEmail.smtp.fromEmail"
              /></el-form-item>
              <div class="flex items-center gap-2 text-xs text-gray-500">
                Mật khẩu:
                <el-tag size="small" type="info">{{
                  form.domainEmail.smtp.passwordMasked ? '****** (masked)' : '(chưa thiết lập)'
                }}</el-tag>
                <el-tooltip content="Đổi mật khẩu ở BE; FE không hiển thị raw password."
                  ><i class="i-ep-warning text-yellow-500"></i
                ></el-tooltip>
              </div>
              <div class="mt-3 flex gap-2">
                <el-input v-model="testMail" placeholder="Email test" class="max-w-60" />
                <el-button :loading="testingMail" @click="sendTestMail">Gửi test</el-button>
              </div>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Auth & Session -->
        <el-tab-pane label="Auth & Session" name="auth">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <el-form label-position="top">
              <div class="grid grid-cols-2 gap-3">
                <el-form-item label="Idle timeout (phút)"
                  ><el-input-number
                    v-model="form.authSession.idleTimeoutMin"
                    :min="1"
                    class="w-full"
                /></el-form-item>
                <el-form-item label="Max session (giờ)"
                  ><el-input-number
                    v-model="form.authSession.maxSessionHours"
                    :min="1"
                    class="w-full"
                /></el-form-item>
                <el-form-item label="Remember-me (ngày)"
                  ><el-input-number
                    v-model="form.authSession.rememberMeDays"
                    :min="1"
                    class="w-full"
                /></el-form-item>
              </div>
              <el-divider />
              <el-checkbox v-model="form.authSession.ssoGoogleEnabled"
                >Bật đăng nhập Google</el-checkbox
              >
              <el-form-item label="Google Client ID" v-if="form.authSession.ssoGoogleEnabled">
                <el-input v-model="form.authSession.googleClientId" />
              </el-form-item>
              <el-divider />
              <div class="text-sm font-medium">2FA bắt buộc</div>
              <el-checkbox v-model="form.authSession.twoFAEnforce.admin">Admin</el-checkbox>
              <el-checkbox v-model="form.authSession.twoFAEnforce.teacher">Teacher</el-checkbox>
              <el-divider />
              <div class="text-sm font-medium mb-1">Chính sách mật khẩu</div>
              <div class="grid grid-cols-2 gap-3">
                <el-form-item label="Độ dài tối thiểu"
                  ><el-input-number
                    v-model="form.authSession.passwordPolicy.minLength"
                    :min="6"
                    class="w-full"
                /></el-form-item>
                <el-form-item label="Phải có số">
                  <el-switch v-model="form.authSession.passwordPolicy.requireNumbers" />
                </el-form-item>
                <el-form-item label="Phải có ký tự đặc biệt">
                  <el-switch v-model="form.authSession.passwordPolicy.requireSymbols" />
                </el-form-item>
              </div>
              <el-divider />
              <el-checkbox v-model="form.authSession.singleDeviceOnly"
                >Giới hạn 1 thiết bị đăng nhập</el-checkbox
              >
            </el-form>

            <!-- Backup -->
            <el-form label-position="top">
              <div class="text-sm font-medium mb-1">Backup</div>
              <div class="grid grid-cols-2 gap-3">
                <el-form-item label="Lịch backup">
                  <el-select v-model="form.backup.schedule">
                    <el-option label="Hourly" value="hourly" />
                    <el-option label="Daily" value="daily" />
                    <el-option label="Weekly" value="weekly" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Retention (ngày)">
                  <el-input-number v-model="form.backup.retentionDays" :min="1" class="w-full" />
                </el-form-item>
                <el-form-item label="RPO (phút)">
                  <el-input-number v-model="form.backup.rpoMinutes" :min="1" class="w-full" />
                </el-form-item>
                <el-form-item label="RTO (phút)">
                  <el-input-number v-model="form.backup.rtoMinutes" :min="1" class="w-full" />
                </el-form-item>
              </div>
              <el-form-item label="Mã hoá bản sao lưu">
                <el-switch v-model="form.backup.encrypted" />
              </el-form-item>

              <div class="mt-3 flex gap-2">
                <el-button :loading="creatingBk" @click="createBackup">Tạo backup</el-button>
                <el-button @click="openRestore">Phục hồi</el-button>
              </div>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Integrations -->
        <el-tab-pane label="Tích hợp" name="integrations">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="rounded-md border p-4">
              <div class="font-medium mb-2">Cổng thanh toán</div>
              <div class="grid grid-cols-2 gap-3">
                <el-checkbox v-model="form.integrations.payments.momo">Momo</el-checkbox>
                <el-checkbox v-model="form.integrations.payments.vnpay">VNPay</el-checkbox>
                <el-checkbox v-model="form.integrations.payments.qr">QR</el-checkbox>
                <el-checkbox v-model="form.integrations.payments.bank">Ngân hàng</el-checkbox>
              </div>
            </div>
            <div class="rounded-md border p-4">
              <div class="font-medium mb-2">Analytics & Zoom</div>
              <el-form label-position="top">
                <el-form-item label="GA4 Measurement ID">
                  <el-input v-model="form.integrations.analytics.ga4MeasurementId" />
                </el-form-item>
                <el-form-item label="Zoom">
                  <el-switch v-model="form.integrations.zoom.enabled" />
                </el-form-item>
              </el-form>
            </div>

            <div class="rounded-md border p-4 md:col-span-2">
              <div class="font-medium mb-2">Storage</div>
              <div class="grid grid-cols-3 gap-3">
                <el-form-item label="Provider">
                  <el-select v-model="form.integrations.storage.provider">
                    <el-option label="Local" value="local" />
                    <el-option label="S3" value="s3" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Bucket">
                  <el-input v-model="form.integrations.storage.bucket" />
                </el-form-item>
                <el-form-item label="Region">
                  <el-input v-model="form.integrations.storage.region" />
                </el-form-item>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Logging -->
        <el-tab-pane label="Logging" name="logging">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <el-form label-position="top">
              <el-form-item label="Mức log">
                <el-select v-model="form.logging.level">
                  <el-option label="info" value="info" />
                  <el-option label="warn" value="warn" />
                  <el-option label="error" value="error" />
                </el-select>
              </el-form-item>
              <el-form-item label="Retention (ngày)">
                <el-input-number v-model="form.logging.retentionDays" :min="7" class="w-full" />
              </el-form-item>
              <el-form-item label="Bật Trace ID">
                <el-switch v-model="form.logging.traceIdEnabled" />
              </el-form-item>
            </el-form>

            <div>
              <div class="font-medium mb-2">Lịch sử chỉnh sửa cấu hình</div>
              <el-table :data="audits" height="300">
                <el-table-column prop="version" label="Version" width="100" />
                <el-table-column prop="key" label="Key" />
                <el-table-column prop="actor" label="Bởi" width="160" />
                <el-table-column label="Thời gian" width="180">
                  <template #default="{ row }">{{ fmt(row.at) }}</template>
                </el-table-column>
                <el-table-column prop="note" label="Ghi chú" />
              </el-table>
            </div>
          </div>

          <el-divider />

          <div class="font-medium mb-2">Danh sách backup</div>
          <el-table :data="backups" height="280">
            <el-table-column prop="id" label="ID" width="160" />
            <el-table-column label="Tạo lúc" width="200">
              <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
            </el-table-column>
            <el-table-column label="Kích thước" width="120" align="right">
              <template #default="{ row }">{{ row.sizeMB }} MB</template>
            </el-table-column>
            <el-table-column prop="notes" label="Ghi chú" />
            <el-table-column fixed="right" width="140">
              <template #default="{ row }">
                <el-button size="small" @click="restore(row.id)">Phục hồi</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Restore dialog -->
    <el-dialog v-model="restoreDialog" title="Phục hồi từ backup" width="420px">
      <el-select v-model="selectedBackup" placeholder="Chọn bản backup">
        <el-option
          v-for="b in backups"
          :key="b.id"
          :label="`${b.id} • ${fmt(b.createdAt)}`"
          :value="b.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="restoreDialog = false">Huỷ</el-button>
        <el-button
          type="primary"
          :disabled="!selectedBackup"
          :loading="restoring"
          @click="doRestore"
          >Phục hồi</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  systemService,
  type SystemConfig,
  type BackupItem,
  type ConfigAuditItem,
} from '@/services/system.service'

const tab = ref<'brand' | 'email' | 'auth' | 'integrations' | 'logging'>('brand')
const saving = ref(false)
const creatingBk = ref(false)
const restoring = ref(false)
const testingMail = ref(false)

const form = reactive<SystemConfig>({
  brand: { siteName: '', language: 'vi', timezone: 'Asia/Bangkok', currency: 'VND', logoUrl: '' },
  domainEmail: {
    domain: '',
    forceHttps: true,
    hsts: true,
    smtp: {
      host: '',
      port: 587,
      username: '',
      passwordMasked: true,
      senderName: '',
      fromEmail: '',
    },
  },
  authSession: {
    idleTimeoutMin: 30,
    maxSessionHours: 24,
    rememberMeDays: 14,
    ssoGoogleEnabled: false,
    googleClientId: '',
    twoFAEnforce: { admin: true, teacher: false },
    passwordPolicy: { minLength: 8, requireNumbers: true, requireSymbols: true },
    singleDeviceOnly: true,
  },
  backup: {
    schedule: 'daily',
    retentionDays: 30,
    rpoMinutes: 15,
    rtoMinutes: 120,
    encrypted: true,
  },
  maintenance: { enabled: false, window: { dayOfWeek: 0, start: '01:00', end: '03:00' } },
  integrations: {
    payments: { momo: true, vnpay: true, qr: true, bank: true },
    analytics: {},
    zoom: { enabled: false },
    storage: { provider: 'local' },
  },
  logging: { level: 'info', retentionDays: 90, traceIdEnabled: true },
  version: 0,
  updatedBy: '',
  updatedAt: new Date().toISOString(),
})

const backups = ref<BackupItem[]>([])
const audits = ref<ConfigAuditItem[]>([])

const restoreDialog = ref(false)
const selectedBackup = ref<string | null>(null)
const testMail = ref('')

function fmt(iso?: string) {
  return iso ? new Date(iso).toLocaleString('vi-VN') : ''
}
function badge(s?: string) {
  return s === 'pass' ? 'success' : s === 'fail' ? 'danger' : 'info'
}

async function load() {
  const [cfg, bks, ads] = await Promise.all([
    systemService.getConfig(),
    systemService.listBackups(),
    systemService.listConfigAudit(),
  ])
  Object.assign(form, cfg)
  backups.value = bks
  audits.value = ads
}

async function save() {
  saving.value = true
  try {
    await systemService.updateConfig(form)
    ElMessage.success('Đã lưu nháp (mock)')
    await load()
  } finally {
    saving.value = false
  }
}
async function apply() {
  await save()
  ElMessage.success('Đã áp dụng cấu hình (mock)')
}
async function createBackup() {
  creatingBk.value = true
  try {
    await systemService.createBackup('manual')
    ElMessage.success('Đã tạo backup (mock)')
    backups.value = await systemService.listBackups()
  } finally {
    creatingBk.value = false
  }
}
function openRestore() {
  selectedBackup.value = backups.value[0]?.id || null
  restoreDialog.value = true
}
async function doRestore() {
  if (!selectedBackup.value) return
  restoring.value = true
  try {
    await systemService.restoreBackup(selectedBackup.value)
    ElMessage.success('Đã gửi yêu cầu phục hồi (mock)')
    restoreDialog.value = false
  } finally {
    restoring.value = false
  }
}
async function restore(id: string) {
  selectedBackup.value = id
  restoreDialog.value = true
}
async function sendTestMail() {
  if (!testMail.value) return ElMessage.warning('Nhập email test')
  testingMail.value = true
  try {
    await systemService.sendTestEmail(testMail.value)
    ElMessage.success('Đã gửi email test (mock)')
  } finally {
    testingMail.value = false
  }
}

onMounted(load)
</script>
