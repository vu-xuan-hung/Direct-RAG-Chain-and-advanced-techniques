import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import { Send, FileText, Bot, User, Search, MoreVertical, MessageSquare, Plus, Trash2 } from 'lucide-react';

const QUICK_PROMPTS = [
  "Đi muộn 5 phút bị phạt bao nhiêu?",
  "Thủ tục xin nghỉ ốm",
  "Quy định mặc đồng phục",
  "Thời gian làm việc buổi sáng",
  "Chính sách thai sản"
];

const DEFAULT_MESSAGES = [
  {
    id: 1,
    type: 'system',
    text: 'Cuộc hội thoại được bảo mật theo quy định của FPT.'
  },
  {
    id: 2,
    type: 'ai',
    text: 'Chào bạn! Mình là FPT HR Assistant. Bạn cần hỗ trợ thông tin gì về quy định, chính sách, giờ giấc hay lương thưởng của FPT?',
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
];

function App() {
  const getSavedSessions = () => {
    const saved = localStorage.getItem('chatSessions');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && parsed.length > 0) return parsed;
      } catch (e) {
        console.error("Error parsing localstorage", e);
      }
    }
    return null;
  };

  const initialSessions = getSavedSessions() || [{
    id: Date.now(),
    title: 'Cuộc trò chuyện mới',
    messages: DEFAULT_MESSAGES
  }];

  const [sessions, setSessions] = useState(initialSessions);
  const [currentSessionId, setCurrentSessionId] = useState(initialSessions[0].id);

  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [sessions, currentSessionId, isTyping]);

  // Persist to localStorage whenever sessions change
  useEffect(() => {
    localStorage.setItem('chatSessions', JSON.stringify(sessions));
  }, [sessions]);

  const currentSession = sessions.find(s => s.id === currentSessionId) || sessions[0];
  const messages = currentSession.messages;

  const handleNewChat = () => {
    const newId = Date.now();
    setSessions(prev => [{
      id: newId,
      title: 'Cuộc trò chuyện mới',
      messages: DEFAULT_MESSAGES
    }, ...prev]);
    setCurrentSessionId(newId);
  };

  const handleDeleteChat = (e, id) => {
    e.stopPropagation();
    const remaining = sessions.filter(s => s.id !== id);
    if (remaining.length === 0) {
      const newId = Date.now();
      setSessions([{ id: newId, title: 'Cuộc trò chuyện mới', messages: DEFAULT_MESSAGES }]);
      setCurrentSessionId(newId);
    } else {
      setSessions(remaining);
      if (currentSessionId === id) {
        setCurrentSessionId(remaining[0].id);
      }
    }
  };

  const handleSend = async (text) => {
    const finalQuery = text.trim();
    if (!finalQuery) return;

    // Tính toán tiêu đề nếu đây là câu hỏi đầu tiên
    let newTitle = currentSession.title;
    if (newTitle === 'Cuộc trò chuyện mới') {
      newTitle = finalQuery.length > 20 ? finalQuery.slice(0, 20) + '...' : finalQuery;
    }

    const newUserMsg = {
      id: Date.now(),
      type: 'user',
      text: finalQuery,
      timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
    };
    
    // Lưu ngay tin nhắn user vào session
    setSessions(prev => prev.map(s => {
      if (s.id === currentSessionId) {
        return { ...s, title: newTitle, messages: [...s.messages, newUserMsg] };
      }
      return s;
    }));

    setInputValue('');
    setIsTyping(true);
    setIsSearching(true); 

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: finalQuery })
      });
      
      setIsSearching(false);

      if (!response.ok) {
        throw new Error('API Error');
      }

      const data = await response.json();
      
      const newAiMsg = {
        id: Date.now() + 1,
        type: 'ai',
        text: data.answer || "Xin lỗi, mình không thể tự hiểu câu trả lời.",
        timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
      };

      setSessions(prev => Object.assign([], prev).map(s => {
        if (s.id === currentSessionId) {
            return { ...s, messages: [...s.messages, newAiMsg] };
        }
        return s;
      }));

    } catch (error) {
      console.error('Error fetching chat response:', error);
      setIsSearching(false);
      
      const errorMsg = {
        id: Date.now() + 1,
        type: 'ai',
        text: "Xin lỗi, máy chủ hiện không phản hồi. Vui lòng thử lại sau.",
        timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
      };

      setSessions(prev => Object.assign([], prev).map(s => {
        if (s.id === currentSessionId) {
            return { ...s, messages: [...s.messages, errorMsg] };
        }
        return s;
      }));

    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(inputValue);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="fpt-logo-placeholder">FPT</div>
          <div className="sidebar-title">
            <h2>HR Assistant</h2>
            <p>Hỗ trợ Nhân sự</p>
          </div>
        </div>

        <button className="new-chat-btn" onClick={handleNewChat}>
          <Plus size={18} />
          <span>Đoạn chat mới</span>
        </button>

        <div className="history-list">
          {sessions.map(session => (
            <div 
              key={session.id} 
              className={`history-item ${session.id === currentSessionId ? 'active' : ''}`}
              onClick={() => setCurrentSessionId(session.id)}
            >
              <div className="history-item-content">
                <MessageSquare size={18} style={{ flexShrink: 0 }} />
                <span className="truncate-text">{session.title}</span>
              </div>
              <button 
                className="delete-chat-btn" 
                onClick={(e) => handleDeleteChat(e, session.id)}
                title="Xóa đoạn chat này"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="main-chat">
        <div className="chat-header">
          <div>
            <h3 style={{ color: 'var(--fpt-blue)', margin: 0, fontSize: '1.1rem' }}>FPT HR Assistant</h3>
            <div className="header-status">
              <div className="status-dot"></div>
              <span style={{ fontSize: '0.8rem', color: 'var(--fpt-gray-500)' }}>Sẵn sàng (Powered by RAG)</span>
            </div>
          </div>
          <button className="action-btn">
            <MoreVertical size={20} />
          </button>
        </div>

        <div className="chat-messages">
          {messages.map((msg) => {
            if (msg.type === 'system') {
              return <div key={msg.id} className="system-message">{msg.text}</div>
            }

            return (
              <div key={msg.id} className={`message-wrapper ${msg.type}`}>
                <div className={`avatar ${msg.type}-avatar`}>
                  {msg.type === 'ai' ? <Bot size={22} /> : <User size={22} />}
                </div>
                <div className="message-content">
                  <div className="message">
                    {formatText(msg.text)}
                  </div>
                  <span className="message-time">{msg.timestamp}</span>
                </div>
              </div>
            );
          })}

          {isSearching && (
            <div className="message-wrapper ai">
              <div className="avatar ai-avatar">
                <Search size={18} />
              </div>
              <div className="message-content">
                <div className="message" style={{ fontStyle: 'italic', color: 'var(--fpt-gray-500)' }}>
                  Đang tìm kiếm thông tin quy định trong CSDL chính sách...
                </div>
              </div>
            </div>
          )}

          {isTyping && !isSearching && (
            <div className="message-wrapper ai">
              <div className="avatar ai-avatar">
                <Bot size={22} />
              </div>
              <div className="message-content">
                <div className="message">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="chat-input-container">
          <div className="quick-prompts">
            {QUICK_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                className="prompt-btn"
                onClick={() => handleSend(prompt)}
                disabled={isTyping}
              >
                {prompt}
              </button>
            ))}
          </div>

          <div className="input-box">
            <button className="action-btn" title="Đính kèm tệp">
              <FileText size={20} />
            </button>
            <textarea
              placeholder="Nhập câu hỏi về chính sách..."
              rows="1"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isTyping}
            />
            <button
              className="send-btn"
              onClick={() => handleSend(inputValue)}
              disabled={!inputValue.trim() || isTyping}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Hàm format text đơn giản hỗ trợ xuống dòng
function formatText(text) {
  return text.split('\n').map((str, index) => (
    <React.Fragment key={index}>
      {str}
      {index < text.split('\n').length - 1 && <br />}
    </React.Fragment>
  ));
}

export default App;
