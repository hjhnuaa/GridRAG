import React from "react";
import ReactDOM from "react-dom/client";
import zhCN from "antd/locale/zh_CN";
import { ConfigProvider } from "antd";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import dayjs from "dayjs";
import "dayjs/locale/zh-cn";
import "antd/dist/reset.css";

import { router } from "./router";
import "./styles/global.css";

dayjs.locale("zh-cn");

const RootMode = import.meta.env.DEV ? React.Fragment : React.StrictMode;

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false
    }
  }
});

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <RootMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: "#216f6a",
          colorInfo: "#216f6a",
          colorWarning: "#b8842f",
          colorError: "#a84735",
          borderRadius: 14,
          fontFamily: '"PingFang SC", "Microsoft YaHei", sans-serif'
        },
        components: {
          Button: {
            controlHeight: 38,
            primaryShadow: "0 10px 24px rgba(33, 111, 106, 0.18)"
          },
          Table: {
            headerBg: "rgba(33, 111, 106, 0.08)",
            rowHoverBg: "rgba(33, 111, 106, 0.06)"
          },
          Tag: {
            borderRadiusSM: 999
          }
        }
      }}
    >
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ConfigProvider>
  </RootMode>
);
