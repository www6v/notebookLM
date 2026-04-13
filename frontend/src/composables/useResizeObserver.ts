import { onBeforeUnmount, onMounted, ref } from 'vue'

export function useResizeObserver<T extends HTMLElement>() {
  const elementRef = ref<T | null>(null)
  const width = ref(0)
  const height = ref(0)
  let observer: ResizeObserver | null = null

  onMounted(() => {
    if (!elementRef.value) {
      return
    }

    observer = new ResizeObserver((entries) => {
      const entry = entries[0]
      width.value = entry.contentRect.width
      height.value = entry.contentRect.height
    })

    observer.observe(elementRef.value)
  })

  onBeforeUnmount(() => {
    observer?.disconnect()
  })

  return {
    elementRef,
    width,
    height,
  }
}
