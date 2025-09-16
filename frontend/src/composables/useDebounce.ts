import { ref } from 'vue';

export function useDebounce() {
    const value = ref('');
    let timeout: any;

    function debounceInput(newValue: string, delay = 300) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            value.value = newValue;
        }, delay);
    }

    return { value, debounceInput };
}
