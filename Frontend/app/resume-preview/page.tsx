"use client"
import React from "react";
import { useRouter } from "next/navigation";
import { Download, ArrowLeft, FileText } from "lucide-react";
import remarkGfm from "remark-gfm";
import ReactMarkdown from 'react-markdown';

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

// Add a new utility to further clean and format resume markdown for display
function formatResumeMarkdown(md: string) {
  // Remove duplicate subheadings within a section
  md = md.replace(/(Relevant Coursework:)([\s\S]*?)(?=Relevant Coursework:|$)/g, (block: string) => {
    // Only keep the first 'Relevant Coursework:' per section
    const lines = block.split('\n');
    const seen = new Set();
    return lines.filter((line: string) => {
      if (/^Relevant Coursework:/i.test(line)) {
        if (seen.has('rc')) return false;
        seen.add('rc');
      }
      return true;
    }).join('\n');
  });
  // Bulletize comma-separated lists
  md = md.replace(/(Relevant Coursework:|Skills:|Technologies:|Tools:|Languages:|Achievements:|Responsibilities:)[ \t]*\n?([^-\n][^\n]*)/gi, (match: string, heading: string, items: string) => {
    if (!items) return match;
    const bullets = items.split(/,|•|\u2022/).map((s: string) => s.trim()).filter(Boolean);
    if (bullets.length > 1) {
      return `${heading}\n` + bullets.map((b: string) => `- ${b}`).join('\n');
    }
    return match;
  });
  // Bulletize any line with multiple comma-separated items (not already a list)
  md = md.replace(/^(?![-*] )([^\n]+,[^\n]+)$/gm, (line: string) => {
    const items = line.split(/,|•|\u2022/).map((s: string) => s.trim()).filter(Boolean);
    if (items.length > 1) {
      return items.map((b: string) => `- ${b}`).join('\n');
    }
    return line;
  });
  // Remove extra blank lines
  md = md.replace(/\n{3,}/g, '\n\n');
  return md;
}

