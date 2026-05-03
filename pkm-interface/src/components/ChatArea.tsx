import { useState, useRef, useEffect } from 'react';
import { Bot, User, Copy, ThumbsUp, ThumbsDown, MoreHorizontal, Image, Sparkles, FileText, Search } from 'lucide-react';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  images?: string[];
  timestamp: Date;
  liked?: boolean;
  disliked?: boolean;
}

interface ChatAreaProps {
  messages: Message[];
  onImageUpload?: (images: string[]) => void;
  mode?: 'store' | 'query';
}

export default function ChatArea({ messages, onImageUpload, mode = 'store' }: ChatAreaProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleCopy = async (content: string, id: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleFeedback = (id: string, type: 'like' | 'dislike') => {
    // 这里可以添加反馈逻辑
    console.log(`Feedback for message ${id}:`, type);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* 顶部栏 */}
      <div className="h-14 px-6 border-b border-gray-200 flex items-center justify-between bg-white">
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
            mode === 'store' ? 'bg-gray-800' : 'bg-blue-600'
          }`}>
            {mode === 'store' ? (
              <FileText className="w-4 h-4 text-white" />
            ) : (
              <Search className="w-4 h-4 text-white" />
            )}
          </div>
          <div>
            <h2 className="font-medium text-sm text-gray-800">
              {mode === 'store' ? '笔记记录' : '知识问答'}
            </h2>
            <p className="text-xs text-gray-400">
              {mode === 'store' ? '记录灵感，整理知识' : '基于你的笔记内容回答问题'}
            </p>
          </div>
        </div>
        <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
          <MoreHorizontal className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto px-6 py-6 bg-gray-50">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <div className={`w-20 h-20 rounded-2xl bg-white shadow-sm flex items-center justify-center mb-6 ${
              mode === 'store' ? 'text-gray-800' : 'text-blue-600'
            }`}>
              {mode === 'store' ? (
                <FileText className="w-10 h-10" />
              ) : (
                <Search className="w-10 h-10" />
              )}
            </div>
            <h2 className="text-2xl font-semibold mb-3 text-gray-800">
              {mode === 'store' ? '开始记录' : '知识问答助手'}
            </h2>
            <p className="text-gray-400 max-w-md mb-8">
              {mode === 'store'
                ? '上传截图或输入文字，将内容保存到你的知识库中。'
                : '我可以帮你从知识库中寻找答案，解答你的问题。'}
            </p>
            {mode === 'store' ? (
              <div className="grid grid-cols-2 gap-4 max-w-lg">
                <div className="p-4 rounded-xl bg-white border border-gray-200 text-left shadow-sm">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center mb-3">
                    <Image className="w-5 h-5 text-gray-600" />
                  </div>
                  <h3 className="font-medium text-sm mb-1 text-gray-800">截图收藏</h3>
                  <p className="text-xs text-gray-400">上传截图，快速保存重要信息</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gray-200 text-left shadow-sm">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center mb-3">
                    <FileText className="w-5 h-5 text-gray-600" />
                  </div>
                  <h3 className="font-medium text-sm mb-1 text-gray-800">文本记录</h3>
                  <p className="text-xs text-gray-400">输入文字，保存灵感心得</p>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4 max-w-lg">
                <div className="p-4 rounded-xl bg-white border border-gray-200 text-left shadow-sm">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center mb-3">
                    <Search className="w-5 h-5 text-gray-600" />
                  </div>
                  <h3 className="font-medium text-sm mb-1 text-gray-800">知识检索</h3>
                  <p className="text-xs text-gray-400">用关键词找到相关笔记</p>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gray-200 text-left shadow-sm">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center mb-3">
                    <Sparkles className="w-5 h-5 text-gray-600" />
                  </div>
                  <h3 className="font-medium text-sm mb-1 text-gray-800">智能总结</h3>
                  <p className="text-xs text-gray-400">帮你总结笔记要点</p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 message-enter ${
                  message.role === 'user' ? 'flex-row-reverse' : ''
                }`}
              >
                {/* 头像 */}
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user'
                      ? 'bg-gray-800'
                      : 'bg-gray-200'
                  }`}
                >
                  {message.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-gray-600" />
                  )}
                </div>

                {/* 消息内容 */}
                <div
                  className={`flex-1 ${
                    message.role === 'user' ? 'items-end' : 'items-start'
                  } flex flex-col gap-2`}
                >
                  {/* 图片预览 */}
                  {message.images && message.images.length > 0 && (
                    <div className="flex gap-2 flex-wrap">
                      {message.images.map((img, idx) => (
                        <div
                          key={idx}
                          className="relative group rounded-xl overflow-hidden border border-gray-200"
                        >
                          <img
                            src={img}
                            alt={`上传图片 ${idx + 1}`}
                            className="max-w-[300px] max-h-[200px] object-cover"
                          />
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 文本内容 */}
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-white text-gray-800 rounded-tr-md shadow-sm'
                        : 'bg-white text-gray-800 rounded-tl-md shadow-sm'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap text-gray-800">
                      {message.content}
                    </p>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex items-center gap-2">
                    {message.role === 'assistant' && (
                      <>
                        <button
                          onClick={() => handleCopy(message.content, message.id)}
                          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors group"
                          title="复制"
                        >
                          {copiedId === message.id ? (
                            <span className="text-xs text-gray-600">已复制</span>
                          ) : (
                            <Copy className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
                          )}
                        </button>
                        <button
                          onClick={() => handleFeedback(message.id, 'like')}
                          className={`p-1.5 rounded-lg hover:bg-gray-100 transition-colors ${
                            message.liked ? 'text-gray-800' : ''
                          }`}
                          title="有帮助"
                        >
                          <ThumbsUp
                            className={`w-4 h-4 ${
                              message.liked
                                ? 'fill-gray-800 text-gray-800'
                                : 'text-gray-400'
                            }`}
                          />
                        </button>
                        <button
                          onClick={() => handleFeedback(message.id, 'dislike')}
                          className={`p-1.5 rounded-lg hover:bg-gray-100 transition-colors ${
                            message.disliked ? 'text-red-500' : ''
                          }`}
                          title="不够准确"
                        >
                          <ThumbsDown
                            className={`w-4 h-4 ${
                              message.disliked
                                ? 'fill-red-500 text-red-500'
                                : 'text-gray-400'
                            }`}
                          />
                        </button>
                      </>
                    )}
                    <span className="text-xs text-gray-400">
                      {message.timestamp.toLocaleTimeString('zh-CN', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}