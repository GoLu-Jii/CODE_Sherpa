import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const ingestRepository = async (repoUrl) => {
  try {
    const response = await client.post('/api/v1/ingest/github-repo', {
      repo_url: repoUrl
    });
    return response.data;
  } catch (error) {
    console.error('Error ingesting repository:', error);
    throw error;
  }
};

export const sendChatMessage = async (query, history = []) => {
  try {
    const response = await client.post('/api/v1/sherpachat/chat', {
      query,
      history
    });
    return response.data;
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
};

export default client;
