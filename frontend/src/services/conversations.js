import api from './api';

export const conversationService = {
  // Get all conversations for current user
  async getConversations() {
    const response = await api.get('/conversations');
    return response.data;
  },

  // Get conversations by assistant type
  async getConversationsByAssistant(assistantType) {
    const response = await api.get(`/conversations?assistant_type=${assistantType}`);
    return response.data;
  },

  // Create new conversation
  async createConversation(assistantType, title = 'New conversation') {
    const response = await api.post('/conversations', {
      assistant_type: assistantType,
      title
    });
    return response.data;
  },

  // Get single conversation with messages
  async getConversation(conversationId) {
    const response = await api.get(`/conversations/${conversationId}`);
    return response.data;
  },

  // Update conversation title
  async updateConversation(conversationId, title) {
    const response = await api.put(`/conversations/${conversationId}`, { title });
    return response.data;
  },

  // Delete conversation
  async deleteConversation(conversationId) {
    await api.delete(`/conversations/${conversationId}`);
  },

  // Add message to conversation
  async addMessage(conversationId, role, content) {
    const response = await api.post(`/conversations/${conversationId}/messages`, {
      role,
      content
    });
    return response.data;
  },

  // Get user statistics
  async getUserStats() {
    const response = await api.get('/conversations/stats/user');
    return response.data;
  }
};
