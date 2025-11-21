import React from 'react';
import { FileSpreadsheet, Download } from 'lucide-react';

const DataTemplateGuide = () => {
    return (
        <div className="guide-card">
            <div className="guide-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <FileSpreadsheet size={24} color="#3b82f6" />
                    <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Data Template Guide</h2>
                </div>
                <a href="/Lead_Data_Template.xlsx" download className="btn-download" style={{ textDecoration: 'none' }}>
                    <Download size={16} />
                    Download Template
                </a>
            </div>

            <div className="guide-content">
                <div>
                    <p style={{ color: '#94a3b8', marginBottom: '16px', fontSize: '0.9rem' }}>
                        Ensure your file follows this structure for optimal analysis.
                        Supported formats: <span style={{ color: 'white', fontFamily: 'monospace' }}>.csv, .xlsx, .xls</span>
                    </p>
                    <ul className="guide-list">
                        {[
                            "Full Name",
                            "Email Address",
                            "Company Name",
                            "Job Title",
                            "LinkedIn URL (Optional)"
                        ].map((item, i) => (
                            <li key={i}>
                                <div className="dot" />
                                {item}
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="table-preview">
                    <div className="table-header-dots">
                        <div className="dot-red" />
                        <div className="dot-yellow" />
                        <div className="dot-green" />
                    </div>
                    <div style={{ overflowX: 'auto' }}>
                        <table className="preview-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Email</th>
                                    <th>Company</th>
                                    <th>Role</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>John Doe</td>
                                    <td>john@acme.com</td>
                                    <td>Acme Inc</td>
                                    <td>CEO</td>
                                </tr>
                                <tr>
                                    <td>Jane Smith</td>
                                    <td>jane@tech.io</td>
                                    <td>TechCorp</td>
                                    <td>CTO</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DataTemplateGuide;
