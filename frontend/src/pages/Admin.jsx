import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = '/api';

function Admin() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState(localStorage.getItem('adminToken') || '');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [activeTab, setActiveTab] = useState('lines');
  const [loginError, setLoginError] = useState('');

  const queryClient = useQueryClient();

  // Check if already authenticated on mount
  useEffect(() => {
    if (token) {
      setIsAuthenticated(true);
    }
  }, [token]);

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials) => {
      const response = await fetch(`${API_BASE}/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      return response.json();
    },
    onSuccess: (data) => {
      setToken(data.token);
      localStorage.setItem('adminToken', data.token);
      setIsAuthenticated(true);
      setLoginError('');
    },
    onError: (error) => {
      setLoginError(error.message);
    },
  });

  const handleLogin = (e) => {
    e.preventDefault();
    loginMutation.mutate({ username, password });
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('adminToken');
    setIsAuthenticated(false);
    setUsername('');
    setPassword('');
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto mt-20">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-6 text-center">
            Admin Login
          </h1>

          <form onSubmit={handleLogin}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-haiku-500"
                required
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-haiku-500"
                required
              />
            </div>

            {loginError && (
              <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
                {loginError}
              </div>
            )}

            <button
              type="submit"
              className="w-full btn-primary"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? 'Logging in...' : 'Login'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold text-gray-800">Admin Panel</h1>
        <button onClick={handleLogout} className="btn-secondary">
          Logout
        </button>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('lines')}
              className={`${
                activeTab === 'lines'
                  ? 'border-haiku-500 text-haiku-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Manage Lines
            </button>
            <button
              onClick={() => setActiveTab('haikus')}
              className={`${
                activeTab === 'haikus'
                  ? 'border-haiku-500 text-haiku-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Manage Haikus
            </button>
            <button
              onClick={() => setActiveTab('syllable-check')}
              className={`${
                activeTab === 'syllable-check'
                  ? 'border-haiku-500 text-haiku-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Syllable Validation
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'lines' && <ManageLines token={token} />}
      {activeTab === 'haikus' && <ManageHaikus token={token} />}
      {activeTab === 'syllable-check' && <SyllableCheck token={token} />}
    </div>
  );
}

function ManageLines({ token }) {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const queryClient = useQueryClient();

  const { data: lines, isLoading } = useQuery({
    queryKey: ['admin-lines', startDate, endDate],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('limit', '100');

      const response = await fetch(`${API_BASE}/admin/lines?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to fetch lines');
      return response.json();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async ({ lineId, cascade = false }) => {
      const url = cascade
        ? `${API_BASE}/admin/lines/${lineId}?cascade=true`
        : `${API_BASE}/admin/lines/${lineId}`;

      const response = await fetch(url, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        if (response.status === 409) {
          // Line is used in haikus
          const errorData = await response.json();
          throw { status: 409, data: errorData.detail };
        }
        throw new Error('Failed to delete line');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-lines']);
    },
    onError: (error, variables) => {
      if (error.status === 409) {
        // Show dialog asking if user wants to cascade delete
        const haikuCount = error.data.haiku_count;
        const lineText = error.data.line_text;
        if (
          confirm(
            `This line is used in ${haikuCount} haiku(s):\n\n"${lineText}"\n\nDo you want to delete the line AND all ${haikuCount} haiku(s) that use it?`
          )
        ) {
          // Retry with cascade=true
          deleteMutation.mutate({ lineId: variables.lineId, cascade: true });
        }
      } else {
        alert('Error deleting line: ' + error.message);
      }
    },
  });

  return (
    <div>
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Filter Lines</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <p>Loading lines...</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Text
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Syllables
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {lines?.map((line) => (
                <tr key={line.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {line.id}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{line.text}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {line.syllable_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {line.username}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(line.timestamp).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => {
                        if (confirm(`Delete line: "${line.text}"?`)) {
                          deleteMutation.mutate({ lineId: line.id });
                        }
                      }}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ManageHaikus({ token }) {
  const [page, setPage] = useState(0);
  const limit = 20;
  const queryClient = useQueryClient();

  const { data: haikus, isLoading } = useQuery({
    queryKey: ['admin-haikus', page],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE}/haikus?skip=${page * limit}&limit=${limit}`
      );

      if (!response.ok) throw new Error('Failed to fetch haikus');
      return response.json();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (haikuId) => {
      const response = await fetch(`${API_BASE}/admin/haikus/${haikuId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to delete haiku');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-haikus']);
    },
  });

  return (
    <div>
      {isLoading ? (
        <div className="text-center py-12">
          <p>Loading haikus...</p>
        </div>
      ) : (
        <>
          <div className="space-y-6 mb-8">
            {haikus?.map((haiku) => (
              <div key={haiku.id} className="haiku-card">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="haiku-text mb-4">
                      {haiku.full_text.split(' / ').map((line, i) => (
                        <div key={i}>{line}</div>
                      ))}
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Haiku #{haiku.id}</span>
                      <span>
                        {new Date(haiku.generated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm('Delete this haiku?')) {
                        deleteMutation.mutate(haiku.id);
                      }
                    }}
                    className="ml-4 text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

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
      )}
    </div>
  );
}

function SyllableCheck({ token }) {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [method, setMethod] = useState('perl');
  const [includeValidated, setIncludeValidated] = useState(false);
  const [results, setResults] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  const queryClient = useQueryClient();

  const handleCheck = async () => {
    setIsChecking(true);
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('method', method);
      params.append('include_validated', includeValidated);

      const response = await fetch(
        `${API_BASE}/admin/syllable-check?${params}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) throw new Error('Failed to check syllables');
      const data = await response.json();
      setResults(data);
    } catch (error) {
      alert('Error checking syllables: ' + error.message);
    } finally {
      setIsChecking(false);
    }
  };

  const deleteMutation = useMutation({
    mutationFn: async (lineId) => {
      const response = await fetch(`${API_BASE}/admin/lines/${lineId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to delete line');
      return response.json();
    },
    onSuccess: () => {
      // Remove from results
      setResults((prev) => prev.filter((r) => r.id !== deleteMutation.variables));
    },
  });

  const validateMutation = useMutation({
    mutationFn: async (lineId) => {
      const response = await fetch(`${API_BASE}/admin/lines/${lineId}/validate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to validate line');
      return response.json();
    },
    onSuccess: (data, lineId) => {
      // Remove from results since it's now validated
      setResults((prev) => prev.filter((r) => r.id !== lineId));
    },
  });

  return (
    <div>
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Syllable Validation</h2>
        <p className="text-sm text-gray-600 mb-4">
          Check lines for incorrect syllable counts using the latest syllable
          counter algorithm.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Counting Method
            </label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="perl">Perl (78% accuracy - most accurate)</option>
              <option value="python">Python (64% accuracy - fallback)</option>
            </select>
          </div>
        </div>

        <div className="mb-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={includeValidated}
              onChange={(e) => setIncludeValidated(e.target.checked)}
              className="mr-2 h-4 w-4 text-haiku-600 focus:ring-haiku-500 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-700">
              Include human-validated lines (lines you've already marked as correct)
            </span>
          </label>
        </div>

        <button
          onClick={handleCheck}
          className="btn-primary"
          disabled={isChecking}
        >
          {isChecking ? 'Checking...' : 'Run Syllable Check'}
        </button>
      </div>

      {results && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-2">
              Found {results.length} line(s) with incorrect syllable counts
            </h3>
            {results.length > 0 && (
              <p className="text-sm text-gray-600 mb-2">
                Using method: <span className="font-medium">{results[0].method}</span>
              </p>
            )}
            {results.length === 0 && (
              <p className="text-gray-600">
                All lines in the date range have correct syllable counts!
              </p>
            )}
          </div>

          {results.length > 0 && (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Text
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Stored
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actual
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.map((result) => (
                  <tr key={result.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {result.id}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {result.text}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {result.stored_syllables}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {result.actual_syllables}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {result.username}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-4">
                      <button
                        onClick={() => {
                          validateMutation.mutate(result.id);
                        }}
                        className="text-green-600 hover:text-green-900"
                        title="Mark this line as correct (human validation)"
                      >
                        Mark as Correct
                      </button>
                      <button
                        onClick={() => {
                          if (
                            confirm(
                              `Delete line (${result.stored_syllables} → ${result.actual_syllables} syllables): "${result.text}"?`
                            )
                          ) {
                            deleteMutation.mutate({ lineId: result.id });
                          }
                        }}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

export default Admin;
