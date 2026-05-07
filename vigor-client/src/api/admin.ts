import request from './index'

export const adminApi = {
  login(username: string, password: string): Promise<{ token: string }> {
    return request.post('/api/admin/login', { username, password })
  },

  logout(): Promise<void> {
    return request.post('/api/admin/logout')
  }
}
