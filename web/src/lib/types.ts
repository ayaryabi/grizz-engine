export interface FileAttachment {
  id: string;
  file?: File; // For optimistic display before upload
  url?: string; // For actual uploaded file URL
  name: string;
  size: number;
  type: string;
  uploading?: boolean;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp?: string; // We can refine this to Date later
  files?: FileAttachment[];
} 