"use client"
import React from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { Download } from "lucide-react";
import remarkGfm from "remark-gfm";

// Utility to decode base64 to string
function decodeBase64(str: string) {
  try {
    return decodeURIComponent(escape(window.atob(str)));
  } catch {
    return "";
  }
}

// Utility to trigger TXT download
function downloadTxt(filename: string, text: string) {
  const element = document.createElement("a");
  const file = new Blob([text], { type: "text/plain" });
  element.href = URL.createObjectURL(file);
  element.download = filename;
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}

// Utility to clean up markdown: remove duplicate headings, fix structure, and convert bullets
export function cleanResumeMarkdown(md: string) {
  // Remove any subheading (###) that immediately follows a section heading (##) with the same text
  md = md.replace(/(##+ .+)\n(### .+)\n/g, (match, h2, h3) => {
    if (h2.replace(/#+ /, '') === h3.replace(/#+ /, '')) return h2 + '\n';
    return match;
  });
  // Remove all but the first occurrence of each section heading (e.g., '## Technical Skills')
  const seen = new Set<string>();
  md = md.split('\n').filter(line => {
    const headingMatch = line.match(/^(#+) (.+)$/);
    if (headingMatch) {
      const key = headingMatch[2].trim().toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
    }
    return true;
  }).join('\n');
  // Group lines starting with '-' or '*' into proper Markdown lists, ensuring blank lines before/after
  md = md.replace(/((?:^[-*] .+(?:\n|$))+)/gm, (block) => {
    // Ensure blank line before and after
    return '\n' + block.trim() + '\n';
  });
  // Add extra blank lines before section headings for spacing
  md = md.replace(/(#+ .+)/g, '\n$1');
  // Remove extra blank lines at the start
  md = md.replace(/^\s+/, '');
  return md;
}

export default function ResumePreview() {
  const router = useRouter();
  // Parse resume data from query string
  const [resume, setResume] = React.useState("");
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => {
    setMounted(true);
    const params = new URLSearchParams(window.location.search);
    const data = params.get("data");
    if (data) setResume(cleanResumeMarkdown(decodeBase64(data)));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50 font-sans text-slate-900 flex flex-col items-center py-0 px-2">
      {/* Top bar with heading and button */}
      <div className="w-full max-w-3xl flex items-center justify-between px-4 py-6 sticky top-0 z-20 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md shadow-md rounded-b-xl border-b border-slate-200 mb-0">
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">Your Improved Resume</h1>
        <button
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2 rounded-full shadow transition-all focus:outline-none focus:ring-2 focus:ring-blue-400 text-base"
          onClick={() => router.push("/")}
        >
          Start New Analysis
        </button>
      </div>
      {/* Resume content with card background and extra spacing */}
      <div className="w-full max-w-3xl bg-white dark:bg-slate-900 rounded-3xl shadow-xl p-6 md:p-12 text-base leading-relaxed relative mt-10 mb-16 border border-slate-100 dark:border-slate-800 transition-all">
        {/* Download icon button with tooltip */}
        <div className="absolute top-4 right-4 group">
          <button
            className="p-2 rounded-full bg-blue-100 hover:bg-blue-200 text-blue-600 hover:text-blue-800 transition focus:outline-none focus:ring-2 focus:ring-blue-400 shadow"
            title="Download as TXT"
            aria-label="Download as TXT"
            onClick={() => downloadTxt("ResumeWise-Resume.txt", resume)}
          >
            <Download className="w-5 h-5" />
          </button>
          <span className="absolute right-0 mt-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition pointer-events-none whitespace-nowrap z-50">
            Download as TXT
          </span>
        </div>
        {resume ? (
          <div className="prose prose-slate max-w-none">
            {mounted && (() => {
              const ReactMarkdown = require('react-markdown').default;
              return <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: (props: React.PropsWithChildren<any>) => <h1 className="text-3xl font-extrabold mt-10 mb-8 border-b border-slate-200 pb-2 tracking-tight text-slate-900 dark:text-white" {...props} />,
                  h2: (props: React.PropsWithChildren<any>) => <h2 className="text-2xl font-bold mt-10 mb-6 border-b border-slate-100 pb-1 text-blue-700 dark:text-blue-400" style={{marginTop: '2.5rem'}} {...props} />,
                  h3: (props: React.PropsWithChildren<any>) => <h3 className="text-lg font-semibold mt-8 mb-3 text-blue-600 dark:text-blue-300 border-b border-slate-50 pb-1" style={{marginTop: '2rem'}} {...props} />,
                  ul: (props: React.PropsWithChildren<any>) => <ul className="list-disc ml-8 mb-4 space-y-2" {...props} />,
                  li: (props: React.PropsWithChildren<any>) => <li className="mb-1 pl-1 text-base leading-relaxed" {...props} />,
                  strong: (props: React.PropsWithChildren<any>) => <strong className="font-bold text-slate-900 dark:text-white" {...props} />,
                  em: (props: React.PropsWithChildren<any>) => <em className="italic text-slate-700 dark:text-slate-300" {...props} />,
                  p: (props: React.PropsWithChildren<any>) => <p className="mb-3 text-base leading-relaxed" {...props} />,
                  hr: () => <hr className="my-8 border-slate-200 dark:border-slate-700" />,
                }}
              >{resume}</ReactMarkdown>;
            })()}
          </div>
        ) : (
          <span className="text-slate-400">No resume data found.</span>
        )}
      </div>
    </div>
  );
} 