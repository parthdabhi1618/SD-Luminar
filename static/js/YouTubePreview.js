const YouTubePreview = ({ videoInfo, onDownload }) => {
    const [downloading, setDownloading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);

    const formatDuration = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    const handleDownload = async () => {
        try {
            setDownloading(true);
            setError(null);
            // Try YouTube, then X/Twitter, fallback to error
            let response = await fetch(`/download_youtube?url=${encodeURIComponent(videoInfo.url)}&download_id=${videoInfo.download_id}`);
            if (!response.ok) {
                response = await fetch(`/download_twitter?url=${encodeURIComponent(videoInfo.url)}&download_id=${videoInfo.download_id}`);
                if (!response.ok) {
                    const errorText = await response.text();
                    if (errorText.includes('Sign in to confirm you’re not a bot')) {
                        setError('YouTube requires authentication for this video. Please follow the instructions to export your cookies and upload them. See https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp');
                    } else {
                        setError('Download failed. Try again or check the video URL.');
                    }
                    setDownloading(false);
                    return;
                }
            }
            // Check for missing output file
            const contentType = response.headers.get('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                if (data.missingOutput) {
                    showMissingFileError('The output file is missing or was cleaned up. Please re-upload and try again.');
                    setDownloading(false);
                    return;
                }
            }
            const reader = response.body.getReader();
            const contentLengthHeader = response.headers.get('Content-Length');
            const contentLength = contentLengthHeader ? +contentLengthHeader : null;
            let receivedLength = 0;
            if (!contentLength) {
                let fake = 10;
                const fakeInterval = setInterval(() => {
                    fake = Math.min(90, fake + Math.random() * 15);
                    setProgress(Math.round(fake));
                }, 600);
                while(true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                }
                clearInterval(fakeInterval);
                setProgress(100);
            } else {
                while(true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    receivedLength += value.length;
                    setProgress(Math.round((receivedLength / contentLength) * 100));
                }
            }
            setDownloading(false);
            setProgress(0);
        } catch (err) {
            setError('Download failed. Try again or check the video URL.');
            setDownloading(false);
        }
    };

    // Show download button for all supported platforms
    return (
        <div className="video-preview-container animate-scale-in">
            <div className="video-preview">
                {videoInfo.thumbnail && (
                    <img 
                        src={videoInfo.thumbnail} 
                        alt={videoInfo.title}
                        className="w-full h-full object-contain"
                    />
                )}
                <div className="video-preview-overlay">
                    <div className="video-info">
                        <h3 className="font-semibold mb-2">{videoInfo.title}</h3>
                        {videoInfo.length && <p className="text-sm opacity-80">Duration: {formatDuration(videoInfo.length)}</p>}
                        {videoInfo.author && <p className="text-sm opacity-80">By: {videoInfo.author}</p>}
                        {error && (
                            <div className="text-red-500 text-sm mt-2">
                                {error}
                            </div>
                        )}
                        <button
                            onClick={handleDownload}
                            disabled={downloading}
                            className={`mt-4 px-4 py-2 rounded-lg bg-accent-green text-black font-semibold
                                ${downloading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-opacity-90'}`}
                        >
                            {downloading ? 'Downloading...' : 'Download'}
                        </button>
                    </div>
                </div>
                {downloading && (
                    <div className="download-progress">
                        <div 
                            className="download-progress-bar"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                )}
            </div>
        </div>
    );
};