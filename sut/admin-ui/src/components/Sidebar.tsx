import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Package, ShoppingCart, Tag, LogOut } from 'lucide-react'

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/orders', label: 'Orders', icon: ShoppingCart },
  { to: '/products', label: 'Products', icon: Package },
  { to: '/coupons', label: 'Coupons', icon: Tag },
]

export default function Sidebar({ onLogout }: { onLogout: () => void }) {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-56 flex-col border-r border-stone-200 bg-white">
      <div className="flex h-14 items-center gap-2 border-b border-stone-200 px-5">
        <span className="text-lg">📦</span>
        <span className="text-sm font-semibold tracking-tight text-stone-800">
          Order Admin
        </span>
      </div>

      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium transition-colors ${
                isActive
                  ? 'bg-stone-100 text-stone-900'
                  : 'text-stone-500 hover:bg-stone-50 hover:text-stone-700'
              }`
            }
          >
            <Icon size={16} strokeWidth={1.8} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-stone-200 p-3">
        <button
          onClick={onLogout}
          data-testid="logout-btn"
          className="flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium text-stone-500 transition-colors hover:bg-red-50 hover:text-red-600"
        >
          <LogOut size={16} strokeWidth={1.8} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
