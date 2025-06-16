"use client";

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  MessageCircle, 
  Send,
  User,
  Bot,
  Sparkles,
  Clock,
  BookOpen,
  Share2,
  Copy,
  ThumbsUp,
  ThumbsDown,
  MoreVertical,
  Plus,
  Search
} from 'lucide-react';

// Datos de ejemplo - en producción vendrían de la base de datos
const availableAuthors = [
  {
    id: 1,
    name: 'Gabriel García Márquez',
    avatar: 'GGM',
    color: 'bg-blue-500',
    books: 15,
    lastActive: '2 min',
    specialty: 'Realismo Mágico',
    description: 'Maestro del realismo mágico latinoamericano',
  },
  {
    id: 2,
    name: 'Jorge Luis Borges',
    avatar: 'JLB',
    color: 'bg-purple-500',
    books: 23,
    lastActive: '5 min',
    specialty: 'Cuentos Fantásticos',
    description: 'Escritor de laberintos literarios y metafísica',
  },
  {
    id: 3,
    name: 'Julio Cortázar',
    avatar: 'JC',
    color: 'bg-green-500',
    books: 18,
    lastActive: '1 hora',
    specialty: 'Literatura Experimental',
    description: 'Innovador de la narrativa contemporánea',
  },
  {
    id: 4,
    name: 'Isabel Allende',
    avatar: 'IA',
    color: 'bg-red-500',
    books: 12,
    lastActive: '3 horas',
    specialty: 'Novela Histórica',
    description: 'Narradora de historias familiares épicas',
  },
];

const conversationHistory = [
  {
    id: 1,
    type: 'user' as const,
    content: '¿Podrías explicarme el concepto de realismo mágico en tus obras?',
    timestamp: '14:30',
  },
  {
    id: 2,
    type: 'bot' as const,
    content: 'El realismo mágico es una técnica narrativa donde lo extraordinario se presenta como algo natural y cotidiano. En mis obras como "Cien años de soledad", los elementos fantásticos conviven armoniosamente con la realidad, creando una atmósfera donde la magia es parte integral de la vida diaria. No se trata de escapar de la realidad, sino de mostrar que la realidad latinoamericana contiene elementos que pueden parecer mágicos para otras culturas.',
    timestamp: '14:31',
    author: 'Gabriel García Márquez',
  },
  {
    id: 3,
    type: 'user' as const,
    content: '¿Cómo puedo aplicar esta técnica en mis propios escritos?',
    timestamp: '14:32',
  },
  {
    id: 4,
    type: 'bot' as const,
    content: 'Para aplicar el realismo mágico en tus escritos, te sugiero: 1) Observa tu entorno con ojos nuevos - busca lo extraordinario en lo cotidiano. 2) No expliques los elementos mágicos, preséntalos como hechos naturales. 3) Mantén un tono narrativo sereno y objetivo, incluso ante lo fantástico. 4) Conecta lo mágico con las emociones y experiencias humanas profundas. 5) Usa la técnica para explorar temas sociales y culturales de tu contexto. Recuerda: el realismo mágico no es fantasía pura, sino una forma de revelar verdades más profundas sobre la condición humana.',
    timestamp: '14:33',
    author: 'Gabriel García Márquez',
  },
];

export default function ChatbotPage() {
  const { t } = useTranslation();
  const [selectedAuthor, setSelectedAuthor] = useState(availableAuthors[0]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const newMessage: Message = {
      id: Date.now(),
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputText('');

    // TODO: Implement AI response
    setTimeout(() => {
      const botResponse: Message = {
        id: Date.now() + 1,
        text: "I'm still learning! This feature will be available soon.",
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    }, 1000);
  };

  return (
    <div className="container mx-auto px-4 py-8 h-[calc(100vh-8rem)]">
      <div className="max-w-4xl mx-auto h-full flex flex-col">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {t('chatbot.title')}
          </h1>
          <p className="text-gray-600">
            Have conversations with your favorite authors and their works
          </p>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 card p-6 overflow-y-auto mb-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              <Bot className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Start a conversation! Ask me about any author or work in your library.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.sender === 'user'
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-200 text-gray-900'
                    }`}
                  >
                    <div className="flex items-center mb-1">
                      {message.sender === 'user' ? (
                        <User className="w-4 h-4 mr-2" />
                      ) : (
                        <Bot className="w-4 h-4 mr-2" />
                      )}
                      <span className="text-xs opacity-75">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <p>{message.text}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Message Input */}
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask about an author or their work..."
            className="flex-1 input"
          />
          <button
            type="submit"
            disabled={!inputText.trim()}
            className="btn-primary flex items-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
} 