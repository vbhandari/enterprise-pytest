import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Shell({ onLogout }: { onLogout: () => void }) {
  return (
    <div className="min-h-screen">
      <Sidebar onLogout={onLogout} />
      <main className="ml-56 min-h-screen">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
