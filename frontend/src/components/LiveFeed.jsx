import { useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import HaikuCard from './HaikuCard';

// Default to 60 minutes - will be configurable via backend in the future
const LIVE_FEED_DURATION_MINUTES = 60;

function LiveFeed({ onNewHaiku }) {
  const { isConnected, recentItems, clearOldItems } = useWebSocket();

  // Call onNewHaiku callback when a new haiku arrives
  useEffect(() => {
    const latestItem = recentItems[0];
    if (latestItem && latestItem.type === 'new_haiku' && onNewHaiku) {
      onNewHaiku(latestItem.data);
    }
  }, [recentItems, onNewHaiku]);

  // Periodically clean up old items
  useEffect(() => {
    const interval = setInterval(() => {
      clearOldItems(LIVE_FEED_DURATION_MINUTES);
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [clearOldItems]);

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatRelativeTime = (timestamp) => {
    const now = new Date().getTime();
    const diffMs = now - timestamp;
    const diffMinutes = Math.floor(diffMs / 60000);

    if (diffMinutes < 1) return 'just now';
    if (diffMinutes === 1) return '1 minute ago';
    if (diffMinutes < 60) return `${diffMinutes} minutes ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours === 1) return '1 hour ago';
    return `${diffHours} hours ago`;
  };

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-800">
          Live Feed
          {recentItems.length > 0 && (
            <span className="text-sm font-normal text-gray-600 ml-2">
              (last {LIVE_FEED_DURATION_MINUTES} minutes)
            </span>
          )}
        </h2>
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

      {recentItems.length === 0 ? (
        <div className="haiku-card text-center text-gray-500">
          <p>Waiting for new activity...</p>
          <p className="text-sm mt-2">
            New haikus and collected lines will appear here in real-time
          </p>
        </div>
      ) : (
        <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
          {recentItems.map((item, index) => (
            <div key={`${item.type}-${item.receivedAt}-${index}`} className="animate-fadeIn">
              {item.type === 'new_haiku' ? (
                <>
                  <div className="mb-2 text-sm font-semibold text-haiku-600 flex items-center justify-between">
                    <span>🆕 New Haiku Generated!</span>
                    <span className="text-xs text-gray-500 font-normal">
                      {formatRelativeTime(item.receivedAt)}
                    </span>
                  </div>
                  <HaikuCard haiku={item.data} />
                </>
              ) : (
                <div className="haiku-card bg-gradient-to-r from-green-50 to-blue-50 border-l-4 border-haiku-500">
                  <div className="flex items-start justify-between mb-2">
                    <div className="text-sm font-semibold text-haiku-700">
                      ✨ New Line Collected!
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">
                        {formatRelativeTime(item.receivedAt)}
                      </span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        item.data.syllable_count === 5
                          ? 'bg-green-100 text-green-800'
                          : 'bg-purple-100 text-purple-800'
                      }`}>
                        {item.data.syllable_count} syllables
                      </span>
                    </div>
                  </div>
                  <div className="text-lg font-serif text-gray-800 mb-3">
                    "{item.data.text}"
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">{item.data.username}</span>
                      <span>•</span>
                      <span className="font-mono">{item.data.channel}</span>
                      <span>•</span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        item.data.source === 'auto'
                          ? 'bg-gray-100 text-gray-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {item.data.source === 'auto' ? 'auto-collected' : 'manually added'}
                      </span>
                    </div>
                    <div>{formatTimestamp(item.data.timestamp)}</div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default LiveFeed;

