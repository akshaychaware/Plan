const root = document.documentElement;

document.querySelector('[data-theme-toggle]')?.addEventListener('click', () => {
  const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
  root.dataset.theme = next;
  try {
    localStorage.setItem('theme', next);
  } catch {}
});

document.addEventListener('pointerdown', (event) => {
  const button = event.target.closest('.btn');
  if (!button) return;
  const rect = button.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  const ripple = document.createElement('span');
  ripple.className = 'ripple';
  ripple.style.width = ripple.style.height = `${size}px`;
  ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
  ripple.style.top = `${event.clientY - rect.top - size / 2}px`;
  button.append(ripple);
  ripple.addEventListener('animationend', () => ripple.remove());
});

const dismiss = (alert) => {
  alert.classList.add('is-leaving');
  alert.addEventListener('animationend', () => alert.remove(), { once: true });
};
document.querySelectorAll('.alert').forEach((alert) => {
  alert.querySelector('button')?.addEventListener('click', () => dismiss(alert));
  setTimeout(() => dismiss(alert), 5000);
});

document.querySelectorAll('form[method="post"]').forEach((form) => {
  form.addEventListener('submit', () => {
    form.querySelector('button:not([type="button"])')?.classList.add('is-loading');
    if (form.querySelector('.btn-success')) navigator.vibrate?.(15);
  });
});

const centerInRow = (row, item) => {
  if (!row || !item || row.scrollWidth <= row.clientWidth) return;
  const offset = item.getBoundingClientRect().left - row.getBoundingClientRect().left;
  row.scrollLeft += offset - (row.clientWidth - item.clientWidth) / 2;
};
centerInRow(document.querySelector('.week'), document.querySelector('.week .is-today'));
document.querySelectorAll('.chips, .segmented').forEach((row) => {
  centerInRow(row, row.querySelector('[aria-current="true"]'));
});

const initMetricScope = (scope) => {
  const exercise = scope.querySelector('select[name$="exercise_type"]');
  const metrics = scope.querySelectorAll(
    'input[name$="duration_minutes"], input[name$="distance_km"], input[name$="repetitions"]'
  );
  if (!exercise || !metrics.length) return;

  const update = () => {
    const skipped = scope.querySelector('input[name$="status"]:checked')?.value === 'SKIPPED';
    const disabled = Boolean(exercise.selectedOptions[0]?.hasAttribute('data-no-metrics')) || skipped;
    metrics.forEach((input) => {
      if (disabled && !input.disabled) {
        input.dataset.previous = input.value;
        input.value = '';
      } else if (!disabled && input.disabled) {
        input.value = input.dataset.previous ?? '';
      }
      input.disabled = disabled;
    });
  };

  scope.addEventListener('change', update);
  update();
};

document.querySelectorAll('[data-duration-scope]').forEach(initMetricScope);

document.querySelectorAll('[data-add-activity]').forEach((button) => {
  const prefix = button.dataset.addActivity;
  const total = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
  const template = document.getElementById(`${prefix}-template`);
  const list = document.getElementById(`${prefix}-forms`);
  button.addEventListener('click', () => {
    const index = Number(total.value);
    list.insertAdjacentHTML('beforeend', template.innerHTML.replaceAll('__prefix__', String(index)));
    total.value = index + 1;
    const row = list.lastElementChild;
    initMetricScope(row);
    row.querySelector('select')?.focus();
  });
});

const animateRing = (ring) => {
  const target = Number(ring.dataset.progress) || 0;
  const label = ring.querySelector('span');
  const start = performance.now();
  const step = (now) => {
    const t = Math.min((now - start) / 1200, 1);
    const value = target * (1 - (1 - t) ** 3);
    ring.style.setProperty('--value', value);
    label.textContent = `${Math.round(value)}%`;
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
};

const dogCards = document.querySelectorAll('.dog-card');
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const setGlare = (card, event) => {
  const rect = card.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width;
  const y = (event.clientY - rect.top) / rect.height;
  card.style.setProperty('--mx', `${x * 100}%`);
  card.style.setProperty('--my', `${y * 100}%`);
  return { x, y };
};

if (dogCards.length && !reducedMotion && matchMedia('(hover: hover) and (pointer: fine)').matches) {
  dogCards.forEach((card) => {
    card.addEventListener('pointermove', (event) => {
      const { x, y } = setGlare(card, event);
      card.style.setProperty('--rx', `${(0.5 - y) * 8}deg`);
      card.style.setProperty('--ry', `${(x - 0.5) * 10}deg`);
    });
    card.addEventListener('pointerleave', () => {
      ['--mx', '--my', '--rx', '--ry'].forEach((name) => card.style.removeProperty(name));
    });
  });
} else if (dogCards.length && !reducedMotion && 'IntersectionObserver' in window) {
  const seen = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      seen.unobserve(entry.target);
    });
  }, { threshold: 0.5 });
  dogCards.forEach((card, index) => {
    card.style.setProperty('--i', index);
    seen.observe(card);
    card.addEventListener('pointerdown', (event) => {
      setGlare(card, event);
      card.classList.remove('is-tapped');
      void card.offsetWidth;
      card.classList.add('is-tapped');
    });
    card.addEventListener('animationend', (event) => {
      if (event.animationName === 'dog-sweep') card.classList.remove('is-tapped');
    });
  });
}

const rings = document.querySelectorAll('.ring[data-progress]');
if (rings.length && 'IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      animateRing(entry.target);
    });
  }, { threshold: 0.4 });
  rings.forEach((ring) => {
    ring.style.setProperty('--value', 0);
    ring.querySelector('span').textContent = '0%';
    observer.observe(ring);
  });
}

const reminder = document.querySelector('dialog[data-weigh-in-reminder]');
if (reminder?.showModal) {
  const key = `weigh-in-dismissed-${reminder.dataset.weighInReminder}`;
  let dismissed = false;
  try {
    dismissed = sessionStorage.getItem(key) === '1';
  } catch {}
  if (!dismissed) {
    reminder.addEventListener('close', () => {
      try {
        sessionStorage.setItem(key, '1');
      } catch {}
    });
    reminder.showModal();
  }
}

if ('serviceWorker' in navigator && document.body.dataset.serviceWorker) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register(document.body.dataset.serviceWorker).catch(() => {});
  });
}
