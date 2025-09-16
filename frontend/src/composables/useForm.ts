import { ref } from 'vue';

export function useForm(initialValues: any) {
    const values = ref({ ...initialValues });
    const errors = ref({});

    function validate() {
        // Validate form
    }

    function reset() {
        values.value = { ...initialValues };
        errors.value = {};
    }

    function submit() {
        // Submit form
    }

    return { values, errors, validate, reset, submit };
}
