import { Link, useLocation } from 'react-router-dom';

function Navigation() {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path
      ? 'bg-haiku-600 text-white'
      : 'text-gray-700 hover:bg-haiku-100';
  };

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl font-bold text-haiku-600">俳句</span>
            <span className="text-xl font-semibold text-gray-800">HaikuBot</span>
          </Link>

          <div className="flex space-x-2">
            <Link
              to="/"
              className={`px-4 py-2 rounded-md font-medium transition-colors ${isActive('/')}`}
            >
              Home
            </Link>
            <Link
              to="/browse"
              className={`px-4 py-2 rounded-md font-medium transition-colors ${isActive('/browse')}`}
            >
              Haikus
            </Link>
            <Link
              to="/lines"
              className={`px-4 py-2 rounded-md font-medium transition-colors ${isActive('/lines')}`}
            >
              Lines
            </Link>
            <Link
              to="/stats"
              className={`px-4 py-2 rounded-md font-medium transition-colors ${isActive('/stats')}`}
            >
              Statistics
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;

