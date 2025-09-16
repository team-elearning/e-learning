// Hàm format dữ liệu
export function formatDate(date: Date): string {
    return date.toLocaleDateString('vi-VN');
}

export function formatCurrency(amount: number): string {
    return amount.toLocaleString('vi-VN', { style: 'currency', currency: 'VND' });
}
