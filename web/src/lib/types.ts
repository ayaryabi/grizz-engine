export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp?: string; // We can refine this to Date later
} 