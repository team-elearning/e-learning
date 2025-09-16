import { ref } from 'vue';

export function useAuth() {
    const user = ref(null);
    const isAuthenticated = ref(false);

    function login(credentials: any) {
        // Call login API
    }

    function logout() {
        // Call logout API
    }

    function fetchUserInfo() {
        // Fetch user info
    }

    return { user, isAuthenticated, login, logout, fetchUserInfo };
}
