<template>
  <Teleport to="body">
    <!-- ✅ đảm bảo thoát khỏi Navbar DOM -->
    <div v-if="open" class="fixed inset-0 z-[9999] flex items-center justify-center">
      <!-- overlay -->
      <div class="absolute inset-0 bg-black/50" @click="close"></div>

      <!-- modal -->
      <div
        class="relative z-[10000] w-11/12 max-w-md p-6 rounded-lg shadow-xl bg-white"
        :style="containerStyle"
        role="dialog"
        aria-modal="true"
      >
        <h3 class="text-lg font-semibold mb-2">Bạn có chắc muốn đăng xuất không?</h3>
        <p class="text-sm text-gray-600 mb-4">
          Hành động này sẽ đăng bạn khỏi phiên làm việc hiện tại.
        </p>

        <div class="flex justify-end gap-3">
          <button @click="close" class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200">
            Hủy
          </button>
          <button @click="confirm" class="px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700">
            Đăng xuất
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { defineProps, defineEmits } from 'vue'
import type { CSSProperties } from 'vue'

type AnchorRect = { top: number; left: number; width: number; height: number } | null

const props = defineProps({
  open: { type: Boolean, default: false },
  anchor: { type: Object as () => AnchorRect, default: null },
})
const emit = defineEmits(['update:open', 'confirm'])

function close() {
  emit('update:open', false)
}

function confirm() {
  emit('confirm')
  emit('update:open', false)
}

const containerStyle = computed<CSSProperties>(() => {
  const base: CSSProperties = {
    position: 'fixed',
    left: '50%',
    top: '50%',
    transform: 'translate(-50%, -50%)',
    width: 'min(520px, 90vw)',
  }

  if (props.anchor) {
    const top = props.anchor.top + props.anchor.height + 8
    const left = props.anchor.left + props.anchor.width / 2
    return {
      position: 'fixed',
      top: `${top}px`,
      left: `${left}px`,
      transform: 'translateX(-50%)',
      width: 'min(260px, 90vw)',
    }
  }

  return base
})
</script>

<style scoped>
/* tuỳ chỉnh nếu cần */
</style>
