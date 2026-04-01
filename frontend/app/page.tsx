'use client';

import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-blue-500 to-purple-600">
      <div className="text-center text-white">
        <h1 className="text-6xl font-bold mb-4">DevOps AI Assistant</h1>
        <p className="text-2xl mb-8">Autonomous Infrastructure Management</p>

        <div className="space-x-4">
          <button
            onClick={() => router.push('/login')}
            className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100"
          >
            Get Started
          </button>

          <button
            onClick={() => router.push('/dashboard')}
            className="px-8 py-3 bg-transparent border-2 border-white text-white rounded-lg font-semibold hover:bg-white hover:text-blue-600"
          >
            Dashboard
          </button>
        </div>

        <div className="mt-16 grid grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="bg-white bg-opacity-10 p-6 rounded-lg">
            <div className="text-4xl mb-2">&#128269;</div>
            <h3 className="font-semibold mb-2">24/7 Monitoring</h3>
            <p className="text-sm">Continuous surveillance of your infrastructure</p>
          </div>

          <div className="bg-white bg-opacity-10 p-6 rounded-lg">
            <div className="text-4xl mb-2">&#129302;</div>
            <h3 className="font-semibold mb-2">Auto-Healing</h3>
            <p className="text-sm">AI agents fix issues automatically</p>
          </div>

          <div className="bg-white bg-opacity-10 p-6 rounded-lg">
            <div className="text-4xl mb-2">&#128202;</div>
            <h3 className="font-semibold mb-2">Predictive Analytics</h3>
            <p className="text-sm">Prevent problems before they occur</p>
          </div>
        </div>
      </div>
    </div>
  );
}
