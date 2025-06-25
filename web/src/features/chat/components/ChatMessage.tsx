"use client";

import React from 'react';
import { Message, FileAttachment } from '@/lib/types';
import { cn } from "@/lib/utils";
import ReactMarkdown, { Components } from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import CodeBlock from '@/components/ui/CodeBlock';
import Image from 'next/image';
import { FileIcon, Loader2, ExternalLink } from 'lucide-react';

interface CodeProps {
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

interface ChatMessageProps {
  message: Message;
}

const FileAttachmentDisplay: React.FC<{ file: FileAttachment }> = ({ file }) => {
  const isImage = file.type.startsWith('image');
  
  // Always call hooks at the top level - React Rules of Hooks
  const [previewUrl, setPreviewUrl] = React.useState<string>();
  
  React.useEffect(() => {
    // Only create preview URL for images that have a file but no URL yet
    if (file.file && !file.url && isImage) {
      const url = URL.createObjectURL(file.file);
      setPreviewUrl(url);
      
      // Cleanup function
      return () => {
        URL.revokeObjectURL(url);
        setPreviewUrl(undefined);
      };
    } else {
      // Clear preview URL if conditions don't match
      setPreviewUrl(undefined);
    }
  }, [file.file, file.url, isImage]);
  
  // Show loading state
  if (file.uploading) {
    return (
      <div className="flex items-center gap-2 p-3 bg-muted rounded-lg mb-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{file.name}</p>
          <p className="text-xs text-muted-foreground">Uploading...</p>
        </div>
      </div>
    );
  }
  
  // Show error state if upload failed
  if (!file.url && !file.file) {
    return (
      <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg mb-2">
        <FileIcon className="h-4 w-4 text-destructive" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{file.name}</p>
          <p className="text-xs text-destructive">Upload failed</p>
        </div>
      </div>
    );
  }
  
  // Show uploaded file with URL (final state)
  if (file.url) {
    if (isImage) {
      return (
        <div className="mb-2">
          <img
            src={file.url}
            alt={file.name}
            className="max-w-full h-auto max-h-64 rounded-lg object-contain"
            loading="lazy"
          />
        </div>
      );
    } else {
      return (
        <a 
          href={file.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-2 p-3 bg-muted hover:bg-muted/80 rounded-lg mb-2 transition-colors"
        >
          <FileIcon className="h-4 w-4" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{file.name}</p>
            <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
          <ExternalLink className="h-3 w-3" />
        </a>
      );
    }
  }
  
  // Show preview for files still uploading (optimistic display)
  if (file.file && !file.url) {
    if (isImage && previewUrl) {
      return (
        <div className="mb-2">
          <img
            src={previewUrl}
            alt={file.name}
            className="max-w-full h-auto max-h-64 rounded-lg"
          />
        </div>
      );
    } else {
      return (
        <div className="flex items-center gap-2 p-3 bg-muted rounded-lg mb-2">
          <FileIcon className="h-4 w-4" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{file.name}</p>
            <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
        </div>
      );
    }
  }
  
  return null;
};

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  // Define components for ReactMarkdown with CodeBlock
  const markdownComponents: Components = {
    h1: ({ children }) => <h1 className="text-2xl font-bold my-4">{children}</h1>,
    h2: ({ children }) => <h2 className="text-xl font-bold my-3">{children}</h2>,
    h3: ({ children }) => <h3 className="text-lg font-bold my-2">{children}</h3>,
    h4: ({ children }) => <h4 className="text-base font-bold my-2">{children}</h4>,
    h5: ({ children }) => <h5 className="text-sm font-bold my-1">{children}</h5>,
    h6: ({ children }) => <h6 className="text-xs font-bold my-1">{children}</h6>,
    p: ({ children }) => <p className="my-2">{children}</p>,
    ul: ({ children }) => <ul className="list-disc ml-6 my-2">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal ml-6 my-2">{children}</ol>,
    li: ({ children }) => <li className="ml-2 my-1">{children}</li>,
    blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 my-2 italic">{children}</blockquote>,
    code: (props: CodeProps) => {
      const {inline, className, children} = props;
      if (inline) {
        return <code className="bg-gray-200 dark:bg-gray-800 px-1 py-0.5 rounded text-sm">{children}</code>;
      }
      return <CodeBlock className={className}>{children}</CodeBlock>;
    },
    table: ({ children }) => <table className="border-collapse table-auto w-full my-4">{children}</table>,
    thead: ({ children }) => <thead className="bg-gray-200 dark:bg-gray-800">{children}</thead>,
    tbody: ({ children }) => <tbody>{children}</tbody>,
    tr: ({ children }) => <tr className="border-b dark:border-gray-700">{children}</tr>,
    th: ({ children }) => <th className="border px-4 py-2 text-left">{children}</th>,
    td: ({ children }) => <td className="border px-4 py-2">{children}</td>,
    a: ({ children, href }) => <a className="text-blue-500 hover:underline" href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
    img: ({ src, alt = "" }) => {
      if (!src || typeof src !== 'string') return null;
      return (
        <Image
          src={src}
          alt={alt}
          width={800}
          height={400}
          className="max-w-full h-auto my-4"
        />
      );
    },
    hr: () => <hr className="my-4 border-t border-gray-300 dark:border-gray-700" />,
  };

  return (
    <div className={cn("flex mb-3", isUser ? "justify-end" : "justify-start")}>
      {isUser ? (
        <div className="max-w-[70%] text-sm leading-relaxed break-words px-4 py-2.5 rounded-xl shadow-sm bg-secondary text-secondary-foreground rounded-br-none">
          {/* Display file attachments */}
          {message.files && message.files.length > 0 && (
            <div className="mb-3">
              {message.files.map((file) => (
                <FileAttachmentDisplay key={file.id} file={file} />
              ))}
            </div>
          )}
          
          {/* Display text message */}
          {message.text && (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={markdownComponents}
            >
              {message.text}
            </ReactMarkdown>
          )}
        </div>
      ) : (
        <div className="max-w-[70%] text-sm leading-relaxed break-words p-4">
          {/* Display file attachments */}
          {message.files && message.files.length > 0 && (
            <div className="mb-3">
              {message.files.map((file) => (
                <FileAttachmentDisplay key={file.id} file={file} />
              ))}
            </div>
          )}
          
          {/* Display text message */}
          {message.text && (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={markdownComponents}
            >
              {message.text}
            </ReactMarkdown>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatMessage; 