'use client';
import { useState } from 'react';

export default function Home() {
  const [urls, setUrls] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e:any) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/submit-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          urls: urls.includes('\n') ? urls.split('\n').filter(Boolean) : urls
        })
      });

      const data = await response.json();
      setResults(data.results);
    } catch (error) {
      console.error('Error:', error);
      setResults({ error: 'Something went wrong' });
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Webcrawler UI</h1>
      <form onSubmit={handleSubmit}>
        <textarea
          rows={10}
          style={{ width: '100%' }}
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          placeholder="Enter one or more URLs, each on a new line"
        />
        <br />
        <button type="submit" disabled={loading}>
          {loading ? 'Crawling...' : 'Submit'}
        </button>
      </form>

      {results && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Results:</h2>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
