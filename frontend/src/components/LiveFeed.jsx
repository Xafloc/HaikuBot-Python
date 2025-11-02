import { useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import HaikuCard from './HaikuCard';

function LiveFeed({ onNewHaiku }) {
  const { isConnected, newHaiku, newLine, clearNewHaiku, clearNewLine } = useWebSocket();

  useEffect(() => {
    if (newHaiku) {
      if (onNewHaiku) {
        onNewHaiku(newHaiku);
      }
      // Clear after a delay
      const timeout = setTimeout(() => {
        clearNewHaiku();
      }, 10000); // Clear after 10 seconds
      return () => clearTimeout(timeout);
    }
  }, [newHaiku, onNewHaiku, clearNewHaiku]);

  useEffect(() => {
    if (newLine) {
      // Clear after a delay
      const timeout = setTimeout(() => {
        clearNewLine();
      }, 8000); // Clear after 8 seconds
      return () => clearTimeout(timeout);
    }
  }, [newLine, clearNewLine]);

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Live Feed</h2>
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
            }`}
          />
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {newHaiku ? (
        <div className="animate-fadeIn">
          <div className="mb-2 text-sm font-semibold text-haiku-600">
            🆕 New Haiku Generated!
          </div>
          <HaikuCard haiku={newHaiku} />
        </div>
      ) : newLine ? (
        <div className="animate-fadeIn">
          <div className="haiku-card bg-gradient-to-r from-green-50 to-blue-50 border-l-4 border-haiku-500">
            <div className="flex items-start justify-between mb-2">
              <div className="text-sm font-semibold text-haiku-700">
                ✨ New Line Collected!
              </div>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                newLine.syllable_count === 5
                  ? 'bg-green-100 text-green-800'
                  : 'bg-purple-100 text-purple-800'
              }`}>
                {newLine.syllable_count} syllables
              </span>
            </div>
            <div className="text-lg font-serif text-gray-800 mb-3">
              "{newLine.text}"
            </div>
            <div className="flex items-center justify-between text-xs text-gray-600">
              <div className="flex items-center space-x-2">
                <span className="font-medium">{newLine.username}</span>
                <span>•</span>
                <span className="font-mono">{newLine.channel}</span>
                <span>•</span>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  newLine.source === 'auto'
                    ? 'bg-gray-100 text-gray-700'
                    : 'bg-blue-100 text-blue-700'
                }`}>
                  {newLine.source === 'auto' ? 'auto-collected' : 'manually added'}
                </span>
              </div>
              <div>{formatTimestamp(newLine.timestamp)}</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="haiku-card text-center text-gray-500">
          <p>Waiting for new activity...</p>
          <p className="text-sm mt-2">
            New haikus and collected lines will appear here in real-time
          </p>
        </div>
      )}
    </div>
  );
}

export default LiveFeed;

