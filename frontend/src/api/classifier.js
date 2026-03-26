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
    },
  })

  // Django returns HTML — parse prediction from it
  const html = response.data
  const match = html.match(/The classification is\s*:\s*([^<]+)</)
  if (match) return match[1].trim()

  throw new Error('Could not parse prediction from response')
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
