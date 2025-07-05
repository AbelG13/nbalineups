function App() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="w-full max-w-6xl flex flex-col items-center gap-10 p-6 border border-red-500">
        <h1 className="text-4xl font-bold mb-4">NBA Lineups</h1>

        {/* Debug block to test visibility */}
        <div className="w-[400px] h-[500px] bg-green-800 relative border-4 border-white">
          <div className="absolute left-1/2 top-8 -translate-x-1/2 w-16 h-16 bg-blue-500 rounded-full"></div>
          <div className="absolute left-8 top-32 w-16 h-16 bg-yellow-500 rounded-full"></div>
          <div className="absolute right-8 top-32 w-16 h-16 bg-yellow-500 rounded-full"></div>
          <div className="absolute left-24 bottom-24 w-16 h-16 bg-red-500 rounded-full"></div>
          <div className="absolute right-24 bottom-10 w-16 h-16 bg-red-500 rounded-full"></div>
        </div>

        <div className="flex gap-6">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="w-16 h-16 bg-gray-600 rounded-full" />
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
