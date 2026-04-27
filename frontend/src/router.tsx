import { Suspense, lazy } from "react";
import { Skeleton } from "antd";
import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "./components/AppLayout/AppLayout";

const DashboardPage = lazy(async () => {
  const module = await import("./pages/Dashboard/DashboardPage");
  return { default: module.DashboardPage };
});
const ChatPage = lazy(async () => {
  const module = await import("./pages/Chat/ChatPage");
  return { default: module.ChatPage };
});
const EventsPage = lazy(async () => {
  const module = await import("./pages/Events/EventsPage");
  return { default: module.EventsPage };
});
const KnowledgePage = lazy(async () => {
  const module = await import("./pages/Knowledge/KnowledgePage");
  return { default: module.KnowledgePage };
});
const ResidentsPage = lazy(async () => {
  const module = await import("./pages/Residents/ResidentsPage");
  return { default: module.ResidentsPage };
});
const ResidentDetailPage = lazy(async () => {
  const module = await import("./pages/Residents/ResidentDetailPage");
  return { default: module.ResidentDetailPage };
});

const pageFallback = (
  <div className="page-shell">
    <Skeleton active paragraph={{ rows: 12 }} />
  </div>
);

function withSuspense(element: JSX.Element): JSX.Element {
  return <Suspense fallback={pageFallback}>{element}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />
      },
      {
        path: "dashboard",
        element: withSuspense(<DashboardPage />)
      },
      {
        path: "chat",
        element: withSuspense(<ChatPage />)
      },
      {
        path: "events",
        element: withSuspense(<EventsPage />)
      },
      {
        path: "knowledge",
        element: withSuspense(<KnowledgePage />)
      },
      {
        path: "residents",
        element: withSuspense(<ResidentsPage />)
      },
      {
        path: "residents/:residentId",
        element: withSuspense(<ResidentDetailPage />)
      }
    ]
  }
]);
