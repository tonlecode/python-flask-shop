/* ===== ShopKH Main JavaScript ===== */

// Navbar scroll effect
window.addEventListener('scroll', function () {
    const nav = document.getElementById('mainNav');
    if (!nav) return;
    if (window.scrollY > 50) {
        nav.style.background = 'rgba(15, 23, 42, 0.98)';
        nav.style.backdropFilter = 'blur(10px)';
    } else {
        nav.style.background = '#1e293b';
        nav.style.backdropFilter = 'none';
    }
});

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

// Toggle password visibility
function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

// Product grid/list view toggle
document.addEventListener('DOMContentLoaded', function () {
    const gridBtn = document.getElementById('gridView');
    const listBtn = document.getElementById('listView');
    const grid = document.getElementById('productGrid');
    if (!gridBtn || !grid) return;

    gridBtn.addEventListener('click', function () {
        grid.querySelectorAll('.product-col').forEach(col => {
            col.className = 'col-xl-4 col-md-6 product-col';
        });
        gridBtn.classList.add('btn-secondary');
        gridBtn.classList.remove('btn-outline-secondary');
        listBtn.classList.add('btn-outline-secondary');
        listBtn.classList.remove('btn-secondary');
    });

    listBtn.addEventListener('click', function () {
        grid.querySelectorAll('.product-col').forEach(col => {
            col.className = 'col-12 product-col';
        });
        listBtn.classList.add('btn-secondary');
        listBtn.classList.remove('btn-outline-secondary');
        gridBtn.classList.add('btn-outline-secondary');
        gridBtn.classList.remove('btn-secondary');
    });
});

// Add to cart animation
document.querySelectorAll('form[action*="cart/add"]').forEach(form => {
    form.addEventListener('submit', function (e) {
        const btn = form.querySelector('button[type="submit"]');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-check me-1"></i>Added!';
            btn.classList.add('btn-success');
            btn.classList.remove('btn-primary');
        }
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function (e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Product image lazy loading fallback
document.querySelectorAll('img[loading="lazy"]').forEach(img => {
    img.addEventListener('error', function () {
        this.src = 'https://via.placeholder.com/400x300/e2e8f0/64748b?text=No+Image';
    });
});

// Form validation feedback
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function (e) {
        const requiredFields = form.querySelectorAll('[required]');
        let valid = true;
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                valid = false;
            } else {
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
            }
        });
        if (!valid) e.preventDefault();
    });
});

// Counter animation for hero stats
function animateCounter(el, target) {
    let current = 0;
    const increment = Math.ceil(target / 60);
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) { current = target; clearInterval(timer); }
        el.textContent = current + '+';
    }, 25);
}

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const el = entry.target;
            const val = parseInt(el.textContent.replace('+', ''));
            if (!isNaN(val) && val > 0) animateCounter(el, val);
            observer.unobserve(el);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-number').forEach(el => observer.observe(el));

// Back to top button
const backToTop = document.createElement('button');
backToTop.id = 'backToTop';
backToTop.innerHTML = '<i class="fas fa-chevron-up"></i>';
backToTop.style.cssText = `
    position: fixed; bottom: 30px; right: 30px; z-index: 9999;
    background: #2563eb; color: white; border: none; border-radius: 50%;
    width: 44px; height: 44px; font-size: 1rem; cursor: pointer;
    box-shadow: 0 4px 15px rgba(37,99,235,0.4); display: none;
    transition: all 0.3s ease; align-items: center; justify-content: center;
`;
document.body.appendChild(backToTop);

window.addEventListener('scroll', () => {
    backToTop.style.display = window.scrollY > 400 ? 'flex' : 'none';
});
backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
backToTop.addEventListener('mouseenter', () => backToTop.style.transform = 'translateY(-3px)');
backToTop.addEventListener('mouseleave', () => backToTop.style.transform = 'translateY(0)');
