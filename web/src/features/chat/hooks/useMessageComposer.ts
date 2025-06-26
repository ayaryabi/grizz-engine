import { useState, useCallback } from 'react';
import { FileAttachment } from '@/lib/types';
import { useAuth } from '@/features/auth/AuthContext';

interface FilePreview {
  file: File;
  id: string;
  preview?: string;
}

interface UseMessageComposerReturn {
  inputText: string;
  setInputText: (v: string) => void;
  selectedFiles: FilePreview[];
  addFiles: (files: FileList) => void;
  removeFile: (id: string) => void;
  handleSend: () => void;
  isLoading: boolean;
  setIsLoading: (v: boolean) => void;
}

/**
 * Encapsulates all business logic required to compose a chat message: text state,
 * file selection / preview management, clearing state after send, and invoking the
 * parent-provided send callback.
 */
export function useMessageComposer(onSendMessage: (text: string, files?: FileAttachment[]) => void): UseMessageComposerReturn {
  const { user } = useAuth();

  const [inputText, setInputText] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<FilePreview[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const createFilePreview = (file: File): FilePreview => {
    const preview: FilePreview = {
      file,
      id: Math.random().toString(36).substr(2, 9),
    };

    if (file.type.startsWith('image/')) {
      preview.preview = URL.createObjectURL(file);
    }
    return preview;
  };

  const addFiles = useCallback((files: FileList) => {
    const fileArray = Array.from(files);
    const newPreviews = fileArray.map(createFilePreview);
    setSelectedFiles((prev) => [...prev, ...newPreviews]);
  }, []);

  const removeFile = useCallback((id: string) => {
    setSelectedFiles((prev) => {
      const updated = prev.filter((fp) => fp.id !== id);
      const removed = prev.find((fp) => fp.id === id);
      if (removed?.preview) {
        URL.revokeObjectURL(removed.preview);
      }
      return updated;
    });
  }, []);

  const clearState = () => {
    setInputText('');
    setSelectedFiles((prev) => {
      prev.forEach((fp) => {
        if (fp.preview) URL.revokeObjectURL(fp.preview);
      });
      return [];
    });
  };

  const handleSend = useCallback(() => {
    const trimmed = inputText.trim();
    if (!trimmed && selectedFiles.length === 0) return;

    if (!user?.id) {
      alert('Please log in to send messages with files.');
      return;
    }

    setIsLoading(true);

    const fileAttachments: FileAttachment[] = selectedFiles.map((fp) => ({
      id: fp.id,
      file: fp.file,
      name: fp.file.name,
      size: fp.file.size,
      type: fp.file.type,
      uploading: true,
    }));

    onSendMessage(trimmed, fileAttachments.length > 0 ? fileAttachments : undefined);

    clearState();
    setIsLoading(false);
  }, [inputText, selectedFiles, user?.id, onSendMessage]);

  return {
    inputText,
    setInputText,
    selectedFiles,
    addFiles,
    removeFile,
    handleSend,
    isLoading,
    setIsLoading,
  };
} 