import { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea, { Message } from './components/ChatArea';
import InputArea from './components/InputArea';
import { Moon, Sun, Menu, FileText, Search } from 'lucide-react';
import { collectContent, listKnowledge } from './lib/api';

type Mode = 'store' | 'query';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [mode, setMode] = useState<Mode>('store');
  const [isLoading, setIsLoading] = useState(false);

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
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        // 问答模式：搜索相关知识并返回
        const result = await listKnowledge({ keyword: content, pageSize: 5 });
        if (result.list.length === 0) {
          const assistantMessage: Message = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: '抱歉，我在知识库中没有找到相关内容。你可以先记录这条信息，稍后再来询问。',
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        } else {
          const relevantKnowledge = result.list
            .slice(0, 3)
            .map((k) => `【${k.title || '无标题'}】\n${k.summary || k.content.slice(0, 200)}`)
            .join('\n\n');
          const assistantMessage: Message = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: `根据你的知识库，我找到了以下相关内容：\n\n${relevantKnowledge}\n\n如需更详细的答案，请告诉我具体想了解哪方面的内容。`,
            timestamp: new Date(),
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
        <Sidebar />
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
        {/* 移动端顶部栏 */}
        <div className="lg:hidden h-14 px-4 border-b border-gray-200 flex items-center justify-between gap-2 bg-white">
          {/* 移动端模式切换 Tab */}
          <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg flex-1">
            <button
              onClick={() => setMode('store')}
              className={`flex-1 flex items-center justify-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                mode === 'store'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-gray-500'
              }`}
            >
              <FileText className="w-3 h-3" />
              记录
            </button>
            <button
              onClick={() => setMode('query')}
              className={`flex-1 flex items-center justify-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                mode === 'query'
                  ? 'bg-white text-gray-800 shadow-sm'
                  : 'text-gray-500'
              }`}
            >
              <Search className="w-3 h-3" />
              问答
            </button>
          </div>

          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title={isDarkMode ? '切换到亮色模式' : '切换到暗色模式'}
          >
            {isDarkMode ? (
              <Sun className="w-4 h-4 text-amber-500" />
            ) : (
              <Moon className="w-4 h-4 text-gray-400" />
            )}
          </button>
        </div>

        {/* 桌面端顶部栏 */}
        <div className="hidden lg:flex h-14 px-6 border-b border-gray-200 items-center justify-between gap-2 bg-white">
          {/* 模式切换 Tab */}
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

        {/* 聊天区域 */}
        <ChatArea messages={messages} mode={mode} />

        {/* 输入区域 */}
        <InputArea onSend={handleSend} mode={mode} disabled={isLoading} />
      </div>
    </div>
  );
}

export default App;
