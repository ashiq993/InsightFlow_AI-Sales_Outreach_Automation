import React from 'react';
import { Sparkles } from 'lucide-react';

const Header = ({ children }) => {
    return (
        <header className="header">
            <div className="header-content">
                <div className="logo" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles className="logo-icon" size={24} />
                    <span>InsightFlow AI</span>
                </div>
                <nav style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem' }}>
                        Documentation
                    </a>
                    {children}
                </nav>
            </div>
        </header>
    );
};

export default Header;
