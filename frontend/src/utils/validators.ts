// Hàm validate input
export function isEmail(email: string): boolean {
    return /\S+@\S+\.\S+/.test(email);
}

export function isRequired(value: any): boolean {
    return value !== null && value !== undefined && value !== '';
}
