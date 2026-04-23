import axios, { AxiosInstance } from 'axios';
import { ElMessage } from 'element-plus';

export class Request {
    private axios:AxiosInstance | null
    constructor() {
        this.axios = null
    }
    create(url:string,timeout:number = 60000):void {
        if(this.axios) return
        this.axios = axios.create({
            baseURL: url,
            timeout: timeout
        })
    }
    async get<T = any>(url:string,params:any = {}):Promise<T> {
        if (!this.axios) return Promise.reject(new Error('请先调用create方法初始化接口'));

        try {
            const response = await this.axios.get<T>(url,{params: params });
            return response.data;
        } catch (error) {
            const message = this.getErrorMessage(error);
            console.log('后端请求错误:', error);
            ElMessage.error(message);
            throw error;
        }
    }

    private getErrorMessage(error: unknown): string {
        if (axios.isAxiosError(error)) {
            const responseData = error.response?.data;
            if (typeof responseData === 'string') {
                return responseData;
            }
            if (responseData && typeof responseData === 'object') {
                const data = responseData as Record<string, unknown>;
                return String(data.message || data.msg || data.error || data.detail || '后端请求失败');
            }
            return error.message || '后端请求失败';
        }

        if (error instanceof Error) {
            return error.message;
        }

        return '请求失败';
    }
}
export const request = new Request()
