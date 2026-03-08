import { useCallback, useEffect, useState } from 'react'

export function useAuth() {
  const [token, setTokenState] = useState<string | null>(() =>
    localStorage.getItem('admin_token'),
  )

  const setToken = useCallback((t: string | null) => {
    if (t) {
      localStorage.setItem('admin_token', t)
    } else {
      localStorage.removeItem('admin_token')
    }
    setTokenState(t)
  }, [])

  return { token, setToken, isAuthenticated: !!token }
}

export function useFetch<T>(fetcher: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(() => {
    setLoading(true)
    setError(null)
    fetcher()
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => { refetch() }, [refetch])

  return { data, loading, error, refetch }
}
