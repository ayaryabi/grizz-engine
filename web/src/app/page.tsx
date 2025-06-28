export default function HomePage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome to Grizz</h1>
        <p className="text-xl text-gray-600 mb-8">Your AI Knowledge Base</p>
        <div className="space-x-4">
          <a 
            href="/signin" 
            className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Sign In
          </a>
          <a 
            href="/signup" 
            className="inline-block bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Sign Up
          </a>
        </div>
      </div>
    </div>
  );
}
