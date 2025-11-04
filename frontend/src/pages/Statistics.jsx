import { useQuery } from '@tanstack/react-query';
import { fetchStats, fetchLeaderboard } from '../api/client';
import { Link } from 'react-router-dom';

function Statistics() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
  });

  const { data: leaderboard, isLoading: leaderboardLoading } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: () => fetchLeaderboard(10),
  });

  const formatNumber = (num) => {
    return num?.toLocaleString() || '0';
  };

  const getDynamicFontSize = (num) => {
    if (!num) return 'text-4xl';

    const digits = num.toString().length;

    if (digits <= 6) return 'text-4xl';      // Up to 999,999
    if (digits <= 9) return 'text-3xl';      // Up to 999,999,999
    if (digits <= 12) return 'text-2xl';     // Up to 999,999,999,999
    if (digits <= 15) return 'text-xl';      // Up to quadrillions
    if (digits <= 18) return 'text-lg';      // Up to quintillions
    return 'text-base';                      // Anything larger
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-4xl font-bold text-gray-800 mb-8">Statistics</h1>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {statsLoading ? (
          <div className="col-span-full text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-haiku-600"></div>
          </div>
        ) : stats ? (
          <>
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-lg p-6 text-white">
              <div className="text-4xl font-bold mb-2">
                {formatNumber(stats.lines_5_syllable)}
              </div>
              <div className="text-blue-100">5-Syllable Lines</div>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg p-6 text-white">
              <div className="text-4xl font-bold mb-2">
                {formatNumber(stats.lines_7_syllable)}
              </div>
              <div className="text-purple-100">7-Syllable Lines</div>
            </div>

            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-lg p-6 text-white">
              <div className="text-4xl font-bold mb-2">
                {formatNumber(stats.generated_haikus)}
              </div>
              <div className="text-green-100">Generated Haikus</div>
            </div>

            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-lg p-6 text-white">
              <div className={`font-bold mb-2 ${getDynamicFontSize(stats.possible_permutations)}`}>
                {formatNumber(stats.possible_permutations)}
              </div>
              <div className="text-orange-100">Possible Combinations</div>
            </div>
          </>
        ) : null}
      </div>

      {/* Detailed Stats */}
      {stats && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-12">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Line Distribution
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="text-sm text-gray-600 mb-1">Position 1 (5-syl)</div>
              <div className="text-2xl font-bold text-haiku-600">
                {formatNumber(stats.lines_position_1)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Any or First placement
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Position 2 (7-syl)</div>
              <div className="text-2xl font-bold text-haiku-600">
                {formatNumber(stats.lines_position_2)}
              </div>
              <div className="text-xs text-gray-500 mt-1">All 7-syllable lines</div>
            </div>
            <div>
              <div className="text-sm text-gray-600 mb-1">Position 3 (5-syl)</div>
              <div className="text-2xl font-bold text-haiku-600">
                {formatNumber(stats.lines_position_3)}
              </div>
              <div className="text-xs text-gray-500 mt-1">Any or Last placement</div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-md">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              How it works:
            </h3>
            <p className="text-sm text-gray-600">
              HaikuBot uses smart placement logic. 5-syllable lines can be marked for
              specific positions (first or last), while 7-syllable lines always go in
              the middle. This creates better narrative flow in generated haikus.
            </p>
          </div>
        </div>
      )}

      {/* Leaderboard */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">
          Top Contributors
        </h2>

        {leaderboardLoading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-haiku-600"></div>
          </div>
        ) : leaderboard && leaderboard.length > 0 ? (
          <div className="space-y-3">
            {leaderboard.map((user, index) => (
              <Link
                key={user.username}
                to={`/user/${user.username}`}
                className="flex items-center justify-between p-4 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                      index === 0
                        ? 'bg-yellow-400 text-yellow-900'
                        : index === 1
                        ? 'bg-gray-300 text-gray-700'
                        : index === 2
                        ? 'bg-orange-400 text-orange-900'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-800">
                      {user.username}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-haiku-600">
                    {formatNumber(user.lines_contributed)}
                  </div>
                  <div className="text-xs text-gray-500">lines contributed</div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-8">
            No contributions yet
          </div>
        )}
      </div>
    </div>
  );
}

export default Statistics;

