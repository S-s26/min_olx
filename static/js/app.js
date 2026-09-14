/**
 * Mini-oLx — global UI helpers
 *
 * - Toast auto-hide
 * - Live search submit on Enter (already handled by form)
 */

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.molx-toast.is-visible').forEach((t) => {
        setTimeout(() => {
            t.style.opacity = '0';
            t.style.transform = 'translateY(20px)';
            setTimeout(() => t.remove(), 250);
        }, 3500);
    });
});