<template>
  <el-card class="dashboard-card" shadow="hover">
    <h2>Chào mừng đến với Dashboard Học Sinh</h2>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-statistic title="Bài học đã hoàn thành" :value="completedLessons" />
      </el-col>
      <el-col :span="12">
        <el-statistic title="Tiến độ (%)" :value="progress" suffix="%" />
      </el-col>
    </el-row>
    <el-divider />
    <el-table :data="lessons" style="width: 100%">
      <el-table-column prop="name" label="Tên bài học" />
      <el-table-column prop="status" label="Trạng thái" />
      <el-table-column prop="score" label="Điểm số" />
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from "vue";

const completedLessons = ref(8);
const progress = ref(80);
const lessons = ref([
  { name: "Toán học", status: "Hoàn thành", score: 9 },
  { name: "Vật lý", status: "Đang học", score: null },
  { name: "Tiếng Anh", status: "Hoàn thành", score: 8 },
  { name: "Lịch sử", status: "Chưa học", score: null },
]);
</script>

<style scoped>
.dashboard-card {
  max-width: 700px;
  margin: 40px auto;
  padding: 24px;
}
</style>
