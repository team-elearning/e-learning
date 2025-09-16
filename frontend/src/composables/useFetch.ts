import { ref } from 'vue';

export function useFetch() {
    const data = ref(null);
    const loading = ref(false);
    const error = ref(null);

    async function get(url: string) {
        loading.value = true;
        // Call GET API
        loading.value = false;
    }

    async function post(url: string, payload: any) {
        loading.value = true;
        // Call POST API
        loading.value = false;
    }

    return { data, loading, error, get, post };
}
