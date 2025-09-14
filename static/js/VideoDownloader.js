const VideoDownloader = () => {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [videoInfo, setVideoInfo] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!url.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('url', url);

            const response = await fetch('/download_youtube', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to fetch video information');
            }

            const data = await response.json();
            setVideoInfo({ ...data, url });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="glass-card p-6">
                <h3 className="text-xl font-semibold mb-4">Video Downloader</h3>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <input
                            type="url"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="Enter video URL..."
                            className="input-modern w-full"
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className={`btn-primary w-full ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {loading ? 'Loading...' : 'Fetch Video'}
                    </button>
                </form>

                {error && (
                    <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-lg">
                        {error}
                    </div>
                )}

                {videoInfo && (
                    <div className="mt-6">
                        <YouTubePreview videoInfo={videoInfo} />
                    </div>
                )}
            </div>
        </div>
    );
};