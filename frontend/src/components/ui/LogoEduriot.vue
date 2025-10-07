<template>
  <div class="logo-eduriot flex items-center select-none" :style="{ fontSize: size + 'px' }">
    <!-- Icon -->
    <svg
      v-if="showIcon"
      class="mr-2"
      :width="size"
      :height="size"
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="32" cy="32" r="18" :fill="primary" />
      <path d="M32 20v24M20 32h24" stroke="white" stroke-width="3" stroke-linecap="round" />
      <circle cx="46" cy="18" r="4" :fill="accent" />
    </svg>

    <!-- Text -->
    <span class="font-bold tracking-wide leading-none">
      <span :style="{ color: primary }">Edu</span>
      <span :style="{ color: accent }">Riot</span>
    </span>
  </div>
</template>

<script setup>
/**
 * ✅ Logo EDURIOT — component chuẩn cho header, landing page, favicon.
 * Dễ đổi màu, kích thước, có thể tắt icon, hỗ trợ dark mode tự nhiên.
 */
const props = defineProps({
  size: { type: Number, default: 40 }, // Kích thước base (px)
  primary: { type: String, default: '#2563EB' }, // Màu phần "EDU"
  accent: { type: String, default: '#F97316' }, // Màu phần "RIOT"
  showIcon: { type: Boolean, default: true }, // Bật/tắt icon
})
</script>

<style scoped>
.logo-eduriot {
  font-family: 'Inter', 'Poppins', 'Montserrat', sans-serif;
  line-height: 1;
  transition:
    transform 0.2s ease,
    opacity 0.2s ease;
}
.logo-eduriot:hover {
  transform: scale(1.03);
  opacity: 0.95;
}

/* Dark mode support (nếu app có dark:bg-... thì logo vẫn nổi bật) */
:root.dark .logo-eduriot svg circle {
  filter: brightness(1.1);
}
</style>

<!--
🧩 Usage Examples:

<LogoEduriot /> 
<LogoEduriot :size="48" primary="#6366F1" accent="#F59E0B" />
<LogoEduriot :showIcon="false" />
<LogoEduriot :size="32" primary="#14B8A6" accent="#EAB308" />

💡 Tips:
- Đặt trong header: <div class="flex items-center space-x-2"><LogoEduriot /></div>
- Để favicon: chỉ dùng SVG icon phần trên, xuất riêng.
-->
