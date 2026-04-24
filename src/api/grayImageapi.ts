import { request } from './request'

export const grayImageApi = {
  async generateGrayDatas(count: number): Promise<any> {
    return await request.post('/grayImage/generateGrayDatas', { count })
  }
}
