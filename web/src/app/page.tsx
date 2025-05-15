import MainAppLayout from "@/components/layouts/MainAppLayout";
import ChatView from "@/features/chat/components/ChatView";

export default function HomePage() {
  return (
    <MainAppLayout>
      <ChatView />
    </MainAppLayout>
  );
}
