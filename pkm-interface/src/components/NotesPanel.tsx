import { useState, useEffect } from 'react';
import {
  X,
  Search,
  FileText,
  Image,
  ExternalLink,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { Knowledge, listKnowledge, getCatalog } from '@/lib/api';

interface CatalogEntry {
  id: string;
  title: string;
  summary?: string;
  contentPreview: string;
  tags: string[];
  category?: string;
  filePath: string;
  status: string;
  updatedAt: string;
}

interface NotesPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onViewNote: (note: Knowledge) => void;
}

export default function NotesPanel({ isOpen, onClose, onViewNote }: NotesPanelProps) {
  const [catalogEntries, setCatalogEntries] = useState<CatalogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNote, setSelectedNote] = useState<Knowledge | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadCatalog();
    }
  }, [isOpen]);

  const loadCatalog = async () => {
    setIsLoading(true);
    try {
      const result = await getCatalog({ keyword: searchQuery || undefined, limit: 100 });
      setCatalogEntries(result.entries);
    } catch (error) {
      console.error('Failed to load catalog:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = () => {
    loadCatalog();
  };

  const handleViewNote = async (entry: CatalogEntry) => {
    try {
      const note = await import('@/lib/api').then(m => m.getKnowledge(entry.id));
      onViewNote(note);
    } catch (error) {
      console.error('Failed to load note:', error);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffHours < 1) return '刚刚';
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays === 1) return '昨天';
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  if (!isOpen) return null;

  return (
    <>
      {/* 遮罩 */}
      <div
        className="fixed inset-0 bg-black/30 z-40"
        onClick={onClose}
      />

      {/* 面板 */}
      <div className="fixed right-0 top-0 bottom-0 w-[480px] bg-white shadow-2xl z-50 flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">笔记库</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={loadCatalog}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              title="刷新"
            >
              <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* 搜索框 */}
        <div className="p-4 border-b border-gray-100">
          <div className="relative flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索笔记..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full pl-10 pr-4 py-2 bg-gray-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 text-gray-800 placeholder:text-gray-400"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-gray-800 text-white rounded-lg text-sm font-medium hover:bg-gray-900 transition-colors"
            >
              搜索
            </button>
          </div>
        </div>

        {/* 笔记列表 */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
            </div>
          ) : catalogEntries.length === 0 ? (
            <div className="text-center py-12 text-gray-500 text-sm">
              暂无笔记
            </div>
          ) : (
            <div className="space-y-3">
              {catalogEntries.map((entry) => (
                <div
                  key={entry.id}
                  className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer group"
                  onClick={() => handleViewNote(entry as any)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate">
                        {entry.title || '无标题'}
                      </h3>
                      {entry.summary && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {entry.summary}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-gray-400">
                          {formatDate(entry.updatedAt)}
                        </span>
                        {entry.tags && entry.tags.slice(0, 2).map((tag) => (
                          <span
                            key={tag}
                            className="px-1.5 py-0.5 bg-gray-200 text-gray-600 text-xs rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                    <button
                      className="p-1.5 rounded-lg hover:bg-gray-200 transition-colors opacity-0 group-hover:opacity-100"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewNote(entry as any);
                      }}
                    >
                      <ExternalLink className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
