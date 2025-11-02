import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import DataQuality from "./components/DataQuality";
import SQLMigration from "./components/SQLMigration";
import Monitoring from "./components/Monitoring";
import Settings from "./components/Settings";
import NotFound from "./pages/NotFound";
import ErrorBoundary from "./components/ErrorBoundary";

const queryClient = new QueryClient();

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <div className="dark min-h-screen bg-background">
          <BrowserRouter>
            <Routes>
              {/* All routes are now public - no authentication required */}
              <Route path="/" element={<Layout />}>
                <Route index element={<Dashboard />} />
                <Route path="data-quality" element={<DataQuality />} />
                <Route path="sql-migration" element={<SQLMigration />} />
                <Route path="monitoring" element={<Monitoring />} />
                <Route path="settings" element={<Settings />} />
              </Route>
              
              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </div>
      </TooltipProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
