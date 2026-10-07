import { useCallback, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { ToastContainer, type ToastMessage, type ToastType } from "@/components/ui/Toast";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { ChatPage } from "@/pages/ChatPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { DocumentViewerPage } from "@/pages/DocumentViewerPage";
import { EvaluationPage } from "@/pages/EvaluationPage";
import { KnowledgePage } from "@/pages/KnowledgePage";
import { SearchPage } from "@/pages/SearchPage";

export function App() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = useCallback((type: ToastType, title: string, description?: string) => {
    setToasts((current) => [...current, { id: crypto.randomUUID(), type, title, description }]);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  return (
    <>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/knowledge" element={<KnowledgePage onAddToast={addToast} />} />
          <Route path="/documents/:id" element={<DocumentViewerPage />} />
          <Route path="/chat" element={<ChatPage onAddToast={addToast} />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/evaluation" element={<EvaluationPage onAddToast={addToast} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </>
  );
}
