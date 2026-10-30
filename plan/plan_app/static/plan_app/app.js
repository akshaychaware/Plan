const root = document.documentElement;
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const animates = !reducedMotion && 'IntersectionObserver' in window;

const onVisible = (elements, callback, threshold = 0.4) => {
  if (!elements.length || !animates) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      callback(entry.target);
    });
  }, { threshold });
  elements.forEach((element) => observer.observe(element));
};

document.querySelector('[data-theme-toggle]')?.addEventListener('click', (event) => {
  const button = event.currentTarget;
  const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
  const apply = () => {
    root.dataset.theme = next;
  };
  button.classList.remove('is-switching');
  void button.offsetWidth;
  button.classList.add('is-switching');
  if (document.startViewTransition && !reducedMotion) {
    const rect = button.getBoundingClientRect();
    root.style.setProperty('--reveal-x', `${rect.left + rect.width / 2}px`);
    root.style.setProperty('--reveal-y', `${rect.top + rect.height / 2}px`);
    root.classList.add('theme-reveal');
    document.startViewTransition(apply).finished.finally(() => root.classList.remove('theme-reveal'));
  } else {
    apply();
  }
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
  let remaining = 5000;
  let started = 0;
  let timer = 0;
  const run = () => {
    started = Date.now();
    timer = setTimeout(() => dismiss(alert), remaining);
  };
  alert.addEventListener('pointerenter', () => {
    clearTimeout(timer);
    remaining -= Date.now() - started;
  });
  alert.addEventListener('pointerleave', run);
  run();
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

document.querySelectorAll('form[data-guard]').forEach((form) => {
  const snapshot = () => new URLSearchParams(new FormData(form)).toString();
  const initial = snapshot();
  let submitting = false;
  form.addEventListener('submit', () => {
    submitting = true;
  });
  window.addEventListener('beforeunload', (event) => {
    if (submitting || snapshot() === initial) return;
    event.preventDefault();
    event.returnValue = '';
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
    else if (target >= 100) ring.classList.add('is-complete');
  };
  requestAnimationFrame(step);
};

const countUp = (element) => {
  const text = element.textContent;
  const match = text.match(/\d+(?:\.\d+)?/);
  const target = match ? Number(match[0]) : 0;
  if (!target) return;
  const decimals = (match[0].split('.')[1] || '').length;
  const before = text.slice(0, match.index);
  const after = text.slice(match.index + match[0].length);
  const render = (value) => {
    element.textContent = before + value.toFixed(decimals) + after;
  };
  render(0);
  onVisible([element], () => {
    const start = performance.now();
    const step = (now) => {
      const t = Math.min((now - start) / 900, 1);
      if (t < 1) {
        render(target * (1 - (1 - t) ** 3));
        requestAnimationFrame(step);
      } else {
        element.textContent = text;
      }
    };
    requestAnimationFrame(step);
  });
};
if (animates) document.querySelectorAll('.stat-value').forEach(countUp);

const dogCards = document.querySelectorAll('.dog-card');
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
if (animates) {
  rings.forEach((ring) => {
    ring.style.setProperty('--value', 0);
    ring.querySelector('span').textContent = '0%';
  });
  onVisible(rings, animateRing);
}

const svgNS = 'http://www.w3.org/2000/svg';
const svgElement = (name, attributes) => {
  const element = document.createElementNS(svgNS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
};
const drawSparkline = (svg) => {
  const rows = [...svg.closest('.card').querySelectorAll('[data-weight]')].reverse();
  const values = rows.map((row) => Number(row.dataset.weight));
  const width = svg.clientWidth;
  const height = svg.clientHeight;
  if (values.length < 2 || values.some(Number.isNaN) || !width) return;
  const pad = 10;
  const min = Math.min(...values);
  const span = Math.max(...values) - min;
  const points = values.map((value, index) => [
    pad + (index * (width - 2 * pad)) / (values.length - 1),
    span ? height - pad - ((value - min) * (height - 2 * pad)) / span : height / 2,
  ]);
  const line = points.map((point) => point.join(',')).join(' ');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.replaceChildren(
    svgElement('polygon', { class: 'sparkline-area', points: `${pad},${height} ${line} ${width - pad},${height}` }),
    svgElement('polyline', { class: 'sparkline-line', points: line, pathLength: 1 }),
    ...points.map(([x, y], index) => {
      const dot = svgElement('circle', { cx: x, cy: y, r: 4 });
      const title = svgElement('title', {});
      title.textContent = `${rows[index].dataset.date} · ${values[index]} kg`;
      dot.append(title);
      return dot;
    }),
  );
};
document.querySelectorAll('[data-sparkline]').forEach((svg) => {
  drawSparkline(svg);
  if ('ResizeObserver' in window) {
    let width = svg.clientWidth;
    new ResizeObserver(() => {
      if (svg.clientWidth === width) return;
      width = svg.clientWidth;
      drawSparkline(svg);
    }).observe(svg);
  }
});

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
