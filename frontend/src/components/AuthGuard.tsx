import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/auto';

const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const navigate = useNavigate();
    const [checked, setChecked] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login', { replace: true });
            return;
        }

        // 尝试用 relogin 刷新 token
        authApi.relogin()
            .then((res) => {
                localStorage.setItem('token', res.token);
                setChecked(true);
            })
            .catch(() => {
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                localStorage.removeItem('role');
                navigate('/login', { replace: true });
            });
    }, [navigate]);

    if (!checked) return null;

    return <>{children}</>;
};

export default AuthGuard;
