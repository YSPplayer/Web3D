import axios from 'axios'
import type { AxiosInstance } from 'axios'
import { ElMessage } from 'element-plus'

export class Request {
    private axios: AxiosInstance | null

    constructor() {
        this.axios = null
    }

    create(url: string, timeout: number = 60000): void {
        if (this.axios) return
        this.axios = axios.create({
            baseURL: url,
            timeout: timeout
        })
    }

    async get<T = any>(url: string, params: any = {}): Promise<T> {
        if (!this.axios) return Promise.reject(new Error('Please call create() first'))

        try {
            const response = await this.axios.get<T>(url, params)
            return response.data
        } catch (error) {
            const message = this.getErrorMessage(error)
            console.log('Backend request error:', error)
            ElMessage.error(message)
            // throw error
        }
    }

    async put<T = any>(url: string, data: any = {}): Promise<T> {
        if (!this.axios) return Promise.reject(new Error('Please call create() first'))

        try {
            const response = await this.axios.put<T>(url, data)
            return response.data
        } catch (error) {
            const message = this.getErrorMessage(error)
            console.log('Backend request error:', error)
            ElMessage.error(message)
            //throw error
        }
    }

    async delete<T = any>(url: string, params: any = {}): Promise<T> {
        if (!this.axios) return Promise.reject(new Error('Please call create() first'))

        try {
            const response = await this.axios.delete<T>(url, { params })
            return response.data
        } catch (error) {
            const message = this.getErrorMessage(error)
            console.log('Backend request error:', error)
            ElMessage.error(message)
            //throw error
        }
    }

    async post<T = any>(url: string, data: any = {}): Promise<T> {
        if (!this.axios) return Promise.reject(new Error('Please call create() first'))

        try {
            const response = await this.axios.post<T>(url, data)
            return response.data
        } catch (error) {
            const message = this.getErrorMessage(error)
            console.log('Backend request error:', error)
            ElMessage.error(message)
            //throw error
        }
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
