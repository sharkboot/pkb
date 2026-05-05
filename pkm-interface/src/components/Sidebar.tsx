import { useState, useEffect } from 'react';
import {
  Search,
  Plus,
  Settings,
  FolderOpen,
  Clock,
  Star,
  Trash2,
  Sparkles,
  ChevronDown,
  ChevronRight,
  FileText,
  Image,
  File,
  Loader2,
} from 'lucide-react';
import { listKnowledge, Knowledge } from '@/lib/api';

interface SidebarProps {
  viewMode: 'chat' | 'notes';
  onViewModeChange: (mode: 'chat' | 'notes') => void;
}

interface Category {
  id: string;
  name: string;
  icon: React.ReactNode;
  count: number;
}

export default function Sidebar({ viewMode, onViewModeChange }: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoriesExpanded, setCategoriesExpanded] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string | null>('all');
  const [knowledgeItems, setKnowledgeItems] = useState<Knowledge[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 加载知识列表
  useEffect(() => {
    loadKnowledge();
  }, []);

  const loadKnowledge = async () => {
    setIsLoading(true);
    try {
      const result = await listKnowledge({ pageSize: 50 });
      setKnowledgeItems(result.list);
    } catch (error) {
      console.error('Failed to load knowledge:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const categories: Category[] = [
    { id: 'all', name: '全部笔记', icon: <FolderOpen className="w-4 h-4" />, count: knowledgeItems.length },
    { id: 'recent', name: '最近', icon: <Clock className="w-4 h-4" />, count: 8 },
    { id: 'starred', name: '收藏', icon: <Star className="w-4 h-4" />, count: 5 },
    { id: 'trash', name: '回收站', icon: <Trash2 className="w-4 h-4" />, count: 3 },
  ];

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'text':
        return <FileText className="w-4 h-4 text-gray-500" />;
      case 'image':
        return <Image className="w-4 h-4 text-gray-500" />;
      case 'file':
        return <File className="w-4 h-4 text-gray-500" />;
      default:
        return <FileText className="w-4 h-4 text-gray-500" />;
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

  return (
    <div className="w-72 h-full bg-white border-r border-gray-200 flex flex-col">
      {/* 顶部 Logo 区域 */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gray-800 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-lg text-gray-800">我的知识库</h1>
            <p className="text-xs text-gray-400">Personal KM</p>
          </div>
        </div>

        {/* 搜索框 */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索笔记..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 transition-all text-gray-800 placeholder:text-gray-400"
          />
        </div>
      </div>

      {/* 新建按钮 */}
      <div className="p-3">
        <button className="w-full py-2.5 px-4 bg-gray-800 text-white rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-gray-900 transition-colors">
          <Plus className="w-4 h-4" />
          新建笔记
        </button>
      </div>

      {/* 分类列表 */}
      <div className="flex-1 overflow-y-auto px-3">
        <div
          className="flex items-center justify-between py-2 cursor-pointer select-none"
          onClick={() => setCategoriesExpanded(!categoriesExpanded)}
        >
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">快速访问</span>
          {categoriesExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-400" />
          )}
        </div>

        {categoriesExpanded && (
          <div className="space-y-1">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedCategory === category.id
                    ? 'bg-gray-100 text-gray-800 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {category.icon}
                <span className="flex-1 text-left">{category.name}</span>
                <span className="text-xs text-gray-400">{category.count}</span>
              </button>
            ))}
          </div>
        )}

        {/* 最近笔记列表 */}
        <div className="mt-6">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">最近笔记</span>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
            </div>
          ) : (
            <div className="mt-2 space-y-1">
              {knowledgeItems.slice(0, 10).map((item) => (
                <button
                  key={item.id}
                  className="w-full flex items-start gap-3 px-3 py-2.5 rounded-lg text-sm hover:bg-gray-50 transition-colors group"
                >
                  <div className="mt-0.5">
                    {getTypeIcon(item.source || 'text')}
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate text-gray-800">
                        {item.title || '无标题'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 truncate mt-0.5">
                      {formatDate(item.updated_at)}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 底部设置 */}
      <div className="p-3 border-t border-gray-200">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-50 transition-colors">
          <Settings className="w-4 h-4" />
          <span>设置</span>
        </button>
      </div>
    </div>
  );
}
