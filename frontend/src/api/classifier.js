import axios from 'axios'

/**
 * Sends image to Django backend for CNN classification.
 * @param {File} file
 * @returns {Promise<string>} predicted class label
 */
export async function predictImage(file) {
  const formData = new FormData()
  formData.append('filePath', file)

  // CSRF token from Django cookie
  const csrfToken = getCsrfToken()
  if (csrfToken) {
    formData.append('csrfmiddlewaretoken', csrfToken)
  }

  const response = await axios.post('/predictImage', formData, {
    headers: {
      'X-CSRFToken': csrfToken ?? '',
      'Content-Type': 'multipart/form-data',
    },
  })

  // Django returns JSON with prediction
  return response.data.prediction
}

function getCsrfToken() {
  const name = 'csrftoken'
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split('=')
    if (key === name) return decodeURIComponent(value)
  }
  return null
}
