import axios from 'axios'

/**
 * Anonymous share viewers: no JWT. Do not trigger global 401 logout on failure.
 */
const shareClient = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

shareClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
)

export default shareClient
