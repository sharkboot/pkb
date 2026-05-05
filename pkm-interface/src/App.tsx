import { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea, { Message } from './components/ChatArea';
import InputArea from './components/InputArea';
import NotesList from './components/NotesList';
import NoteModal from './components/NoteModal';
import { Moon, Sun, Menu, FileText, Search, BookOpen } from 'lucide-react';
import { collectContent, smartSearch, Knowledge } from './lib/api';

type ViewMode = 'chat' | 'notes';
type Mode = 'store' | 'query';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('chat');
  const [mode, setMode] = useState<Mode>('store');
  const [isLoading, setIsLoading] = useState(false);

  // 笔记弹窗
  const [selectedNote, setSelectedNote] = useState<Knowledge | null>(null);

  const handleSend = useCallback(async (content: string, images: string[]) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      images: images.length > 0 ? images : undefined,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      if (mode === 'store') {
        // 存储模式：调用内容收集 API
        const sourceType = images.length > 0 ? 'screenshot' : 'text';
        const result = await collectContent(content, images, sourceType);
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: result.summary || '已成功保存到知识库',
          timestamp: new Date(),
          relatedNotes: [result],
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        // 问答模式：智能搜索
        const result = await smartSearch(content);

        if (result.results.length === 0) {
          const assistantMessage: Message = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: '抱歉，我在知识库中没有找到相关内容。你可以先记录这条信息，稍后再来询问。',
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        } else {
          const responseText = result.reason
            ? `根据分析：${result.reason}\n\n找到 ${result.total} 条相关笔记：`
            : `找到 ${result.total} 条相关笔记：`;

          const relevantKnowledge = result.results
            .map((k) => `【${k.title || '无标题'}】\n${k.summary || k.content.slice(0, 200)}`)
            .join('\n\n');

          const assistantMessage: Message = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: `${responseText}\n\n${relevantKnowledge}\n\n如需更详细的答案，请告诉我具体想了解哪方面的内容。`,
            timestamp: new Date(),
            relatedNotes: result.results,
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }
      }
    } catch (error) {
      console.error('API Error:', error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: error instanceof Error ? error.message : '处理失败，请稍后重试',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [mode]);

  const handleViewNote = useCallback((note: Knowledge) => {
    setSelectedNote(note);
  }, []);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <div className="h-screen flex bg-gray-100 overflow-hidden">
      {/* 移动端菜单按钮 */}
      <button
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white border border-gray-200 shadow-md"
      >
        <Menu className="w-5 h-5 text-gray-600" />
      </button>

      {/* 侧边栏 */}
      <div
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          transform transition-transform duration-300 ease-in-out
          lg:transform-none
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <Sidebar
          viewMode={viewMode}
          onViewModeChange={setViewMode}
        />
      </div>

      {/* 移动端遮罩 */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* 主内容区 */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* 桌面端顶部栏 */}
        <div className="hidden lg:flex h-14 px-6 border-b border-gray-200 items-center justify-between gap-4 bg-white">
          {/* 视图切换 */}
          <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
            <button
              onClick={() => setViewMode('chat')}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'chat'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <FileText className="w-4 h-4" />
              聊天
            </button>
            <button
              onClick={() => setViewMode('notes')}
              className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'notes'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              全部笔记
            </button>
          </div>

          {viewMode === 'chat' && (
            <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
              <button
                onClick={() => setMode('store')}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  mode === 'store'
                    ? 'bg-white text-gray-800 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <FileText className="w-4 h-4" />
                记录模式
              </button>
              <button
                onClick={() => setMode('query')}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  mode === 'query'
                    ? 'bg-white text-gray-800 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Search className="w-4 h-4" />
                问答模式
              </button>
            </div>
          )}

          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title={isDarkMode ? '切换到亮色模式' : '切换到暗色模式'}
          >
            {isDarkMode ? (
              <Sun className="w-5 h-5 text-amber-500" />
            ) : (
              <Moon className="w-5 h-5 text-gray-400" />
            )}
          </button>
        </div>

        {/* 移动端顶部栏 */}
        <div className="lg:hidden h-14 px-4 border-b border-gray-200 flex items-center justify-between gap-2 bg-white">
          <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg flex-1">
            <button
              onClick={() => setViewMode('chat')}
              className={`flex-1 flex items-center justify-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                viewMode === 'chat'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-gray-500'
              }`}
            >
              <FileText className="w-3 h-3" />
              聊天
            </button>
            <button
              onClick={() => setViewMode('notes')}
              className={`flex-1 flex items-center justify-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                viewMode === 'notes'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-gray-500'
              }`}
            >
              <BookOpen className="w-3 h-3" />
              笔记
            </button>
          </div>

          {viewMode === 'chat' && (
            <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
              <button
                onClick={() => setMode('store')}
                className={`px-2 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  mode === 'store'
                    ? 'bg-white text-gray-800 shadow-sm'
                    : 'text-gray-500'
                }`}
              >
                记录
              </button>
              <button
                onClick={() => setMode('query')}
                className={`px-2 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  mode === 'query'
                    ? 'bg-white text-gray-800 shadow-sm'
                    : 'text-gray-500'
                }`}
              >
                问答
              </button>
            </div>
          )}

          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {isDarkMode ? (
              <Sun className="w-4 h-4 text-amber-500" />
            ) : (
              <Moon className="w-4 h-4 text-gray-400" />
            )}
          </button>
        </div>

        {/* 内容区 */}
        {viewMode === 'chat' ? (
          <>
            <ChatArea
              messages={messages}
              mode={mode}
              onViewNote={handleViewNote}
            />
            <InputArea onSend={handleSend} mode={mode} disabled={isLoading} />
          </>
        ) : (
          <NotesList onViewNote={handleViewNote} />
        )}
      </div>

      {/* 笔记详情弹窗 */}
      {selectedNote && (
        <NoteModal
          note={selectedNote}
          onClose={() => setSelectedNote(null)}
        />
      )}
    </div>
  );
}

export default App;
