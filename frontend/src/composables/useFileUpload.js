import { ref } from 'vue'

/**
 * Reusable composable for file selection with preview.
 */
export function useFileUpload() {
  const selectedFile = ref(null)
  const previewUrl   = ref(null)
  const fileName     = ref('')
  const isDragging   = ref(false)

  function applyFile(file) {
    if (!file?.type.startsWith('image/')) return
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    selectedFile.value = file
    fileName.value     = file.name
    previewUrl.value   = URL.createObjectURL(file)
  }

  function clearFile() {
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    selectedFile.value = null
    previewUrl.value   = null
    fileName.value     = ''
  }

  return {
    selectedFile,
    previewUrl,
    fileName,
    isDragging,
    applyFile,
    clearFile,
  }
}
