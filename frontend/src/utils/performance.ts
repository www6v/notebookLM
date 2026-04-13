import { onCLS, onINP, onLCP, type Metric } from 'web-vitals'

function reportMetric(metric: Metric) {
  const payload = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,
    delta: metric.delta,
    id: metric.id,
    page: window.location.pathname,
  })
  const endpoint = import.meta.env.VITE_WEB_VITALS_ENDPOINT

  if (import.meta.env.DEV) {
    console.info('[web-vitals]', JSON.parse(payload))
  }

  if (!endpoint) {
    return
  }

  if (navigator.sendBeacon) {
    navigator.sendBeacon(
      endpoint,
      new Blob([payload], { type: 'application/json' })
    )
    return
  }

  void fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: payload,
    keepalive: true,
  })
}

export function initWebVitals() {
  if (typeof window === 'undefined') {
    return
  }

  onCLS(reportMetric)
  onINP(reportMetric)
  onLCP(reportMetric)
}
