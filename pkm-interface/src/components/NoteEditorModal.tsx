import { useEffect, useState } from 'react';
import { X, Loader2, Tag } from 'lucide-react';
import { Knowledge, collectContent, updateKnowledge } from '@/lib/api';

interface NoteEditorModalProps {
  mode: 'create' | 'edit';
  note?: Knowledge | null;
  onClose: () => void;
  onSaved: (note: Knowledge) => void;
}

export default function NoteEditorModal({ mode, note, onClose, onSaved }: NoteEditorModalProps) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [category, setCategory] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (mode === 'edit' && note) {
      setTitle(note.title || '');
      setContent(note.content || '');
      setTags(note.tags || []);
      setCategory(note.category || '');
    }
  }, [mode, note]);

  const addTag = () => {
    const value = tagInput.trim();
    if (!value) return;
    if (!tags.includes(value)) {
      setTags((prev) => [...prev, value]);
    }
    setTagInput('');
  };

  const removeTag = (target: string) => {
    setTags((prev) => prev.filter((item) => item !== target));
  };

  const handleSave = async () => {
    if (!title.trim() && !content.trim()) {
      setErrorMessage('请输入标题或内容');
      return;
    }

    setIsSaving(true);
    setErrorMessage('');

    try {
      let savedNote: Knowledge;

      if (mode === 'create') {
        const payload = [
          title.trim() ? `# ${title.trim()}\n\n` : '',
          content.trim(),
        ]
          .filter(Boolean)
          .join('');

        savedNote = await collectContent(payload, [], 'manual');
        savedNote = {
          ...savedNote,
          title: savedNote.title || title.trim(),
          tags: savedNote.tags?.length ? savedNote.tags : tags,
          category: savedNote.category || category.trim() || undefined,
        };
      } else if (note) {
        savedNote = await updateKnowledge(note.id, {
          title: title.trim() || note.title,
          content: content.trim(),
          tags,
          category: category.trim() || undefined,
        });
      } else {
        throw new Error('未找到可编辑的笔记');
      }

      onSaved(savedNote);
      onClose();
    } catch (error) {
      console.error('Failed to save note:', error);
      setErrorMessage(error instanceof Error ? error.message : '保存失败，请稍后重试');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {mode === 'create' ? '新建笔记' : '编辑笔记'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {mode === 'create' ? '快速记录一个新的知识点' : '更新笔记内容与标签'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {errorMessage && (
            <div className="rounded-lg border border-red-200 bg-red-50 text-sm text-red-600 px-4 py-3">
              {errorMessage}
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">标题</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="为笔记起个名字"
              className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-gray-200"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">内容</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="写下你的笔记内容..."
              className="w-full min-h-[200px] max-h-[340px] resize-y rounded-xl border border-gray-200 px-4 py-3 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-gray-200"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">标签</label>
            <div className="flex gap-2">
              <input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ',') {
                    e.preventDefault();
                    addTag();
                  }
                }}
                placeholder="输入标签后回车"
                className="flex-1 rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-200"
              />
              <button
                type="button"
                onClick={addTag}
                className="px-4 py-2 rounded-xl border border-gray-200 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                添加
              </button>
            </div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-1">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-xs"
                  >
                    <Tag className="w-3 h-3" />
                    {tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      className="ml-1 text-gray-400 hover:text-gray-600"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">分类（可选）</label>
            <input
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="例如：工作、学习、灵感"
              className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-gray-200"
            />
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
          <span className="text-xs text-gray-400">
            {mode === 'create' ? '保存后可在笔记列表和侧栏最近笔记中看到' : '更新后会立即刷新笔记内容'}
          </span>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-gray-200 text-sm text-gray-600 hover:bg-white transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-60"
            >
              {isSaving && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === 'create' ? '保存笔记' : '保存修改'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
