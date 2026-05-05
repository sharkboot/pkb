import { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { X, ExternalLink, Calendar, Tag, Image as ImageIcon } from 'lucide-react';
import { Knowledge } from '@/lib/api';

interface NoteModalProps {
  note: Knowledge;
  onClose: () => void;
}

export default function NoteModal({ note, onClose }: NoteModalProps) {
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());

  // 提取 markdown 中的图片信息
  const extractImages = (content: string): { cleanContent: string; images: Array<{ index: number; src: string; alt: string }> } => {
    if (!content) return { cleanContent: content, images: [] };

    const images: Array<{ index: number; src: string; alt: string }> = [];
    let index = 0;

    // 提取所有图片，替换为占位符
    const cleanContent = content.replace(
      /!\[([^\]]*)\]\(([^)]+)\)/g,
      (match, alt, src) => {
        const placeholder = `__IMAGE_${index}__`;
        images.push({ index, src, alt: alt || '图片' });
        index++;
        return placeholder;
      }
    );

    return { cleanContent, images };
  };

  const { cleanContent, images } = useMemo(() => extractImages(note.content || ''), [note.content]);

  const handleImageError = (src: string) => {
    setImageErrors((prev) => new Set(prev).add(src));
  };

  const isLargeBase64 = (src: string): boolean => {
    if (!src) return false;
    // base64 数据部分超过 2MB 才认为是大图片
    const base64Part = src.includes(',') ? src.split(',')[1] : src;
    return base64Part.length > 2000000000;
  };

  // 渲染单张图片
  const renderImage = (img: { index: number; src: string; alt: string }) => {
    const errorKey = `__IMAGE_${img.index}__`;

    if (imageErrors.has(errorKey)) {
      return (
        <div key={errorKey} className="my-4 p-4 bg-gray-100 rounded-lg text-center text-gray-500 text-sm flex flex-col items-center gap-2">
          <ImageIcon className="w-8 h-8" />
          <span>图片加载失败</span>
          {img.alt && img.alt !== '图片' && (
            <span className="text-xs text-gray-400 truncate max-w-xs">{img.alt}</span>
          )}
        </div>
      );
    }

    if (isLargeBase64(img.src)) {
      return (
        <div key={errorKey} className="my-4 p-4 bg-gray-50 rounded-lg text-center text-gray-500 text-sm flex flex-col items-center gap-2 border border-gray-200">
          <ImageIcon className="w-8 h-8" />
          <span className="font-medium">大图片（base64 格式，内容较长）</span>
          {img.alt && <span className="text-xs text-gray-400">{img.alt}</span>}
        </div>
      );
    }

    return (
      <div key={errorKey} className="my-4 text-center">
        <img
          src={img.src}
          alt={img.alt}
          className="max-w-full h-auto rounded-lg shadow-sm cursor-pointer hover:shadow-md transition-shadow inline-block"
          onError={() => handleImageError(errorKey)}
          onClick={() => window.open(img.src, '_blank')}
        />
        {img.alt && img.alt !== '图片' && (
          <p className="text-xs text-gray-500 text-center mt-1">{img.alt}</p>
        )}
      </div>
    );
  };

  // 将占位符替换回图片
  const renderContentWithImages = () => {
    const parts = cleanContent.split(/(__IMAGE_\d+__)/g);

    return parts.map((part, i) => {
      const match = part.match(/__IMAGE_(\d+)__/);
      if (match) {
        const imgIndex = parseInt(match[1], 10);
        const img = images.find(img => img.index === imgIndex);
        if (img) {
          return renderImage(img);
        }
      }
      // 非图片部分，渲染 markdown
      if (part && !part.startsWith('__IMAGE_')) {
        return (
          <ReactMarkdown key={i} remarkPlugins={[remarkGfm]}>
            {part}
          </ReactMarkdown>
        );
      }
      return null;
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 遮罩 */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* 弹窗 */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* 头部 */}
        <div className="flex items-start justify-between p-5 border-b border-gray-200">
          <div className="flex-1 min-w-0 pr-4">
            <h2 className="text-lg font-semibold text-gray-900 truncate">
              {note.title || '无标题'}
            </h2>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {formatDate(note.updated_at)}
              </span>
              {note.category && (
                <span className="flex items-center gap-1">
                  <Tag className="w-3 h-3" />
                  {note.category}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* 标签 */}
        {note.tags && note.tags.length > 0 && (
          <div className="px-5 py-2 border-b border-gray-100 flex flex-wrap gap-1">
            {note.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* 摘要 */}
        {note.summary && (
          <div className="px-5 py-3 bg-gray-50 border-b border-gray-100">
            <p className="text-sm text-gray-600">{note.summary}</p>
          </div>
        )}

        {/* 内容 */}
        <div className="flex-1 overflow-y-auto p-5">
          <article className="prose prose-gray max-w-none text-gray-700
            prose-headings:text-gray-900 prose-headings:font-semibold
            prose-p:text-gray-700 prose-p:leading-relaxed
            prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
            prose-code:text-pink-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
            prose-pre:bg-gray-900 prose-pre:text-gray-100
            prose-img:rounded-lg prose-img:shadow-md
            prose-ul:list-disc prose-ol:list-decimal
            prose-li:text-gray-700
            prose-hr:border-gray-200
            prose-blockquote:border-l-4 prose-blockquote:border-gray-300 prose-blockquote:text-gray-600 prose-blockquote:italic
          ">
            {renderContentWithImages()}
          </article>
        </div>
      </div>
    </div>
  );
}
