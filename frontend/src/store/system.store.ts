import { defineStore } from 'pinia';

export const useSystemStore = defineStore('system', {
    state: () => ({
        config: {}
    }),
    actions: {
        fetchConfig() { }
    }
});
