import React, { useEffect, useRef } from 'react';

const Console = ({ logs }) => {
    const consoleRef = useRef(null);

    useEffect(() => {
        if (consoleRef.current) {
            consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="console-container" style={{
            backgroundColor: '#1e1e1e',
            color: '#00ff00',
            fontFamily: 'monospace',
            padding: '16px',
            borderRadius: '8px',
            height: '300px',
            overflowY: 'auto',
            marginTop: '20px',
            border: '1px solid #333',
            boxShadow: 'inset 0 0 10px rgba(0,0,0,0.5)'
        }}>
            <div style={{ marginBottom: '8px', borderBottom: '1px solid #333', paddingBottom: '4px', color: '#888' }}>
                &gt;_ Live Analysis Log
            </div>
            <div ref={consoleRef}>
                {logs.map((log, index) => (
                    <div key={index} style={{ marginBottom: '4px', wordBreak: 'break-all' }}>
                        <span style={{ color: '#555', marginRight: '8px' }}>[{new Date().toLocaleTimeString()}]</span>
                        {log}
                    </div>
                ))}
                {logs.length === 0 && (
                    <div style={{ color: '#555', fontStyle: 'italic' }}>Waiting for logs...</div>
                )}
            </div>
        </div>
    );
};

export default Console;
