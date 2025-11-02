import { useState } from 'react';
import { Link } from 'react-router-dom';
import { voteForHaiku } from '../api/client';

function HaikuCard({ haiku, onVoteSuccess }) {
  const [isVoting, setIsVoting] = useState(false);
  const [voteCount, setVoteCount] = useState(haiku.vote_count);
  const [hasVoted, setHasVoted] = useState(false);

  const handleVote = async () => {
    const username = prompt('Enter your username to vote:');
    if (!username) return;

    setIsVoting(true);
    try {
      const result = await voteForHaiku(haiku.id, username);
      setVoteCount(result.vote_count);
      setHasVoted(true);
      if (onVoteSuccess) {
        onVoteSuccess();
      }
    } catch (error) {
      if (error.response?.status === 400) {
        alert('You have already voted for this haiku!');
      } else {
        alert('Failed to vote. Please try again.');
      }
    } finally {
      setIsVoting(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Split haiku into lines
  const lines = haiku.full_text.split(' / ');

  return (
    <div className="haiku-card">
      <div className="mb-4">
        <div className="haiku-text space-y-2">
          {lines.map((line, index) => (
            <div key={index} className="text-center">
              {line}
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
        <div className="flex items-center space-x-4">
          <span className="flex items-center">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {formatDate(haiku.generated_at)}
          </span>
          <Link
            to={`/user/${haiku.triggered_by}`}
            className="flex items-center hover:text-haiku-600"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            {haiku.triggered_by}
          </Link>
        </div>
        <span className="text-gray-500">
          {haiku.server} / {haiku.channel}
        </span>
      </div>

      <div className="flex items-center justify-between pt-4 border-t">
        <div className="flex items-center space-x-2">
          <button
            onClick={handleVote}
            disabled={isVoting || hasVoted}
            className={`flex items-center space-x-1 px-3 py-1 rounded-md transition-colors ${
              hasVoted
                ? 'bg-green-100 text-green-700 cursor-not-allowed'
                : 'bg-haiku-100 hover:bg-haiku-200 text-haiku-700'
            }`}
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
            </svg>
            <span>{voteCount}</span>
          </button>
          <span className="text-xs text-gray-500">ID: {haiku.id}</span>
        </div>

        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <span title="5 syllables">5</span>
          <span>/</span>
          <span title="7 syllables">7</span>
          <span>/</span>
          <span title="5 syllables">5</span>
        </div>
      </div>
    </div>
  );
}

export default HaikuCard;

