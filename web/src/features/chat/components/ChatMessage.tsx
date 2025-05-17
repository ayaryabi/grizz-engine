"use client";

import React from 'react';
import { Message } from '@/lib/types';
import { cn } from "@/lib/utils";
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';
import CodeBlock from '@/components/ui/CodeBlock';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  // Define components for ReactMarkdown with CodeBlock
  const markdownComponents: Components = {
    h1: ({ node, ...props }) => <h1 className="text-2xl font-bold my-4" {...props} />,
    h2: ({ node, ...props }) => <h2 className="text-xl font-bold my-3" {...props} />,
    h3: ({ node, ...props }) => <h3 className="text-lg font-bold my-2" {...props} />,
    h4: ({ node, ...props }) => <h4 className="text-base font-bold my-2" {...props} />,
    h5: ({ node, ...props }) => <h5 className="text-sm font-bold my-1" {...props} />,
    h6: ({ node, ...props }) => <h6 className="text-xs font-bold my-1" {...props} />,
    p: ({ node, ...props }) => <p className="my-2" {...props} />,
    ul: ({ node, ...props }) => <ul className="list-disc ml-6 my-2" {...props} />,
    ol: ({ node, ...props }) => <ol className="list-decimal ml-6 my-2" {...props} />,
    li: ({ node, ...props }) => <li className="ml-2 my-1" {...props} />,
    blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-gray-300 pl-4 my-2 italic" {...props} />,
    // Use CodeBlock for code blocks
    code: ({ node, inline, className, children, ...props }: any) => {
      if (inline) {
        return <code className="bg-gray-200 dark:bg-gray-800 px-1 py-0.5 rounded text-sm" {...props}>{children}</code>;
      }
      return <CodeBlock className={className}>{children}</CodeBlock>;
    },
    table: ({ node, ...props }) => <table className="border-collapse table-auto w-full my-4" {...props} />,
    thead: ({ node, ...props }) => <thead className="bg-gray-200 dark:bg-gray-800" {...props} />,
    tbody: ({ node, ...props }) => <tbody {...props} />,
    tr: ({ node, ...props }) => <tr className="border-b dark:border-gray-700" {...props} />,
    th: ({ node, ...props }) => <th className="border px-4 py-2 text-left" {...props} />,
    td: ({ node, ...props }) => <td className="border px-4 py-2" {...props} />,
    a: ({ node, ...props }) => <a className="text-blue-500 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
    img: ({ node, ...props }) => <img className="max-w-full h-auto my-4" {...props} />,
    hr: ({ node, ...props }) => <hr className="my-4 border-t border-gray-300 dark:border-gray-700" {...props} />,
  };

  return (
    <div className={cn("flex mb-3", isUser ? "justify-end" : "justify-start")}>
      {isUser ? (
        <div className="max-w-[70%] text-sm leading-relaxed break-words px-4 py-2.5 rounded-xl shadow-sm bg-secondary text-secondary-foreground rounded-br-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={markdownComponents}
          >
            {message.text}
          </ReactMarkdown>
        </div>
      ) : (
        <div className="max-w-[70%] text-sm leading-relaxed break-words p-4">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={markdownComponents}
          >
            {message.text}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
};

export default ChatMessage; 