<template>
  <div class="space-y-4">
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="flex items-center justify-between">
        <div class="text-lg font-semibold">Bảo mật hệ thống</div>
        <div class="flex gap-2">
          <el-button @click="load">Tải lại</el-button>
          <el-button type="primary" :loading="saving" @click="savePolicy">Lưu chính sách</el-button>
        </div>
      </div>
    </div>

    <div class="rounded-lg bg-white p-0 ring-1 ring-black/5 overflow-hidden">
      <el-tabs v-model="tab" class="px-4 pt-2">
        <!-- Policy -->
        <el-tab-pane label="Chính sách" name="policy">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="rounded-md border p-4">
              <div class="font-medium mb-2">2FA</div>
              <el-checkbox v-model="policy.twoFA.enforceAdmin">Bắt buộc cho Admin</el-checkbox
              ><br />
              <el-checkbox v-model="policy.twoFA.enforceTeacher">Bắt buộc cho Teacher</el-checkbox>
              <div class="text-xs text-gray-500 mt-2">HS có thể bật tự nguyện.</div>
            </div>

            <div class="rounded-md border p-4">
              <div class="font-medium mb-2">Rate limit & Lockout</div>
              <div class="grid grid-cols-2 gap-3">
                <el-form-item label="Login sai (lần)">
                  <el-input-number
                    v-model="policy.rateLimit.loginFailures"
                    :min="3"
                    class="w-full"
                  />
                </el-form-item>
                <el-form-item label="Trong (phút)">
                  <el-input-number v-model="policy.rateLimit.windowMin" :min="1" class="w-full" />
                </el-form-item>
                <el-form-item label="Ngưỡng lockout (lần)">
                  <el-input-number v-model="policy.lockout.attempts" :min="3" class="w-full" />
                </el-form-item>
                <el-form-item label="Khoá (phút)">
                  <el-input-number v-model="policy.lockout.lockMinutes" :min="1" class="w-full" />
                </el-form-item>
                <el-form-item label="Ban vĩnh viễn sau (lần)">
                  <el-input-number v-model="policy.lockout.banStrikes" :min="3" class="w-full" />
                </el-form-item>
              </div>
            </div>
          </div>
          <el-alert
            title="RBAC được quản trị ở backend; mục này chỉ hiển thị mô tả."
            type="info"
            class="mt-4"
            :closable="false"
          />
          <pre class="mt-2 text-xs bg-gray-50 p-3 rounded">{{ policy.rbacNote }}</pre>
        </el-tab-pane>

        <!-- IP Allowlist -->
        <el-tab-pane label="IP Allowlist" name="ip">
          <div class="flex flex-wrap items-end gap-2">
            <el-input v-model="cidr" placeholder="203.0.113.0/24" class="w-56" />
            <el-input v-model="ipNote" placeholder="Ghi chú" class="w-56" />
            <el-button type="primary" @click="addIp">Thêm</el-button>
          </div>

          <el-table :data="ipList" class="mt-4" height="420">
            <el-table-column prop="cidr" label="CIDR" width="200" />
            <el-table-column prop="note" label="Ghi chú" />
            <el-table-column prop="active" label="Kích hoạt" width="120">
              <template #default="{ row }">
                <el-tag size="small" :type="row.active ? 'success' : 'info'">{{
                  row.active ? 'active' : 'off'
                }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createdBy" label="Bởi" width="160" />
            <el-table-column label="Thời gian" width="180">
              <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
            </el-table-column>
            <el-table-column fixed="right" width="120">
              <template #default="{ row }">
                <el-popconfirm title="Xoá IP này?" @confirm="removeIp(row.id)">
                  <template #reference>
                    <el-button size="small" type="danger" plain>Xoá</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- TLS / Cert -->
        <el-tab-pane label="Chứng chỉ & TLS" name="tls">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="rounded-md border p-4">
              <div class="font-medium">Trạng thái chứng chỉ</div>
              <div class="mt-2 text-sm">
                <div>
                  Issuer: <b>{{ cert.issuer }}</b>
                </div>
                <div>Valid: {{ fmt(cert.validFrom) }} → {{ fmt(cert.validTo) }}</div>
                <div>
                  Còn lại: <b>{{ cert.daysRemaining }}</b> ngày
                </div>
                <div>
                  Auto-renew:
                  <el-tag size="small" :type="cert.autoRenew ? 'success' : 'info'">{{
                    cert.autoRenew ? 'ON' : 'OFF'
                  }}</el-tag>
                </div>
                <div v-if="cert.grade">
                  SSL Labs: <b>{{ cert.grade }}</b>
                </div>
              </div>
              <el-button class="mt-3" :loading="renewing" @click="renewCert"
                >Gia hạn (mock)</el-button
              >
            </div>

            <!-- Alert -->
            <div class="rounded-md border p-4">
              <div class="font-medium">Alerting</div>
              <div class="grid grid-cols-2 gap-3 mt-2">
                <el-form-item label="CPU threshold %"
                  ><el-input-number
                    v-model="alertPolicy.cpuThreshold"
                    :min="10"
                    :max="100"
                    class="w-full"
                /></el-form-item>
                <el-form-item label="Error rate %"
                  ><el-input-number
                    v-model="alertPolicy.errorRateThreshold"
                    :min="0"
                    :max="100"
                    class="w-full"
                /></el-form-item>
                <el-form-item label="Kênh email">
                  <el-switch v-model="alertPolicy.channels.email" />
                </el-form-item>
                <el-form-item label="Kênh SMS">
                  <el-switch v-model="alertPolicy.channels.sms" />
                </el-form-item>
              </div>
              <el-form-item label="On-call">
                <el-input v-model="alertPolicy.onCall" />
              </el-form-item>
              <div class="flex gap-2">
                <el-button @click="saveAlerts" :loading="savingAlerts">Lưu Alert</el-button>
                <el-button type="primary" plain :loading="testingAlert" @click="testAlert"
                  >Test Alert</el-button
                >
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Sessions -->
        <el-tab-pane label="Phiên đăng nhập" name="sessions">
          <div class="flex items-center gap-2">
            <el-input v-model="filterUser" placeholder="Lọc theo User ID" class="w-56" />
            <el-button @click="loadSessions">Tải danh sách</el-button>
          </div>
          <el-table :data="sessions" class="mt-3" height="520">
            <el-table-column prop="jti" label="JTI" min-width="160" />
            <el-table-column prop="userId" label="User" width="100" />
            <el-table-column prop="userName" label="Tên" min-width="160" />
            <el-table-column prop="role" label="Vai trò" width="100" />
            <el-table-column prop="ip" label="IP" width="130" />
            <el-table-column prop="device" label="Thiết bị" width="120" />
            <el-table-column prop="location" label="Vị trí" width="100" />
            <el-table-column label="Tạo lúc" width="180">
              <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
            </el-table-column>
            <el-table-column label="Hoạt động" width="180">
              <template #default="{ row }">{{ fmt(row.lastActiveAt) }}</template>
            </el-table-column>
            <el-table-column fixed="right" width="120">
              <template #default="{ row }">
                <el-popconfirm title="Thu hồi phiên này?" @confirm="revoke(row.jti)">
                  <template #reference>
                    <el-button size="small" type="danger" plain>Revoke</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  securityService,
  type SecurityPolicy,
  type IpAllowItem,
  type SessionItem,
  type CertStatus,
  type AlertPolicy,
} from '@/services/security.service'

