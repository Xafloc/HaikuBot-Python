import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchHaikus } from '../api/client';
import HaikuCard from '../components/HaikuCard';

function Browse() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({
    server: '',
    channel: '',
    username: '',
  });
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data: haikus, isLoading } = useQuery({
    queryKey: ['haikus', { ...filters, skip: page * limit, limit }],
    queryFn: () =>
      fetchHaikus({
        ...filters,
        skip: page * limit,
        limit,
      }),
  });

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0); // Reset to first page on filter change
  };

  const clearFilters = () => {
    setFilters({ server: '', channel: '', username: '' });
    setPage(0);
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-4xl font-bold text-gray-800 mb-8">Browse Haikus</h1>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Server
            </label>
            <input
              type="text"
              value={filters.server}
              onChange={(e) => handleFilterChange('server', e.target.value)}
              placeholder="e.g., libera"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-haiku-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Channel
            </label>
            <input
              type="text"
              value={filters.channel}
              onChange={(e) => handleFilterChange('channel', e.target.value)}
              placeholder="e.g., #haiku"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-haiku-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              value={filters.username}
              onChange={(e) => handleFilterChange('username', e.target.value)}
              placeholder="e.g., Alice"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-haiku-500"
            />
          </div>
        </div>
        {(filters.server || filters.channel || filters.username) && (
          <button
            onClick={clearFilters}
            className="mt-4 text-sm text-haiku-600 hover:text-haiku-700"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Results */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-haiku-600"></div>
          <p className="mt-4 text-gray-600">Loading haikus...</p>
        </div>
      ) : haikus && haikus.length > 0 ? (
        <>
          <div className="space-y-6 mb-8">
            {haikus.map((haiku) => (
              <HaikuCard
                key={haiku.id}
                haiku={haiku}
                onVoteSuccess={() => queryClient.invalidateQueries(['haikus'])}
              />
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="flex items-center text-gray-600">
              Page {page + 1}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!haikus || haikus.length < limit}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </>
      ) : (
        <div className="haiku-card text-center text-gray-500">
          <p>No haikus found with these filters</p>
          <button onClick={clearFilters} className="mt-4 btn-primary">
            Clear Filters
          </button>
        </div>
      )}
    </div>
  );
}

export default Browse;

