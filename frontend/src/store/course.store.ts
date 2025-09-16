import { defineStore } from 'pinia';

export const useCourseStore = defineStore('course', {
    state: () => ({
        courses: []
    }),
    actions: {
        fetchCourses() { }
    }
});
