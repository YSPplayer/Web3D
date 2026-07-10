import { request } from './request'

export const grayImageApi = {
  async generateGrayDatas(count: number): Promise<any> {
    return await request.post('/grayImage/generateGrayDatas', { count })
  },
  async getGrayDatasByPage(params:any): Promise<any> {
    return await request.get('/grayImage/getGrayDatasByPage', { params })
  },
  async getGrayDataTotalCount(): Promise<any> {
    return await request.get('/grayImage/getGrayDataTotalCount')
  }
}
