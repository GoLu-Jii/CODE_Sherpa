import { create } from 'zustand';

const useAppStore = create((set) => ({
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
  chatMode: 'ASK',
  chatPrefill: { targetName: '', query: '' },
  prefillToken: 0,

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

  setChatMode: (mode) => set({ chatMode: mode }),

  prefillChatInput: ({ mode, targetName, query = '' }) =>
    set((state) => ({
      chatMode: mode,
      chatPrefill: { targetName, query },
      prefillToken: state.prefillToken + 1,
    })),

  clearChat: () => set({ chatHistory: [] }),
}));

export default useAppStore;
