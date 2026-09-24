import { NavLink } from 'react-router-dom'

const linkClass = ({ isActive }) =>
  `mono-tag text-sm tracking-wide px-3 py-1.5 transition-colors ${
    isActive ? 'text-amber border-b-2 border-amber' : 'text-paper-300 hover:text-paper-100 border-b-2 border-transparent'
  }`

export default function Nav() {
  return (
    <header className="border-b border-ink-600">
      <div className="max-w-5xl mx-auto flex items-center justify-between px-6 py-4">
        <NavLink to="/" className="flex items-center gap-2 no-underline">
          <span className="w-2.5 h-2.5 bg-amber inline-block" style={{ borderRadius: '1px' }} />
          <span className="font-display text-lg font-semibold text-paper-100">DesignLoop</span>
        </NavLink>
        <nav className="flex gap-1">
          <NavLink to="/" end className={linkClass}>Problems</NavLink>
          <NavLink to="/history" className={linkClass}>History</NavLink>
        </nav>
      </div>
    </header>
  )
}
