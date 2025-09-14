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
            
            // Start download process
            const response = await fetch(`/download_youtube?url=${encodeURIComponent(videoInfo.url)}&download_id=${videoInfo.download_id}`);
            if (!response.ok) throw new Error('Download failed');
            
            const reader = response.body.getReader();
            const contentLength = +response.headers.get('Content-Length');
            let receivedLength = 0;

            while(true) {
                const {done, value} = await reader.read();
                if (done) break;
                
                receivedLength += value.length;
                setProgress((receivedLength / contentLength) * 100);
            }

            setDownloading(false);
            setProgress(0);
        } catch (err) {
            setError(err.message);
            setDownloading(false);
        }
    };

    return (
        <div className="video-preview-container animate-scale-in">
            <div className="video-preview">
                <img 
                    src={videoInfo.thumbnail} 
                    alt={videoInfo.title}
                    className="w-full h-full object-contain"
                />
                <div className="video-preview-overlay">
                    <div className="video-info">
                        <h3 className="font-semibold mb-2">{videoInfo.title}</h3>
                        <p className="text-sm opacity-80">Duration: {formatDuration(videoInfo.length)}</p>
                        <p className="text-sm opacity-80">By: {videoInfo.author}</p>
                        
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