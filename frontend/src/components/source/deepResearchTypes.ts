/** apiStatus mirrors backend `status` when the card is shown (ready | error). */
export interface DeepResearchReport {
  id: string
  query: string
  sourceCount: number
  popularCount: number
  content?: string
  apiStatus: 'ready' | 'error'
  errorMessage?: string
}
