import { Routes, Route } from 'react-router-dom'
import Nav from './components/Nav'
import Home from './pages/Home'
import Workspace from './pages/Workspace'
import History from './pages/History'

export default function App() {
  return (
    <div className="min-h-screen">
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/problem/:slug" element={<Workspace />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </div>
  )
}
