import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchHaikus, generateHaiku } from '../api/client';
import HaikuCard from '../components/HaikuCard';
import LiveFeed from '../components/LiveFeed';

function Home() {
  const queryClient = useQueryClient();
  const [isGenerating, setIsGenerating] = useState(false);

  // Fetch recent haikus
  const { data: haikus, isLoading } = useQuery({
    queryKey: ['haikus', { limit: 10 }],
    queryFn: () => fetchHaikus({ limit: 10 }),
  });

  // Generate haiku mutation
  const generateMutation = useMutation({
    mutationFn: generateHaiku,
    onSuccess: () => {
      queryClient.invalidateQueries(['haikus']);
    },
  });

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await generateMutation.mutateAsync({});
    } catch (error) {
      alert('Failed to generate haiku. Make sure there are enough lines in the database.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleNewHaiku = () => {
    queryClient.invalidateQueries(['haikus']);
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-gray-800 mb-4">
          Welcome to HaikuBot
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Discover beautiful haiku generated from real IRC conversations
        </p>
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="btn-primary text-lg px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? 'Generating...' : '✨ Generate New Haiku'}
        </button>
      </div>

      {/* Live Feed */}
      <LiveFeed onNewHaiku={handleNewHaiku} />

      {/* Recent Haikus */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Recent Haikus</h2>
        
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-haiku-600"></div>
            <p className="mt-4 text-gray-600">Loading haikus...</p>
          </div>
        ) : haikus && haikus.length > 0 ? (
          <div className="space-y-6">
            {haikus.map((haiku) => (
              <HaikuCard
                key={haiku.id}
                haiku={haiku}
                onVoteSuccess={() => queryClient.invalidateQueries(['haikus'])}
              />
            ))}
          </div>
        ) : (
          <div className="haiku-card text-center text-gray-500">
            <p>No haikus yet!</p>
            <p className="text-sm mt-2">
              Generate the first one or wait for IRC activity
            </p>
          </div>
        )}
      </div>

      {/* Info Section */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-3xl mb-2">🎭</div>
          <h3 className="text-lg font-semibold mb-2">Auto-Collection</h3>
          <p className="text-sm text-gray-600">
            The bot monitors IRC conversations and automatically collects 5 and 7 syllable phrases
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-3xl mb-2">🎲</div>
          <h3 className="text-lg font-semibold mb-2">Smart Generation</h3>
          <p className="text-sm text-gray-600">
            Haikus are randomly generated using placement logic for better narrative flow
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-3xl mb-2">👥</div>
          <h3 className="text-lg font-semibold mb-2">Community Driven</h3>
          <p className="text-sm text-gray-600">
            Vote for your favorites and see which haikus resonate with the community
          </p>
        </div>
      </div>
    </div>
  );
}

export default Home;

