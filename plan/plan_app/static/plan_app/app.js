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
  });
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

if ('serviceWorker' in navigator && document.body.dataset.serviceWorker) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register(document.body.dataset.serviceWorker).catch(() => {});
  });
}