function parseSection(section: string) {
  const lines = section.trim().split(/\n+/);
  const heading = lines[0]?.replace(/^#+\s*/, "").trim();
  const content = lines.slice(1).join("\n").trim();
  return { heading, content };
}

// Add a new formatter for section-aware resume rendering
export function formatResumeSections(sections: string[]): JSX.Element[] {
  return sections.map((section, i) => {
    const { heading, content } = parseSection(section);
    if (!heading) return null;
    // Skills: comma-separated
    if (/skills|technologies|tools|languages|certifications/i.test(heading)) {
      const items = content.split(/[,•\-\n]+/).map(s => s.trim()).filter(Boolean);
      return (
        <section key={i} className="resume-section mb-10">
          <h2 className="resume-heading text-2xl font-bold text-emerald-700 mb-4 tracking-tight">{heading}</h2>
          <div className="text-slate-700 text-base leading-relaxed font-normal">
            {items.join(', ')}
          </div>
        </section>
      );
    }
    // Projects: Title, tech/tools, bullets
    if (/projects?/i.test(heading)) {
      // Split by double newlines or project markers
      const entries = content.split(/\n{2,}|(?=^[A-Z][^\n]+\|[^\n]+|\*\*.+\*\*)/gm).map(e => e.trim()).filter(Boolean);
      return (
        <section key={i} className="resume-section mb-10">
          <h2 className="resume-heading text-2xl font-bold text-emerald-700 mb-4 tracking-tight">{heading}</h2>
          <div className="space-y-8">
            {entries.map((entry, idx) => {
              // Try to split title/tools/details
              let [firstLine, ...rest] = entry.split('\n');
              let title = firstLine, tech = '', details = rest.join('\n').trim();
              // If firstLine contains |, treat as Title | Tech
              if (/\|/.test(firstLine)) {
                const parts = firstLine.split('|').map(s => s.trim());
                title = parts[0];
                tech = parts.slice(1).join(' | ');
              }
              // Bulletize details
              let bullets = details.split(/\n|(?<!\d), /).map(s => s.trim()).filter(Boolean);
              // Remove bullets that are just tech/tools
              bullets = bullets.filter(b => b && b !== tech && b !== title);
              return (
                <div key={idx} className="mb-4">
                  <div className="font-bold text-lg text-slate-900 mb-1">{title}</div>
                  {tech && <div className="text-slate-500 text-sm mb-1 italic">{tech}</div>}
                  {bullets.length > 0 && (
                    <ul className="list-disc ml-6 space-y-1">
                      {bullets.map((b, j) => <li key={j} className="text-slate-700 text-base leading-relaxed font-normal">{b}</li>)}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      );
    }
    // Experience: Job Title | Company | Date, bullets
    if (/experience/i.test(heading)) {
      const entries = content.split(/\n{2,}|(?=^[A-Z][^\n]+\|[^\n]+|\*\*.+\*\*)/gm).map(e => e.trim()).filter(Boolean);
      return (
        <section key={i} className="resume-section mb-10">
          <h2 className="resume-heading text-2xl font-bold text-emerald-700 mb-4 tracking-tight">{heading}</h2>
          <div className="space-y-8">
            {entries.map((entry, idx) => {
              let [firstLine, ...rest] = entry.split('\n');
              let title = firstLine, meta = '', details = rest.join('\n').trim();
              // Try to extract Job Title | Company | Date
              if (/\|/.test(firstLine)) {
                const parts = firstLine.split('|').map(s => s.trim());
                title = parts.slice(0, -1).join(' | ');
                meta = parts[parts.length - 1];
              }
              // Bulletize details
              let bullets = details.split(/\n|(?<!\d), /).map(s => s.trim()).filter(Boolean);
              bullets = bullets.filter(b => b && b !== meta && b !== title);
              return (
                <div key={idx} className="mb-4">
                  <div className="font-bold text-lg text-slate-900 mb-1">{title}</div>
                  {meta && <div className="text-slate-500 text-sm mb-1">{meta}</div>}
                  {bullets.length > 0 && (
                    <ul className="list-disc ml-6 space-y-1">
                      {bullets.map((b, j) => <li key={j} className="text-slate-700 text-base leading-relaxed font-normal">{b}</li>)}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      );
    }
    // Education: Degree | Institution | Date, optional GPA/honors
    if (/education/i.test(heading)) {
      const entries = content.split(/\n{2,}|(?=^[A-Z][^\n]+\|[^\n]+|\*\*.+\*\*)/gm).map(e => e.trim()).filter(Boolean);
      return (
        <section key={i} className="resume-section mb-10">
          <h2 className="resume-heading text-2xl font-bold text-emerald-700 mb-4 tracking-tight">{heading}</h2>
          <div className="space-y-8">
            {entries.map((entry, idx) => {
              let [firstLine, ...rest] = entry.split('\n');
              let degree = firstLine, meta = '', details = rest.join('\n').trim();
              // Try to extract Degree | Institution | Date
              if (/\|/.test(firstLine)) {
                const parts = firstLine.split('|').map(s => s.trim());
                degree = parts.slice(0, -1).join(' | ');
                meta = parts[parts.length - 1];
              }
              // GPA/honors
              let extras = details.split(/\n|, /).map(s => s.trim()).filter(Boolean);
              extras = extras.filter(e => e && e !== meta && e !== degree);
              return (
                <div key={idx} className="mb-4">
                  <div className="font-bold text-lg text-slate-900 mb-1">{degree}</div>
                  {meta && <div className="text-slate-500 text-sm mb-1">{meta}</div>}
                  {extras.length > 0 && (
                    <div className="text-slate-600 text-sm mt-1">{extras.join(' | ')}</div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      );
    }
    // Default: paragraph
    return (
      <section key={i} className="resume-section mb-10">
        <h2 className="resume-heading text-2xl font-bold text-emerald-700 mb-4 tracking-tight">{heading}</h2>
        <div className="text-slate-700 text-base leading-relaxed font-normal whitespace-pre-line">{content}</div>
      </section>
    );
  }).filter(Boolean) as JSX.Element[];
}

// Utility to fetch the final resume from the backend
async function fetchFinalResume(analysisId: string): Promise<string> {
  // Try the new backend endpoint
  const res = await fetch(`/api/final-resume/${encodeURIComponent(analysisId)}`);
  if (!res.ok) throw new Error('Failed to fetch final resume');
  const data = await res.json();
  return data.final_resume || data.data?.final_resume || '';
}

export default function ResumePreview() {
  const router = useRouter();
  const [resume, setResume] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    // Get analysis_id from query param or sessionStorage
    const params = new URLSearchParams(window.location.search);
    let analysisId = params.get("analysis_id");
    if (!analysisId) {
      analysisId = window.sessionStorage.getItem("last_analysis_id") || '';
    }
    if (!analysisId) {
      setError("No analysis ID found. Please run an analysis first.");
      setLoading(false);
      return;
    }
    fetchFinalResume(analysisId)
      .then(resumeText => {
        setResume(resumeText);
        setLoading(false);
      })
      .catch(e => {
        // Fallback: try sessionStorage if available
        const fallback = window.sessionStorage.getItem("last_final_resume") || '';
        if (fallback) {
          setResume(fallback);
        } else {
          setError("Failed to load final resume.");
        }
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="text-center py-20 text-lg">Loading resume preview...</div>;
  }
  if (error) {
    return <div className="text-center py-20 text-red-600">{error}</div>;
  }

  return (
    <div className="animate-fade-in">
      {/* Top bar with New Analysis button and download icon */}
      <div className="flex items-center justify-between mb-6">
        <button className="btn-secondary" onClick={() => router.push("/")}> <ArrowLeft className="w-4 h-4 mr-2" /> New Analysis </button>
        {/* Download icon button with tooltip */}
        <button
          className="btn-ghost relative group"
          onClick={() => downloadTxt("ResumeWise-Resume.txt", resume)}
          title="Download as TXT"
          style={{ padding: 8, borderRadius: 8 }}
        >
          <Download className="w-6 h-6 text-slate-500 group-hover:text-blue-600 transition" />
          <span className="tooltip group-hover:opacity-100 group-focus:opacity-100">Download as TXT</span>
        </button>
      </div>
      <div className="text-center mb-8">
        <div className="inline-flex items-center space-x-2 bg-emerald-100 text-emerald-800 px-4 py-2 rounded-full text-sm font-medium mb-4">
          <FileText className="w-4 h-4" />
          <span>Resume Preview</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">Your Improved Resume</h1>
        <p className="text-slate-600 max-w-2xl mx-auto">Here's your resume with all accepted improvements applied.</p>
      </div>
      <div className="resume-card relative">
        <div className="max-w-3xl mx-auto prose max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{resume}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
} 