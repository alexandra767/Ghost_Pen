"use client";

import ReactMarkdown from "react-markdown";

interface BlogContentProps {
  content: string;
}

export function BlogContent({ content }: BlogContentProps) {
  return (
    <div className="prose-ghost max-w-none">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
