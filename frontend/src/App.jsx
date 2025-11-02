import { Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import Home from './pages/Home'
import Browse from './pages/Browse'
import BrowseLines from './pages/BrowseLines'
import Statistics from './pages/Statistics'
import UserProfile from './pages/UserProfile'
import Admin from './pages/Admin'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-haiku-50 to-blue-50">
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/browse" element={<Browse />} />
          <Route path="/lines" element={<BrowseLines />} />
          <Route path="/stats" element={<Statistics />} />
          <Route path="/user/:username" element={<UserProfile />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
      <footer className="mt-16 py-8 bg-gray-800 text-white">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm">
            HaikuBot v2.0 - Generating poetry from IRC conversations
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Built with Python, FastAPI, React, and TailwindCSS
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App

