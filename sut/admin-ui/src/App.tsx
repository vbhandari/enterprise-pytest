import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './hooks'
import Shell from './components/Shell'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Orders from './pages/Orders'
import Products from './pages/Products'
import Coupons from './pages/Coupons'

export default function App() {
  const { isAuthenticated, setToken } = useAuth()

  if (!isAuthenticated) {
    return <Login onLogin={setToken} />
  }

  return (
    <Routes>
      <Route
        element={<Shell onLogout={() => setToken(null)} />}
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/products" element={<Products />} />
        <Route path="/coupons" element={<Coupons />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  )
}
