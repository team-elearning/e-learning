import { ref } from 'vue';

export function usePagination() {
    const currentPage = ref(1);
    const pageSize = ref(10);
    const totalItems = ref(0);

    function setPage(page: number) {
        currentPage.value = page;
    }

    return { currentPage, pageSize, totalItems, setPage };
}
