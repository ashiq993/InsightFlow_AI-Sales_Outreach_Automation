import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, FileText, X, CheckCircle, AlertCircle, Loader2, Download } from 'lucide-react';
import Console from './Console';

const FileUploader = () => {
    const [file, setFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, analyzing, success, error
    const [analysisResult, setAnalysisResult] = useState(null);
    const [logs, setLogs] = useState([]);
    const [progress, setProgress] = useState(0);
    const fileInputRef = useRef(null);
    const wsRef = useRef(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            validateAndSetFile(e.dataTransfer.files[0]);
        }
    };

    const handleFileSelect = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            validateAndSetFile(e.target.files[0]);
        }
    };

    const validateAndSetFile = (selectedFile) => {
        const validTypes = ['.csv', '.xlsx', '.xls'];
        const fileExtension = '.' + selectedFile.name.split('.').pop().toLowerCase();

        if (validTypes.includes(fileExtension)) {
            setFile(selectedFile);
            setUploadStatus('idle');
            setAnalysisResult(null);
            setLogs([]);
            setProgress(0);
        } else {
            alert('Please upload a valid CSV or Excel file.');
        }
    };

    const removeFile = (e) => {
        e.stopPropagation();
        setFile(null);
        setUploadStatus('idle');
        setAnalysisResult(null);
        setLogs([]);
        setProgress(0);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const startAnalysis = async () => {
        if (!file) return;

        setUploadStatus('uploading');
        setLogs(['Initializing upload...']);
        setProgress(5);

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Step 1: Upload file
            const apiUrl = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;
            const response = await fetch(`${apiUrl}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const data = await response.json();
            const fileId = data.file_id;

            setLogs(prev => [...prev, 'Upload successful. Connecting to analysis stream...']);
            setProgress(10);
            setUploadStatus('analyzing');

            // Step 2: Connect to WebSocket
            connectWebSocket(fileId);

        } catch (error) {
            console.error('Error:', error);
            setUploadStatus('error');
            setLogs(prev => [...prev, `Error: ${error.message}`]);
        }
    };

    const connectWebSocket = (fileId) => {
        const apiUrl = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = apiUrl.replace(/^https?:\/\//, '');
        const wsUrl = `${wsProtocol}//${wsHost}/ws/analyze/${fileId}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setLogs(prev => [...prev, 'Connected to analysis server.']);
        };

        ws.onmessage = (event) => {
            const message = event.data;

            try {
                // Check if it's a JSON message (final result)
                if (message.startsWith('{') && message.includes('COMPLETED')) {
                    const result = JSON.parse(message);
                    if (result.type === 'COMPLETED') {
                        setAnalysisResult(result);
                        setUploadStatus('success');
                        setProgress(100);
                        setLogs(prev => [...prev, 'Analysis completed successfully!']);
                        ws.close();
                    }
                } else {
                    // Regular log message
                    setLogs(prev => [...prev, message]);

                    // Simple progress estimation based on keywords
                    if (message.includes('Loaded')) setProgress(20);
                    if (message.includes('Initializing')) setProgress(30);
                    if (message.includes('Fetching')) setProgress(40);
                    if (message.includes('Processing')) setProgress(60);
                    if (message.includes('Generating')) setProgress(80);
                    if (message.includes('Uploading')) setProgress(90);
                }
            } catch (e) {
                // If parse fails, treat as text
                setLogs(prev => [...prev, message]);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setLogs(prev => [...prev, 'Connection error occurred.']);
            setUploadStatus('error');
        };

        ws.onclose = () => {
            if (uploadStatus !== 'success') {
                setLogs(prev => [...prev, 'Connection closed.']);
            }
        };
    };

    // Cleanup WebSocket on unmount
    useEffect(() => {
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    return (
        <div className="uploader-container">
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`drop-zone ${isDragging ? 'dragging' : ''}`}
                onClick={() => !file && fileInputRef.current?.click()}
                style={{ cursor: file ? 'default' : 'pointer' }}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept=".csv,.xlsx,.xls"
                    style={{ display: 'none' }}
                    onChange={handleFileSelect}
                />

                {!file ? (
                    <>
                        <div style={{ marginBottom: '16px' }}>
                            <UploadCloud className="upload-icon" size={48} color="var(--accent-primary)" />
                        </div>
                        <h3 style={{ fontSize: '1.1rem', marginBottom: '8px' }}>
                            Drag & drop your file here
                        </h3>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '24px' }}>
                            or click to browse from your computer
                        </p>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                            {['CSV', 'XLSX', 'XLS'].map(type => (
                                <span key={type} style={{
                                    padding: '4px 8px',
                                    backgroundColor: 'var(--bg-secondary)',
                                    borderRadius: '4px',
                                    fontSize: '0.75rem',
                                    color: 'var(--text-secondary)',
                                    border: '1px solid var(--border-color)'
                                }}>
                                    {type}
                                </span>
                            ))}
                        </div>
                    </>
                ) : (
                    <div className="file-info" onClick={(e) => e.stopPropagation()}>
                        <div className="file-details">
                            <div style={{ padding: '10px', backgroundColor: 'var(--success-bg)', borderRadius: '8px' }}>
                                <FileText size={24} color="var(--success-text)" />
                            </div>
                            <div style={{ textAlign: 'left' }}>
                                <p style={{ margin: 0, fontWeight: 500 }}>{file.name}</p>
                                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{(file.size / 1024).toFixed(2)} KB</p>
                            </div>
                        </div>
                        {uploadStatus === 'idle' && (
                            <button onClick={removeFile} className="btn-remove">
                                <X size={20} />
                            </button>
                        )}
                    </div>
                )}
            </div>

            {file && uploadStatus === 'idle' && (
                <button
                    onClick={startAnalysis}
                    className="btn-primary"
                >
                    Start AI Analysis
                </button>
            )}

            {(uploadStatus === 'uploading' || uploadStatus === 'analyzing') && (
                <div style={{ marginTop: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                        <span>Processing...</span>
                        <span>{progress}%</span>
                    </div>
                    <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ width: `${progress}%`, height: '100%', backgroundColor: 'var(--accent-primary)', transition: 'width 0.3s ease' }}></div>
                    </div>

                    <Console logs={logs} />
                </div>
            )}

            {uploadStatus === 'success' && analysisResult && (
                <div className="success-message">
                    <div style={{ display: 'inline-flex', padding: '12px', backgroundColor: 'var(--success-bg)', borderRadius: '50%', marginBottom: '16px' }}>
                        <CheckCircle size={32} color="var(--success-text)" />
                    </div>
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', color: 'var(--text-primary)' }}>Analysis Complete!</h3>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
                        Your file has been processed and uploaded to Google Drive.
                    </p>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'center' }}>
                        {analysisResult.drive_link && (
                            <a
                                href={analysisResult.drive_link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn-primary"
                                style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '8px', justifyContent: 'center' }}
                            >
                                <Download size={18} />
                                View Processed File
                            </a>
                        )}
                    </div>

                    <div style={{ marginTop: '20px', textAlign: 'left' }}>
                        <div style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '8px', color: 'var(--text-secondary)' }}>Execution Log:</div>
                        <div style={{ maxHeight: '150px', overflowY: 'auto', backgroundColor: 'var(--bg-secondary)', padding: '10px', borderRadius: '8px', fontSize: '0.8rem', color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }}>
                            {logs.map((log, i) => (
                                <div key={i}>{log}</div>
                            ))}
                        </div>
                    </div>

                    <button
                        onClick={removeFile}
                        style={{ marginTop: '20px', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', textDecoration: 'underline' }}
                    >
                        Analyze Another File
                    </button>
                </div>
            )}

            {uploadStatus === 'error' && (
                <div className="error-message">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '8px' }}>
                        <AlertCircle size={20} />
                        <span>An error occurred</span>
                    </div>
                    <p style={{ fontSize: '0.9rem' }}>Check the logs below for details.</p>
                    <Console logs={logs} />
                    <button
                        onClick={() => setUploadStatus('idle')}
                        style={{ marginTop: '10px', background: 'none', border: '1px solid currentColor', padding: '4px 12px', borderRadius: '4px', color: 'inherit', cursor: 'pointer' }}
                    >
                        Try Again
                    </button>
                </div>
            )}
        </div>
    );
};

export default FileUploader;
