import { ref } from 'vue';

export function useDarkMode() {
    const isDark = ref(false);

    function toggleDark() {
        isDark.value = !isDark.value;
    }

    return { isDark, toggleDark };
}
