import { create } from 'zustand';

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
  selectedNode: null, // { id, label, type, etc... }
  
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
        error: null
      } 
    })),
    
  // Actions - Graph
  setSelectedNode: (node) => set({ selectedNode: node }),
  
  // Actions - Chat
  addChatMessage: (msg) => 
    set((state) => ({ chatHistory: [...state.chatHistory, msg] })),
    
  setLoadingChat: (isLoading) => set({ isLoadingChat: isLoading }),
  
  clearChat: () => set({ chatHistory: [] }),
}));

export default useAppStore;
