import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchLines } from '../api/client';

function BrowseLines() {
  const [filters, setFilters] = useState({
    syllable_count: '',
    username: '',
  });
  const [page, setPage] = useState(0);
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');
  const limit = 50;

  const { data: rawLines, isLoading } = useQuery({
    queryKey: ['lines', { ...filters, skip: page * limit, limit }],
    queryFn: () =>
      fetchLines({
        ...filters,
        syllable_count: filters.syllable_count ? parseInt(filters.syllable_count) : undefined,
        skip: page * limit,
        limit,
      }),
  });

  // Client-side sorting
  const lines = rawLines ? [...rawLines].sort((a, b) => {
    let aVal = a[sortBy];
    let bVal = b[sortBy];

    // Handle different data types
    if (sortBy === 'timestamp') {
      aVal = new Date(aVal).getTime();
      bVal = new Date(bVal).getTime();
    } else if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }

    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    } else {
      return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
    }
  }) : [];

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0); // Reset to first page on filter change
  };

  const clearFilters = () => {
    setFilters({ syllable_count: '', username: '' });
    setPage(0);
  };

  const handleSort = (column) => {
    if (sortBy === column) {
      // Toggle sort order if clicking the same column
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new column and default to descending
      setSortBy(column);
      setSortOrder('desc');
    }
    setPage(0); // Reset to first page
  };

  const SortIcon = ({ column }) => {
    if (sortBy !== column) {
      return <span className="ml-1 text-gray-400">⇅</span>;
    }
    return sortOrder === 'asc' ? (
      <span className="ml-1">↑</span>
    ) : (
      <span className="ml-1">↓</span>
    );
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">Browse Lines</h1>
        <p className="text-gray-600">
          Explore all collected 5 and 7 syllable phrases from IRC conversations
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Syllable Count
            </label>
            <select
              value={filters.syllable_count}
              onChange={(e) => handleFilterChange('syllable_count', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-haiku-500"
            >
              <option value="">All (5 and 7)</option>
              <option value="5">5 syllables</option>
              <option value="7">7 syllables</option>
            </select>
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
        {(filters.syllable_count || filters.username) && (
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
          <p className="mt-4 text-gray-600">Loading lines...</p>
        </div>
      ) : lines && lines.length > 0 ? (
        <>
          {/* Stats Summary */}
          <div className="bg-gradient-to-r from-haiku-50 to-blue-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-600">
              Showing {lines.length} line{lines.length !== 1 ? 's' : ''}
              {filters.syllable_count && ` with ${filters.syllable_count} syllables`}
              {filters.username && ` by ${filters.username}`}
            </p>
          </div>

          {/* Lines Table */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      onClick={() => handleSort('id')}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    >
                      ID <SortIcon column="id" />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Text
                    </th>
                    <th
                      onClick={() => handleSort('syllable_count')}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    >
                      Syllables <SortIcon column="syllable_count" />
                    </th>
                    <th
                      onClick={() => handleSort('username')}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    >
                      User <SortIcon column="username" />
                    </th>
                    <th
                      onClick={() => handleSort('channel')}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    >
                      Channel <SortIcon column="channel" />
                    </th>
                    <th
                      onClick={() => handleSort('source')}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    >
                      Source <SortIcon column="source" />
                    </th>
                    <th
                      onClick={() => handleSort('timestamp')}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                    >
                      Date <SortIcon column="timestamp" />
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {lines.map((line) => (
                    <tr key={line.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                        {line.id}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="font-medium">{line.text}</div>
                        {line.placement && line.placement !== 'any' && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mt-1">
                            Position: {line.placement}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          line.syllable_count === 5
                            ? 'bg-green-100 text-green-800'
                            : 'bg-purple-100 text-purple-800'
                        }`}>
                          {line.syllable_count}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <a
                          href={`/user/${line.username}`}
                          className="text-haiku-600 hover:text-haiku-700 hover:underline"
                        >
                          {line.username}
                        </a>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span className="font-mono text-xs">{line.channel}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          line.source === 'auto'
                            ? 'bg-gray-100 text-gray-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {line.source}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(line.timestamp)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
              disabled={!lines || lines.length < limit}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </>
      ) : (
        <div className="haiku-card text-center text-gray-500">
          <p>No lines found with these filters</p>
          {(filters.syllable_count || filters.username) && (
            <button onClick={clearFilters} className="mt-4 btn-primary">
              Clear Filters
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default BrowseLines;
