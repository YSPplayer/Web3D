import axios from 'axios'
import type {
    AxiosInstance,
    AxiosRequestConfig,
    InternalAxiosRequestConfig
} from 'axios'
import { ElMessage } from 'element-plus'

interface AuthRetryConfig extends InternalAxiosRequestConfig {
    _authRetry?: boolean
}

type AuthFailureHandler = () => void

export class Request {
    private axios: AxiosInstance | null
    private baseURL = ''
    private timeout = 60000
    private accessToken = ''
    private refreshPromise: Promise<any> | null = null
    private authFailureHandler: AuthFailureHandler | null = null
    private authFailureNotified = false
    private authGeneration = 0
    private loggingOut = false

    constructor() {
        this.axios = null
    }

    create(url: string, timeout: number = 60000): void {
        if (this.axios) return
        this.baseURL = url.replace(/\/$/, '')
        this.timeout = timeout
        this.axios = axios.create({
            baseURL: this.baseURL,
            timeout: this.timeout,
            withCredentials: true
        })

        this.axios.interceptors.request.use((config) => {
            if (this.accessToken) {
                config.headers.Authorization = `Bearer ${this.accessToken}`
            }
            return config
        })

        this.axios.interceptors.response.use(
            (response) => response,
            async (error) => {
                const original = error.config as AuthRetryConfig | undefined
                if (
                    error.response?.status !== 401 ||
                    !original ||
                    original._authRetry ||
                    this.isAuthEndpoint(original.url)
                ) {
                    return Promise.reject(error)
                }

                original._authRetry = true
                try {
                    await this.refreshSession()
                    if (!this.axios) return Promise.reject(error)
                    original.headers.Authorization = `Bearer ${this.accessToken}`
                    return this.axios.request(original)
                } catch (refreshError) {
                    this.clearAccessToken()
                    this.notifyAuthFailure()
                    return Promise.reject(refreshError)
                }
            }
        )
    }

    setAccessToken(token: string): void {
        this.accessToken = token
        this.authFailureNotified = false
    }

    getAccessToken(): string {
        return this.accessToken
    }

    clearAccessToken(): void {
        this.accessToken = ''
    }

    setAuthFailureHandler(handler: AuthFailureHandler): void {
        this.authFailureHandler = handler
    }

    beginLogout(): void {
        this.authGeneration += 1
        this.loggingOut = true
    }

    finishLogout(): void {
        this.clearAccessToken()
        this.loggingOut = false
        this.notifyAuthFailure()
    }

    async refreshSession(): Promise<any> {
        if (this.refreshPromise) return this.refreshPromise
        if (this.loggingOut) {
            return Promise.reject(new Error('正在退出登录'))
        }
        if (!this.baseURL) {
            return Promise.reject(new Error('Please call create() first'))
        }

        const refreshGeneration = this.authGeneration

        this.refreshPromise = axios.post(
            `${this.baseURL}/chatai/auth/refresh`,
            {},
            {
                timeout: this.timeout,
                withCredentials: true
            }
        ).then((response) => {
            if (refreshGeneration !== this.authGeneration || this.loggingOut) {
                throw new Error('登录状态已变化，忽略过期的刷新结果')
            }
            const result = response.data
            const token = result?.data?.access_token
            if (!token) throw new Error('刷新接口没有返回 Access Token')
            this.setAccessToken(token)
            return result
        }).finally(() => {
            this.refreshPromise = null
        })

        return this.refreshPromise
    }

    async refreshSessionOrLogout(): Promise<any> {
        try {
            return await this.refreshSession()
        } catch (error) {
            this.clearAccessToken()
            this.notifyAuthFailure()
            throw error
        }
    }

    async get<T = any>(url: string, data: AxiosRequestConfig = {}): Promise<any> {
        if (!this.axios) return Promise.reject(new Error('Please call create() first'))

        try {
            const response = await this.axios.get<T>(url, data)
            return response.data
        } catch (error) {
            return this.handleRequestError(error)
        }
    }

    async put<T = any>(url: string, data: any = {}): Promise<any> {
        if (!this.axios) return Promise.reject(new Error('Please call create() first'))

        try {
            const response = await this.axios.put<T>(url, data)
            return response.data
        } catch (error) {
            return this.handleRequestError(error)
        }
    }

    async delete<T = any>(url: string, data: AxiosRequestConfig = {}): Promise<any> {
        if (!this.axios) return Promise.reject(new Error('Please call create() first'))

        try {
            const response = await this.axios.delete<T>(url, data)
            return response.data
        } catch (error) {
            return this.handleRequestError(error)
        }
    }

    async post<T = any>(url: string, data: any = {}): Promise<any> {
        if (!this.axios) return Promise.reject(new Error('Please call create() first'))

        try {
            const response = await this.axios.post<T>(url, data)
            return response.data
        } catch (error) {
            return this.handleRequestError(error)
        }
    }

    private isAuthEndpoint(url?: string): boolean {
        if (!url) return false
        return url.includes('/chatai/login') ||
            url.includes('/chatai/auth/refresh') ||
            url.includes('/chatai/auth/logout')
    }

    private notifyAuthFailure(): void {
        if (this.authFailureNotified) return
        this.authFailureNotified = true
        this.authFailureHandler?.()
    }

    private handleRequestError(error: unknown): undefined {
        console.log('Backend request error:', error)
        if (axios.isAxiosError(error) && error.response?.status === 401) {
            return undefined
        }
        ElMessage.error(this.getErrorMessage(error))
        return undefined
    }

    private getErrorMessage(error: unknown): string {
        if (axios.isAxiosError(error)) {
            const responseData = error.response?.data
            if (typeof responseData === 'string') {
                return responseData
            }
            if (responseData && typeof responseData === 'object') {
                const data = responseData as Record<string, unknown>
                return String(data.message || data.msg || data.error || data.detail || 'Backend request failed')
            }
            return error.message || 'Backend request failed'
        }

        if (error instanceof Error) {
            return error.message
        }

        return 'Request failed'
    }
}

export const request = new Request()
