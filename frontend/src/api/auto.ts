import request from './request';

export interface LoginResponse {
    username: string;
    role: string;
    token: string;
    expire: string;
}

export interface ReloginResponse {
    token: string;
    expire: string;
}

export const authApi = {
    /** POST /v1/auth/login */
    login: (data: { username: string; password: string }) => {
        return request.post<any, LoginResponse>('/v1/auth/login', data);
    },

    /** GET /v1/auth/logout */
    logout: () => {
        return request.get('/v1/auth/logout');
    },

    /** GET /v1/auth/ask-code?email=xxx&type=register|reset */
    askCode: (email: string, type: 'register' | 'reset') => {
        return request.get('/v1/auth/ask-code', { params: { email, type } });
    },

    /** POST /v1/auth/register */
    register: (data: { email: string; code: string; username: string; password: string }) => {
        return request.post('/v1/auth/register', data);
    },

    /** POST /v1/auth/reset */
    reset: (data: { email: string; code: string; password: string }) => {
        return request.post('/v1/auth/reset', data);
    },

    /** GET /v1/auth/relogin */
    relogin: () => {
        return request.get<any, ReloginResponse>('/v1/auth/relogin');
    },
};

export const uploadApi = {
    /** POST /v1/upload/file  multipart/form-data */
    uploadFile: (file: File, type: string) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', type);
        return request.post<any, any>('/v1/upload/file', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
};