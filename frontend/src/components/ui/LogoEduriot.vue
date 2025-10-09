<template>
  <div class="nav" :style="{ height: size + 'px' }">
    <img
      v-if="show"
      :src="logo"
      alt="EDURIOT logo"
      class="logo-eduriot"
      :style="{ transform: `scale(${scale})`, height: size + 'px' }"
    />
  </div>
</template>

<script setup>
const props = defineProps({
  size: { type: Number, default: 56 }, // Thêm prop size
  scale: { type: Number, default: 1.2 },
  show: { type: Boolean, default: true },
})
import logo from '@/assets/images/demologo.png'
</script>

<style scoped>
.nav {
  display: flex;
  align-items: center;
  overflow: visible;
}
.logo-eduriot {
  width: auto;
  transform-origin: left center;
  transition: transform 0.2s ease;
}
</style>