const tab = ref<'policy' | 'ip' | 'tls' | 'sessions'>('policy')
const saving = ref(false)
const savingAlerts = ref(false)
const renewing = ref(false)
const testingAlert = ref(false)

const policy = reactive<SecurityPolicy>({
  twoFA: { enforceAdmin: true, enforceTeacher: false },
  rateLimit: { loginFailures: 5, windowMin: 10 },
  lockout: { attempts: 5, lockMinutes: 30, banStrikes: 5 },
  rbacNote: '',
})
const ipList = ref<IpAllowItem[]>([])
const sessions = ref<SessionItem[]>([])
const cert = reactive<CertStatus>({
  issuer: '',
  validFrom: '',
  validTo: '',
  daysRemaining: 0,
  autoRenew: true,
})
const alertPolicy = reactive<AlertPolicy>({
  cpuThreshold: 90,
  errorRateThreshold: 2,
  channels: { email: true, sms: true },
  onCall: '',
})

const cidr = ref('')
const ipNote = ref('')
const filterUser = ref<string>('')

function fmt(iso?: string) {
  return iso ? new Date(iso).toLocaleString('vi-VN') : ''
}

async function load() {
  const [p, ips, c, ap] = await Promise.all([
    securityService.getPolicy(),
    securityService.listIpAllow(),
    securityService.getCertStatus(),
    securityService.getAlertPolicy(),
  ])
  Object.assign(policy, p)
  ipList.value = ips
  Object.assign(cert, c)
  Object.assign(alertPolicy, ap)
}
async function savePolicy() {
  saving.value = true
  try {
    await securityService.updatePolicy(policy)
    ElMessage.success('Đã lưu chính sách (mock)')
  } finally {
    saving.value = false
  }
}

async function addIp() {
  if (!cidr.value) return ElMessage.warning('Nhập CIDR')
  await securityService.addIpAllow(cidr.value, ipNote.value)
  cidr.value = ''
  ipNote.value = ''
  ipList.value = await securityService.listIpAllow()
  ElMessage.success('Đã thêm (mock)')
}
async function removeIp(id: string) {
  await securityService.removeIpAllow(id)
  ipList.value = await securityService.listIpAllow()
  ElMessage.success('Đã xoá (mock)')
}

async function loadSessions() {
  const uid = filterUser.value ? Number(filterUser.value) : undefined
  sessions.value = await securityService.listSessions(uid)
}
async function revoke(jti: string) {
  await securityService.revokeSession(jti)
  await loadSessions()
  ElMessage.success('Đã revoke (mock)')
}

async function renewCert() {
  renewing.value = true
  try {
    await securityService.renewCert()
    Object.assign(cert, await securityService.getCertStatus())
    ElMessage.success('Đã gửi yêu cầu gia hạn (mock)')
  } finally {
    renewing.value = false
  }
}

async function saveAlerts() {
  savingAlerts.value = true
  try {
    await securityService.updateAlertPolicy(alertPolicy)
    ElMessage.success('Đã lưu alert (mock)')
  } finally {
    savingAlerts.value = false
  }
}
async function testAlert() {
  testingAlert.value = true
  try {
    await securityService.alertTest()
    ElMessage.success('Đã gửi test alert (mock)')
  } finally {
    testingAlert.value = false
  }
}

onMounted(() => {
  load()
  loadSessions()
})
</script>
