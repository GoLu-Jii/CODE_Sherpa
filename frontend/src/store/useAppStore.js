import { create } from 'zustand';
import { sendChatMessage } from '../api/sherpaClient';

const useAppStore = create((set, get) => ({
  // Repository state
  repo: {
    url: '',
    raw_ast: null,
    mermaid_chart: '',
    status: 'idle', // idle | loading | ready | error
    error: null,
  },

  // Chat state
  chatHistory: [],
  isLoadingChat: false,

  // Graph state
  selectedNode: null,

  // Actions - Repo
  setRepoUrl: (url) => set((state) => ({ repo: { ...state.repo, url } })),

  setRepoStatus: (status, error = null) =>
    set((state) => ({ repo: { ...state.repo, status, error } })),

  setRepoData: (data) =>
    set((state) => ({
      repo: {
        ...state.repo,
        raw_ast: data.raw_ast,
        mermaid_chart: data.mermaid_chart,
        status: 'ready',
        error: null,
      },
    })),

  // Actions - Graph
  setSelectedNode: (node) => set({ selectedNode: node }),

  // Actions - Chat
  addChatMessage: (msg) =>
    set((state) => ({ chatHistory: [...state.chatHistory, msg] })),

  setLoadingChat: (isLoading) => set({ isLoadingChat: isLoading }),

  clearChat: () => set({ chatHistory: [] }),

  // Send a query triggered from a graph node click
  sendNodeQuery: async (nodeLabel, nodeType) => {
    const { isLoadingChat, chatHistory, addChatMessage, setLoadingChat } = get();
    if (isLoadingChat) return;

    // Construct query based on node type
    const query =
      nodeType === 'function'
        ? `what does the function ${nodeLabel} do`
        : `what does ${nodeLabel} do`;

    addChatMessage({ role: 'user', content: query, timestamp: new Date() });
    setLoadingChat(true);

    try {
      const historyForApi = chatHistory.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await sendChatMessage(query, historyForApi);
      const answerPayload = response?.data;

      addChatMessage({
        role: 'assistant',
        content: answerPayload?.answer ?? 'No answer returned.',
        sources: answerPayload?.sources || [],
        timestamp: new Date(),
      });
    } catch (error) {
      addChatMessage({
        role: 'assistant',
        content: `Error: Failed to communicate with the Sherpa engine. (${error.message || 'Unknown error'})`,
        isError: true,
        timestamp: new Date(),
      });
    } finally {
      setLoadingChat(false);
    }
  },
}));

export default useAppStore;