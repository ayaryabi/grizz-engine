import React, { useState } from 'react';

interface CodeBlockProps {
  children: React.ReactNode;
  className?: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ children, className }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (typeof children === 'string') {
      navigator.clipboard.writeText(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <div className={`relative group ${className || ''}`}>
      <button
        className="absolute top-2 right-2 text-xs px-2 py-1 rounded bg-gray-700 text-white opacity-0 group-hover:opacity-100 transition"
        onClick={handleCopy}
        type="button"
      >
        {copied ? 'Copied!' : 'Copy'}
      </button>
      <pre className="rounded bg-gray-900 p-4 overflow-x-auto text-sm text-gray-100">
        <code>{children}</code>
      </pre>
    </div>
  );
};

export default CodeBlock; 