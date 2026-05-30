import ChatInterface from "./components/ChatInterface";

export default function App() {
  return (
    <div className="h-full bg-cosmos-950 flex flex-col">
      {/* Star field background */}
      <div
        className="fixed inset-0 pointer-events-none opacity-30"
        style={{
          backgroundImage: `radial-gradient(1px 1px at 20% 30%, #fff 0%, transparent 100%),
            radial-gradient(1px 1px at 80% 10%, #fff 0%, transparent 100%),
            radial-gradient(1px 1px at 50% 60%, #fff 0%, transparent 100%),
            radial-gradient(1px 1px at 10% 80%, #fff 0%, transparent 100%),
            radial-gradient(1px 1px at 90% 50%, #fff 0%, transparent 100%),
            radial-gradient(1px 1px at 35% 15%, #c9a96e 0%, transparent 100%),
            radial-gradient(1px 1px at 65% 85%, #c9a96e 0%, transparent 100%),
            radial-gradient(2px 2px at 15% 45%, #c9a96e 0%, transparent 100%)`,
        }}
      />

      {/* Nebula glow */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% 0%, rgba(124,107,155,0.08) 0%, transparent 60%), " +
            "radial-gradient(ellipse 60% 40% at 80% 100%, rgba(201,150,62,0.05) 0%, transparent 50%)",
        }}
      />

      <div className="relative flex flex-col h-full max-h-screen">
        <ChatInterface />
      </div>
    </div>
  );
}
