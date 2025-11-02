import { useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchUserStats, fetchUserHaikus, fetchUserLines } from '../api/client';
import HaikuCard from '../components/HaikuCard';

function UserProfile() {
  const { username } = useParams();
  const queryClient = useQueryClient();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['userStats', username],
    queryFn: () => fetchUserStats(username),
  });

  const { data: haikus, isLoading: haikusLoading } = useQuery({
    queryKey: ['userHaikus', username],
    queryFn: () => fetchUserHaikus(username, { limit: 10 }),
  });

  const { data: lines, isLoading: linesLoading } = useQuery({
    queryKey: ['userLines', username],
    queryFn: () => fetchUserLines(username, { limit: 20 }),
  });

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-8">
        <div className="flex items-center space-x-4 mb-4">
          <div className="w-16 h-16 bg-haiku-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            {username.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-800">{username}</h1>
            {stats && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span className="px-2 py-1 bg-haiku-100 text-haiku-700 rounded">
                  {stats.role}
                </span>
              </div>
            )}
          </div>
        </div>

        {statsLoading ? (
          <div className="text-center py-4">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-haiku-600"></div>
          </div>
        ) : stats ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-haiku-600">
                {stats.lines_contributed}
              </div>
              <div className="text-sm text-gray-600">Lines Contributed</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-haiku-600">
                {stats.haikus_generated}
              </div>
              <div className="text-sm text-gray-600">Haikus Generated</div>
            </div>
            <div className="text-center md:col-span-1 col-span-2">
              <div className="text-3xl font-bold text-haiku-600">
                {stats.lines_contributed > 0
                  ? (stats.haikus_generated / stats.lines_contributed).toFixed(2)
                  : '0'}
              </div>
              <div className="text-sm text-gray-600">Haikus per Line</div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Generated Haikus */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Generated Haikus
        </h2>
        {haikusLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-haiku-600"></div>
          </div>
        ) : haikus && haikus.length > 0 ? (
          <div className="space-y-6">
            {haikus.map((haiku) => (
              <HaikuCard
                key={haiku.id}
                haiku={haiku}
                onVoteSuccess={() => queryClient.invalidateQueries(['userHaikus'])}
              />
            ))}
          </div>
        ) : (
          <div className="haiku-card text-center text-gray-500">
            <p>No haikus generated yet</p>
          </div>
        )}
      </div>

      {/* Contributed Lines */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Contributed Lines
        </h2>
        {linesLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-haiku-600"></div>
          </div>
        ) : lines && lines.length > 0 ? (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="space-y-3">
              {lines.map((line) => (
                <div
                  key={line.id}
                  className="flex items-start justify-between p-3 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <div className="font-serif text-lg text-gray-800">
                      {line.text}
                    </div>
                    <div className="flex items-center space-x-3 mt-1 text-xs text-gray-500">
                      <span>{line.server} / {line.channel}</span>
                      <span>•</span>
                      <span>
                        {new Date(line.timestamp).toLocaleDateString()}
                      </span>
                      {line.source === 'manual' && (
                        <>
                          <span>•</span>
                          <span className="text-haiku-600">Manual</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="ml-4">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                        line.syllable_count === 5
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-purple-100 text-purple-700'
                      }`}
                    >
                      {line.syllable_count} syl
                    </span>
                    {line.placement && line.placement !== 'any' && (
                      <span className="ml-2 text-xs text-gray-500">
                        ({line.placement})
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="haiku-card text-center text-gray-500">
            <p>No lines contributed yet</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserProfile;

