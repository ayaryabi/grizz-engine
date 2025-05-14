import Image from "next/image";
import MainAppLayout from "@/components/layouts/MainAppLayout";

// Example placeholder for the chat interface components
function ChatInterfacePlaceholder() {
  return (
    <div className="flex flex-col h-full overflow-hidden p-4">
      {/* Message Display Area */}
      <div className="flex-grow overflow-y-auto mb-4 border border-dashed border-border rounded-md p-4">
        <p className="text-muted-foreground">Message list will go here...</p>
        {/* Example Messages */}
        <div className="space-y-2 mt-2">
          <div className="p-2 bg-secondary rounded-md w-fit max-w-xs sm:max-w-md">
            <p className="text-sm text-secondary-foreground">Hello there!</p>
          </div>
          <div className="p-2 bg-primary rounded-md w-fit max-w-xs sm:max-w-md ml-auto">
            <p className="text-sm text-primary-foreground">Hi! How are you?</p>
          </div>
        </div>
      </div>

      {/* Message Input Area */}
      <div className="border border-dashed border-border rounded-md p-4">
        <p className="text-muted-foreground">Chat input will go here...</p>
        <input 
          type="text" 
          placeholder="Type your message..." 
          className="w-full mt-2 p-2 border rounded-md dark:bg-muted dark:border-input"
        />
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <MainAppLayout>
      <ChatInterfacePlaceholder />
    </MainAppLayout>
  );
}
