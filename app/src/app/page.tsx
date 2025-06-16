"use client";

import { 
  BookOpen, 
  Users, 
  MessageSquare, 
  Heart,
  TrendingUp,
  Clock
} from 'lucide-react';

const stats = [
  { name: 'Content Uploaded', value: '12', icon: BookOpen },
  { name: 'Authors Available', value: '8', icon: Users },
  { name: 'Conversations', value: '24', icon: MessageSquare },
  { name: 'Favorites', value: '6', icon: Heart },
];

const recentActivity = [
  { title: 'One Hundred Years of Solitude', author: 'Gabriel García Márquez', time: '2 hours ago' },
  { title: 'Don Quixote', author: 'Miguel de Cervantes', time: '1 day ago' },
  { title: 'The House of Spirits', author: 'Isabel Allende', time: '3 days ago' },
];

export default function Dashboard() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back!
        </h1>
        <p className="text-gray-600">
          Here is a summary of your digital library
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon className="h-8 w-8 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Reading */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            Recent Reading
          </h2>
          <div className="space-y-4">
            {recentActivity.map((item, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <BookOpen className="w-5 h-5 text-gray-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {item.title}
                  </p>
                  <p className="text-sm text-gray-500">by {item.author}</p>
                  <p className="text-xs text-gray-400">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Reading Activity Chart Placeholder */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Reading Activity
          </h2>
          <div className="flex items-center justify-center h-48 bg-gray-50 rounded-lg">
            <p className="text-gray-500">Activity chart coming soon</p>
          </div>
        </div>
      </div>
    </div>
  );
}
