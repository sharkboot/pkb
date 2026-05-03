import { useState, useRef, useCallback, useEffect } from 'react';
import { Send, Image, X, Loader2 } from 'lucide-react';

interface InputAreaProps {
  onSend: (content: string, images: string[]) => void;
  disabled?: boolean;
  mode?: 'store' | 'query';
}

export default function InputArea({ onSend, disabled, mode = 'store' }: InputAreaProps) {
  const [input, setInput] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const processFiles = (files: File[]) => {
    files
      .filter((file) => file.type.startsWith('image/'))
      .forEach((file) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const result = e.target?.result as string;
          setImages((prev) => [...prev, result]);
        };
        reader.readAsDataURL(file);
      });
  };

  // 处理 Ctrl+V 粘贴
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      const files: File[] = [];
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) files.push(file);
        }
      }
      if (files.length > 0) {
        e.preventDefault();
        processFiles(files);
      }
    };
    document.addEventListener('paste', handlePaste);
    return () => document.removeEventListener('paste', handlePaste);
  }, []);

  const handleSubmit = useCallback(async () => {
    if ((!input.trim() && images.length === 0) || disabled || isSending) return;

    setIsSending(true);
    try {
      await onSend(input.trim(), images);
      setInput('');
      setImages([]);
    } finally {
      setIsSending(false);
    }
  }, [input, images, disabled, isSending, onSend]);

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="border-t border-gray-200 bg-white px-6 py-4">
      <div className="mx-auto max-w-4xl">
        {/* 图片预览区 */}
        {images.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {images.map((img, idx) => (
              <div key={idx} className="relative group">
                <img
                  src={img}
                  alt={`preview-${idx}`}
                  className="w-16 h-16 rounded-lg object-cover border"
                />
                <button
                  onClick={() => removeImage(idx)}
                  className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-black/70 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* 输入区 */}
        <div
          className={`rounded-xl border transition-all ${
            isDragging ? 'border-blue-400 ring-2 ring-blue-100' : 'border-gray-200'
          }`}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            processFiles(Array.from(e.dataTransfer.files));
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              mode === 'store'
                ? '输入随手记录、知识点，或直接粘贴截图...'
                : '输入问题，让我从知识库中寻找答案...'
            }
            className="w-full min-h-[80px] max-h-[160px] resize-none rounded-t-xl border-0 p-4 text-sm focus:outline-none focus:ring-0"
            disabled={disabled || isSending}
          />

          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <div className="flex items-center gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                title="上传图片"
              >
                <Image className="w-5 h-5 text-gray-500" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={(e) => {
                  if (e.target.files) processFiles(Array.from(e.target.files));
                }}
              />
              <span className="text-xs text-gray-400">支持 Ctrl+V 粘贴截图</span>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400">Enter 发送 · Shift+Enter 换行</span>
              <button
                onClick={handleSubmit}
                disabled={(!input.trim() && images.length === 0) || disabled || isSending}
                className="px-5 py-2 rounded-lg bg-gray-900 text-white text-sm font-medium disabled:opacity-50 hover:bg-gray-800 transition-colors"
              >
                {isSending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : mode === 'store' ? (
                  '保存到知识库'
                ) : (
                  <>
                    <Send className="w-4 h-4 inline-block mr-1" />
                    提问
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
