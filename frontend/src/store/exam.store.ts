import { defineStore } from 'pinia';

export const useExamStore = defineStore('exam', {
    state: () => ({
        exams: []
    }),
    actions: {
        fetchExams() { }
    }
});
