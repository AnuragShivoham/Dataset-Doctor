import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('Dataset Doctor landing experience', () => {
  it('renders the landing headline and upload guidance', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: /dataset doctor/i })).toBeInTheDocument()
    expect(screen.getByText(/upload a csv or xlsx file/i)).toBeInTheDocument()
  })
})
