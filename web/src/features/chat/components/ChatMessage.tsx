"use client";

import React from 'react';
import { Message } from '@/lib/types';
import { cn } from "@/lib/utils";
import ReactMarkdown, { Components } from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import CodeBlock from '@/components/ui/CodeBlock';
import Image from 'next/image';

interface CodeProps {
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

interface ChatMessageProps {
  message: Message;
}

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