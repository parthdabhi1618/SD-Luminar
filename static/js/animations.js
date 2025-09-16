// animations.js

function initializeAnimations() {
    // Add smooth reveal animations to elements
    const animateElements = document.querySelectorAll('.animate-on-scroll');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-reveal');
            }
        });
    }, { threshold: 0.1 });

    animateElements.forEach(el => observer.observe(el));

    // Add loading state animations
    function addLoadingState(element) {
        element.classList.add('loading-shimmer');
        element.setAttribute('data-original-content', element.innerHTML);
        element.innerHTML = `
            <div class="skeleton-loader">
                <div class="skeleton-line"></div>
                <div class="skeleton-line"></div>
            </div>
        `;
    }

    function removeLoadingState(element) {
        element.classList.remove('loading-shimmer');
        element.innerHTML = element.getAttribute('data-original-content');
    }

    // Add smooth transitions for modal dialogs
    const modalBackdrops = document.querySelectorAll('.modal-backdrop');
    modalBackdrops.forEach(backdrop => {
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                backdrop.classList.add('fade-out');
                setTimeout(() => {
                    backdrop.style.display = 'none';
                    backdrop.classList.remove('fade-out');
                }, 300);
            }
        });
    });

    // Add button click animations
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;

            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });

    return {
        addLoadingState,
        removeLoadingState
    };
}

// Initialize animations when the document is ready
document.addEventListener('DOMContentLoaded', initializeAnimations);